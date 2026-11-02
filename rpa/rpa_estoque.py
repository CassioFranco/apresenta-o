"""RPA de cadastro de estoque a partir de uma nota fiscal (PDF).

Le os itens de "DADOS DOS PRODUTOS / SERVICOS" de uma DANFE em PDF e cadastra
cada um no sistema web de Controle de Estoque, digitando com o mouse visual
destacado por uma bolinha vermelha.

Para apresentacao, o PDF e exibido em uma janela web com uma animacao que
destaca cada item sendo lido. Em seguida a janela do PDF e fechada, o sistema
e aberto e os itens sao cadastrados. No fim, o navegador permanece na tela do
sistema ate a execucao ser encerrada no terminal.

Uso:
    python rpa_estoque.py
    python rpa_estoque.py --pdf caminho\\nota.pdf --url http://localhost:5173/
    python rpa_estoque.py --delay 0.15

Pre-requisitos:
    pip install -r requirements.txt
    Google Chrome instalado (o ChromeDriver e baixado automaticamente pelo
    Selenium Manager).
"""

import argparse
import html as html_lib
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import pdfplumber
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

APP_URL = "http://localhost:5173/"
LOGIN_USER = "admin"
LOGIN_PASSWORD = "admin123"

XP_USERNAME = '//*[@id="username"]'
XP_PASSWORD = '//*[@id="password"]'
XP_LOGIN_BUTTON = '//*[@id="root"]/div/div/form/button'
XP_ADD_BUTTON = '//*[@id="root"]/div/main/div/div[1]/button'
XP_CODE = '//*[@id="material-code"]'
XP_DESCRIPTION = '//*[@id="material-description"]'
XP_QUANTITY = '//*[@id="material-quantity"]'
XP_UNIT_PRICE = '//*[@id="material-unit-price"]'
XP_SUBMIT = '//*[@id="root"]/div/main/div/div[5]/div/form/div[5]/button[2]'

SESSION_KEY = "estoque_sessao"
MATERIALS_KEY = "estoque_materiais"

MAX_FONT_SIZE = 15.0

PRODUCT_ROW_RE = re.compile(
    r"^(?P<code>\d{4})\s+(?P<desc>.+?)\s+(?P<ncm>\d{8})\s+(?P<cst>\d{3})\s+"
    r"(?P<cfop>\d{4})\s+(?P<unit>[A-Za-z]{1,4})\s+(?P<qty>[\d.,]+)\s+"
    r"(?P<price>[\d.,]+)"
)

CURSOR_JS = r"""
(function () {
  if (window.__rpaCursorReady) return;
  window.__rpaCursorReady = true;

  var dot = document.createElement('div');
  dot.id = 'rpa-cursor';
  Object.assign(dot.style, {
    position: 'fixed', left: '-100px', top: '-100px',
    width: '18px', height: '18px', marginLeft: '-9px', marginTop: '-9px',
    borderRadius: '50%', background: 'rgba(220, 38, 38, 0.92)',
    boxShadow: '0 0 0 3px rgba(220,38,38,0.25), 0 0 12px rgba(220,38,38,0.8)',
    pointerEvents: 'none', zIndex: '2147483647',
    transition: 'left .45s cubic-bezier(.22,.61,.36,1), top .45s cubic-bezier(.22,.61,.36,1), transform .12s ease'
  });
  document.documentElement.appendChild(dot);

  var ripple = document.createElement('div');
  ripple.id = 'rpa-ripple';
  Object.assign(ripple.style, {
    position: 'fixed', left: '-100px', top: '-100px',
    width: '18px', height: '18px', marginLeft: '-9px', marginTop: '-9px',
    borderRadius: '50%', border: '2px solid rgba(220,38,38,0.85)',
    opacity: '0', pointerEvents: 'none', zIndex: '2147483646'
  });
  document.documentElement.appendChild(ripple);

  var posX = 0, posY = 0;

  window.__rpaMove = function (x, y) {
    posX = x; posY = y;
    dot.style.left = x + 'px';
    dot.style.top = y + 'px';
  };

  window.__rpaClick = function () {
    ripple.style.transition = 'none';
    ripple.style.left = posX + 'px';
    ripple.style.top = posY + 'px';
    ripple.style.width = '18px';
    ripple.style.height = '18px';
    ripple.style.marginLeft = '-9px';
    ripple.style.marginTop = '-9px';
    ripple.style.opacity = '0.9';
    void ripple.offsetWidth;
    ripple.style.transition = 'all .55s ease-out';
    ripple.style.width = '56px';
    ripple.style.height = '56px';
    ripple.style.marginLeft = '-28px';
    ripple.style.marginTop = '-28px';
    ripple.style.opacity = '0';
    dot.style.transform = 'scale(.7)';
    setTimeout(function () { dot.style.transform = 'scale(1)'; }, 130);
  };
})();
"""


PDF_PREVIEW_HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<title>Nota Fiscal - Leitura RPA</title>
<style>
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0;
    padding: 24px 340px 120px 24px;
    background: radial-gradient(circle at top, #1e293b, #0f172a 60%);
    font-family: Arial, Helvetica, sans-serif;
  }
  #pdf-status {
    position: fixed; top: 14px; left: 50%; transform: translateX(-50%);
    z-index: 20; max-width: 68vw; padding: 10px 18px; border-radius: 999px;
    background: rgba(15, 23, 42, .92); color: #e2e8f0;
    font-size: 14px; font-weight: 600; letter-spacing: .1px;
    box-shadow: 0 8px 24px rgba(0,0,0,.45); border: 1px solid rgba(148,163,184,.25);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  #pdf-progress {
    position: fixed; top: 14px; right: 356px; z-index: 20;
    padding: 10px 14px; border-radius: 999px;
    background: rgba(220, 38, 38, .92); color: #fff;
    font-size: 13px; font-weight: 700; box-shadow: 0 8px 24px rgba(0,0,0,.45);
  }
  #pdf-list {
    position: fixed; top: 0; right: 0; bottom: 0; width: 310px; z-index: 15;
    padding: 24px 20px; overflow-y: auto;
    background: rgba(15, 23, 42, .96); border-left: 1px solid rgba(148,163,184,.2);
    color: #cbd5e1;
  }
  #pdf-list h2 { margin: 0 0 4px; font-size: 16px; color: #f8fafc; }
  #pdf-list p { margin: 0 0 16px; font-size: 12px; color: #94a3b8; line-height: 1.5; }
  #pdf-list ul { list-style: none; margin: 0; padding: 0; display: grid; gap: 8px; }
  #pdf-list li {
    display: grid; grid-template-columns: 16px 56px 1fr; gap: 8px; align-items: start;
    padding: 9px 10px; border-radius: 8px; font-size: 12px; line-height: 1.35;
    background: rgba(30, 41, 59, .75); border: 1px solid transparent;
    transition: background .25s, border-color .25s, transform .25s;
  }
  #pdf-list li.done { background: rgba(6, 78, 59, .65); border-color: rgba(34,197,94,.55); }
  #pdf-list .tick { color: #64748b; font-weight: 700; transition: color .25s; }
  #pdf-list li.done .tick { color: #22c55e; }
  #pdf-list .code { font-weight: 700; color: #e2e8f0; }
  #pdf-list .desc { color: #94a3b8; }
  #pdf-list li.done .desc { color: #bbf7d0; }
  #pages { position: relative; }
  .pdf-page {
    position: relative; margin: 0 auto 28px; background: #fff;
    border-radius: 4px; box-shadow: 0 18px 45px rgba(0, 0, 0, .5);
    overflow: hidden; opacity: 0; animation: pageIn .5s ease forwards;
  }
  .pdf-page:nth-child(2) { animation-delay: .12s; }
  .pdf-page:nth-child(3) { animation-delay: .24s; }
  @keyframes pageIn {
    from { opacity: 0; transform: translateY(14px) scale(.995); }
    to { opacity: 1; transform: translateY(0) scale(1); }
  }
  .word {
    position: absolute; white-space: pre; color: #111827;
    font-family: Arial, Helvetica, sans-serif; line-height: 1;
  }
  .pdf-highlight {
    position: absolute; border-radius: 3px; pointer-events: none;
    background: transparent; border: 1px solid transparent;
    transition: background .28s ease, border-color .28s ease, box-shadow .28s ease;
  }
  .pdf-highlight.reading {
    background: rgba(250, 204, 21, .38);
    border-color: rgba(250, 204, 21, 1);
    box-shadow: 0 0 0 2px rgba(250, 204, 21, .55), 0 0 18px rgba(250, 204, 21, .75);
  }
  .pdf-highlight.read {
    background: rgba(34, 197, 94, .16);
    border-color: rgba(34, 197, 94, .55);
  }
</style>
</head>
<body>
<div id="pdf-status">Abrindo nota fiscal...</div>
<div id="pdf-progress">0 / __TOTAL__</div>
<aside id="pdf-list">
  <h2>Itens da nota</h2>
  <p>O RPA está lendo os produtos do PDF.</p>
  <ul>__ITEMS__</ul>
</aside>
<main id="pages">__PAGES__</main>
<script>
const statusEl = document.getElementById('pdf-status');
const progressEl = document.getElementById('pdf-progress');
const boxes = Array.from(document.querySelectorAll('.pdf-highlight'));
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

window.__rpaPdfDone = false;
window.__rpaStartReading = async function () {
  await sleep(700);
  for (let i = 0; i < boxes.length; i += 1) {
    const box = boxes[i];
    const li = document.getElementById('pdf-li-' + i);
    box.scrollIntoView({ behavior: 'smooth', block: 'center' });
    statusEl.textContent = box.dataset.label;
    progressEl.textContent = (i + 1) + ' / ' + boxes.length;
    await sleep(700);
    box.classList.add('reading');
    if (li) li.classList.add('done');
    await sleep(620);
    box.classList.remove('reading');
    box.classList.add('read');
  }
  statusEl.textContent = 'Leitura concluída — ' + boxes.length + ' itens encontrados.';
  progressEl.textContent = boxes.length + ' / ' + boxes.length;
  await sleep(1100);
  window.__rpaPdfDone = true;
};
</script>
</body>
</html>
"""


def cluster_rows(words, tol=3.0):
    if not words:
        return []
    ordered = sorted(words, key=lambda w: (round(w["top"], 1), w["x0"]))
    rows = []
    current = [ordered[0]]
    current_top = ordered[0]["top"]
    for word in ordered[1:]:
        if abs(word["top"] - current_top) <= tol:
            current.append(word)
        else:
            rows.append(current)
            current = [word]
            current_top = word["top"]
    rows.append(current)
    for row in rows:
        row.sort(key=lambda w: w["x0"])
    return rows


def parse_pdf_items(pdf_path):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError("PDF nao encontrado: %s" % pdf_path)

    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            pages.append(
                [
                    word
                    for word in page.extract_words(
                        use_text_flow=False,
                        keep_blank_chars=False,
                        extra_attrs=["size"],
                    )
                    if word.get("size", 0) <= MAX_FONT_SIZE
                ]
            )

    items = []
    started = False
    for page_index, words in enumerate(pages):
        for row in cluster_rows(words):
            joined = " ".join(word["text"] for word in row).strip()
            upper = joined.upper()

            if not started:
                if "COD." in upper and "DESCRICAO" in upper:
                    started = True
                continue

            if ("CALCULO" in upper and "IMPOSTO" in upper) or (
                "BASE" in upper and "ICMS" in upper
            ):
                return items

            match = PRODUCT_ROW_RE.match(joined)
            if not match:
                continue

            quantity = re.sub(r"[^\d]", "", match.group("qty")) or "0"
            box = {
                "x0": min(word["x0"] for word in row),
                "top": min(word["top"] for word in row),
                "x1": max(word["x1"] for word in row),
                "bottom": max(word["bottom"] for word in row),
            }
            items.append(
                {
                    "code": match.group("code"),
                    "description": match.group("desc").strip(),
                    "quantity": quantity,
                    "unit_price": match.group("price").strip(),
                    "_page": page_index,
                    "_box": box,
                }
            )

    return items


def extract_pdf_layout(pdf_path):
    layout = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            words = page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
                extra_attrs=["size"],
            )

            watermark_words = set()
            for row in cluster_rows(words):
                joined = " ".join(word["text"] for word in row).upper()
                if "SEM VALOR FISCAL" in joined:
                    watermark_words.update(id(word) for word in row)

            layout.append(
                {
                    "width": page.width,
                    "height": page.height,
                    "words": [
                        {
                            "text": word["text"],
                            "x0": word["x0"],
                            "top": word["top"],
                            "size": word.get("size", 8.0),
                        }
                        for word in words
                        if id(word) not in watermark_words
                    ],
                }
            )
    return layout


def build_pdf_preview(pdf_path, items, output_path):
    layout = extract_pdf_layout(pdf_path)
    max_width = max((page["width"] for page in layout), default=595.0)
    scale = min(1.45, 900.0 / max_width) if max_width else 1.45

    pages_html = []
    for page_index, page in enumerate(layout):
        parts = [
            '<div class="pdf-page" style="width:%.1fpx;height:%.1fpx">'
            % (page["width"] * scale, page["height"] * scale)
        ]
        for word in page["words"]:
            parts.append(
                '<span class="word" style="left:%.1fpx;top:%.1fpx;font-size:%.1fpx">%s</span>'
                % (
                    word["x0"] * scale,
                    word["top"] * scale,
                    max(word["size"] * scale, 1.0),
                    html_lib.escape(word["text"]),
                )
            )

        for index, item in enumerate(items):
            if item.get("_page") != page_index:
                continue
            box = item["_box"]
            label = "Lendo item %d de %d: %s - %s" % (
                index + 1,
                len(items),
                item["code"],
                item["description"],
            )
            parts.append(
                '<div class="pdf-highlight" id="pdf-box-%d" data-label="%s" '
                'style="left:%.1fpx;top:%.1fpx;width:%.1fpx;height:%.1fpx"></div>'
                % (
                    index,
                    html_lib.escape(label, quote=True),
                    (box["x0"] - 3) * scale,
                    (box["top"] - 2) * scale,
                    (box["x1"] - box["x0"] + 6) * scale,
                    (box["bottom"] - box["top"] + 4) * scale,
                )
            )
        parts.append("</div>")
        pages_html.append("".join(parts))

    sidebar = []
    for index, item in enumerate(items):
        sidebar.append(
            '<li id="pdf-li-%d"><span class="tick">&#9675;</span>'
            '<span class="code">%s</span><span class="desc">%s</span></li>'
            % (index, html_lib.escape(item["code"]), html_lib.escape(item["description"]))
        )

    document = (
        PDF_PREVIEW_HTML.replace("__TOTAL__", str(len(items)))
        .replace("__ITEMS__", "".join(sidebar))
        .replace("__PAGES__", "".join(pages_html))
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(document)
    return output_path


def show_pdf_reading(driver, pdf_path, items, log=print):
    preview_path = os.path.join(tempfile.gettempdir(), "rpa_nota_fiscal_preview.html")
    build_pdf_preview(pdf_path, items, preview_path)

    opened = False
    try:
        log("[pdf] Abrindo a nota fiscal na web...")
        driver.switch_to.new_window("tab")
        opened = True
        driver.get(Path(preview_path).resolve().as_uri())

        WebDriverWait(driver, 15).until(
            lambda current: current.execute_script(
                "return typeof window.__rpaStartReading === 'function';"
            )
        )
        driver.execute_script("window.__rpaStartReading();")

        timeout = 25 + len(items) * 2
        WebDriverWait(driver, timeout).until(
            lambda current: current.execute_script("return window.__rpaPdfDone === true;")
        )

        log("[pdf] Leitura concluida: %d item(ns). Fechando a nota..." % len(items))
        time.sleep(0.6)
    except Exception as exc:
        log("[pdf] AVISO: falha ao animar a leitura (%s)." % exc)
    finally:
        if opened:
            try:
                driver.close()
            except Exception:
                pass
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(0.4)


class RpaBot:
    def __init__(self, driver, type_delay=0.03, cursor=True, log=print):
        self.driver = driver
        self.type_delay = type_delay
        self.cursor = cursor
        self.log = log
        self.wait = WebDriverWait(driver, 25)

    def inject_cursor(self):
        if not self.cursor:
            return
        self.driver.execute_script(CURSOR_JS)

    def wait_visible(self, xpath, timeout=25):
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((By.XPATH, xpath))
        )

    def wait_clickable(self, xpath, timeout=25):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )

    def _center(self, element):
        try:
            element.location_once_scrolled_into_view
        except Exception:
            pass
        return self.driver.execute_script(
            "var r = arguments[0].getBoundingClientRect();"
            "return {x: r.left + r.width / 2, y: r.top + r.height / 2};",
            element,
        )

    def move_to(self, element, pause=0.18):
        if not self.cursor:
            return
        point = self._center(element)
        self.driver.execute_script(
            "window.__rpaMove(arguments[0], arguments[1]);", point["x"], point["y"]
        )
        time.sleep(pause)

    def click(self, element):
        self.move_to(element)
        if self.cursor:
            self.driver.execute_script("window.__rpaClick();")
        try:
            element.click()
        except WebDriverException:
            self.driver.execute_script("arguments[0].click();", element)
        time.sleep(0.12)

    def slow_type(self, element, text):
        self.move_to(element)
        try:
            element.click()
        except WebDriverException:
            pass
        element.clear()
        for char in str(text):
            element.send_keys(char)
            time.sleep(self.type_delay)

    def wait_toast_gone(self, timeout=1.2):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, '[role="status"]'))
            )
        except Exception:
            pass


def create_driver(headless=False):
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if headless:
        options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def read_existing_codes(driver):
    codes = driver.execute_script(
        "try { return JSON.parse(localStorage.getItem('%s')) || []; }"
        "catch (e) { return []; }" % MATERIALS_KEY
    )
    existing = set()
    for material in codes or []:
        code = str(material.get("code", "")).strip().lower()
        if code:
            existing.add(code)
    return existing


def login(bot, url):
    driver = bot.driver
    bot.log("[login] Abrindo %s" % url)
    driver.get(url)
    time.sleep(1)
    bot.inject_cursor()

    driver.execute_script(
        "try { localStorage.removeItem('%s'); } catch (e) {}" % SESSION_KEY
    )
    driver.refresh()
    time.sleep(0.8)
    bot.inject_cursor()

    username = bot.wait_visible(XP_USERNAME)
    bot.slow_type(username, LOGIN_USER)
    password = bot.wait_visible(XP_PASSWORD)
    bot.slow_type(password, LOGIN_PASSWORD)
    button = bot.wait_clickable(XP_LOGIN_BUTTON)
    bot.click(button)

    bot.wait_clickable(XP_ADD_BUTTON)
    bot.inject_cursor()
    bot.log("[login] Autenticado como '%s'." % LOGIN_USER)


def register_items(bot, items):
    driver = bot.driver
    existing = read_existing_codes(driver)
    total = len(items)
    created = 0
    skipped = 0

    for index, item in enumerate(items, start=1):
        code = item["code"].strip()
        prefix = "[%d/%d]" % (index, total)

        if code.lower() in existing:
            skipped += 1
            bot.log("%s PULADO   codigo %s ja existe no estoque." % (prefix, code))
            continue

        bot.log(
            "%s CADASTRANDO  cod=%s | qtd=%s | unit=R$ %s | %s"
            % (prefix, code, item["quantity"], item["unit_price"], item["description"])
        )

        add_button = bot.wait_clickable(XP_ADD_BUTTON)
        bot.click(add_button)

        code_el = bot.wait_visible(XP_CODE)
        bot.slow_type(code_el, code)

        desc_el = bot.wait_visible(XP_DESCRIPTION)
        bot.slow_type(desc_el, item["description"])

        qty_el = bot.wait_visible(XP_QUANTITY)
        bot.slow_type(qty_el, item["quantity"])

        price_el = bot.wait_visible(XP_UNIT_PRICE)
        bot.slow_type(price_el, item["unit_price"])

        submit = bot.wait_clickable(XP_SUBMIT)
        bot.click(submit)

        try:
            WebDriverWait(driver, 10).until(
                EC.invisibility_of_element_located((By.XPATH, XP_CODE))
            )
        except Exception:
            bot.log("%s AVISO: o formulario nao fechou; verificando erros..." % prefix)
            error = driver.find_elements(By.CSS_SELECTOR, ".text-red-600")
            for node in error:
                if node.text.strip():
                    bot.log("        validação: %s" % node.text.strip())

        existing.add(code.lower())
        created += 1
        bot.log("%s OK        codigo %s cadastrado." % (prefix, code))

    return created, skipped


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    default_pdf = os.path.join(project_dir, "nota_fiscal_exemplo_painel_eletrico.pdf")

    parser = argparse.ArgumentParser(description="RPA de cadastro de estoque via PDF.")
    parser.add_argument("--pdf", default=default_pdf, help="Caminho do PDF da nota fiscal.")
    parser.add_argument("--url", default=APP_URL, help="URL do sistema web.")
    parser.add_argument("--delay", type=float, default=0.03, help="Segundos por caractere.")
    parser.add_argument("--headless", action="store_true", help="Executa sem janela visivel.")
    parser.add_argument("--no-cursor", action="store_true", help="Desativa a bolinha vermelha.")
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Compatibilidade: o navegador ja permanece aberto no fim.",
    )
    args = parser.parse_args()

    print("=" * 68)
    print(" RPA - Controle de Estoque")
    print("=" * 68)
    print("PDF : %s" % args.pdf)
    print("URL : %s" % args.url)
    print()

    items = parse_pdf_items(args.pdf)
    if not items:
        print("Nenhum item encontrado no PDF. Verifique o caminho/formatos do arquivo.")
        return 1

    driver = create_driver(headless=args.headless)
    bot = RpaBot(driver, type_delay=args.delay, cursor=not args.no_cursor)
    success = False

    try:
        show_pdf_reading(driver, args.pdf, items)

        print("Itens lidos do PDF (%d):" % len(items))
        for i, item in enumerate(items, start=1):
            print(
                "  %2d) cod=%-5s qtd=%-6s unit=R$ %-10s %s"
                % (
                    i,
                    item["code"],
                    item["quantity"],
                    item["unit_price"],
                    item["description"],
                )
            )
        print()

        login(bot, args.url)
        created, skipped = register_items(bot, items)
        success = True

        print()
        print("=" * 68)
        print(" RESULTADO: %d cadastrado(s), %d pulado(s), total %d." % (created, skipped, len(items)))
        print("=" * 68)
        print()
        print("O sistema permanece aberto na tela.")
        print("Para encerrar a apresentacao, feche esta execucao no terminal (Ctrl+C).")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExecucao encerrada pelo usuario. Navegador mantido aberto.")
    finally:
        if not success:
            driver.quit()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
        sys.exit(130)
