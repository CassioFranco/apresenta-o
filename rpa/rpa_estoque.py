"""RPA de cadastro de estoque a partir de uma nota fiscal (PDF).

Le os itens de "DADOS DOS PRODUTOS / SERVICOS" de uma DANFE em PDF e cadastra
cada um no sistema web de Controle de Estoque, digitando devagar e com o mouse
visual destacado por uma bolinha vermelha.

Uso:
    python rpa_estoque.py
    python rpa_estoque.py --pdf caminho\\nota.pdf --url http://localhost:5173/
    python rpa_estoque.py --keep-open --delay 0.15

Pre-requisitos:
    pip install -r requirements.txt
    Google Chrome instalado (o ChromeDriver e baixado automaticamente pelo
    Selenium Manager).
"""

import argparse
import os
import re
import sys
import time

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

    words = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for word in page.extract_words(
                use_text_flow=False,
                keep_blank_chars=False,
                extra_attrs=["size"],
            ):
                if word.get("size", 0) <= MAX_FONT_SIZE:
                    words.append(word)

    rows = cluster_rows(words)
    items = []
    started = False
    for row in rows:
        joined = " ".join(word["text"] for word in row).strip()
        upper = joined.upper()

        if not started:
            if "COD." in upper and "DESCRICAO" in upper:
                started = True
            continue

        if ("CALCULO" in upper and "IMPOSTO" in upper) or (
            "BASE" in upper and "ICMS" in upper
        ):
            break

        match = PRODUCT_ROW_RE.match(joined)
        if not match:
            continue

        quantity = re.sub(r"[^\d]", "", match.group("qty")) or "0"
        items.append(
            {
                "code": match.group("code"),
                "description": match.group("desc").strip(),
                "quantity": quantity,
                "unit_price": match.group("price").strip(),
            }
        )

    return items


class RpaBot:
    def __init__(self, driver, type_delay=0.12, cursor=True, log=print):
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

    def move_to(self, element, pause=0.55):
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
        time.sleep(0.35)

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

    def wait_toast_gone(self, timeout=6):
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
    time.sleep(2)
    bot.inject_cursor()

    driver.execute_script(
        "try { localStorage.removeItem('%s'); } catch (e) {}" % SESSION_KEY
    )
    driver.refresh()
    time.sleep(1.5)
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
        bot.wait_toast_gone()

    return created, skipped


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    default_pdf = os.path.join(project_dir, "nota_fiscal_exemplo_painel_eletrico.pdf")

    parser = argparse.ArgumentParser(description="RPA de cadastro de estoque via PDF.")
    parser.add_argument("--pdf", default=default_pdf, help="Caminho do PDF da nota fiscal.")
    parser.add_argument("--url", default=APP_URL, help="URL do sistema web.")
    parser.add_argument("--delay", type=float, default=0.12, help="Segundos por caractere.")
    parser.add_argument("--headless", action="store_true", help="Executa sem janela visivel.")
    parser.add_argument("--no-cursor", action="store_true", help="Desativa a bolinha vermelha.")
    parser.add_argument("--keep-open", action="store_true", help="Mantem o navegador aberto no fim.")
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

    print("Itens lidos do PDF (%d):" % len(items))
    for i, item in enumerate(items, start=1):
        print(
            "  %2d) cod=%-5s qtd=%-6s unit=R$ %-10s %s"
            % (i, item["code"], item["quantity"], item["unit_price"], item["description"])
        )
    print()

    driver = create_driver(headless=args.headless)
    bot = RpaBot(driver, type_delay=args.delay, cursor=not args.no_cursor)

    try:
        login(bot, args.url)
        created, skipped = register_items(bot, items)

        print()
        print("=" * 68)
        print(" RESULTADO: %d cadastrado(s), %d pulado(s), total %d." % (created, skipped, len(items)))
        print("=" * 68)

        if args.keep_open:
            input("Pressione ENTER para fechar o navegador...")
    finally:
        driver.quit()

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrompido pelo usuario.")
        sys.exit(130)
