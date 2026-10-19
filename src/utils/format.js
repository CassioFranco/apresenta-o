export function formatCurrency(value) {
  return (Number(value) || 0).toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  })
}

export function formatQuantity(value) {
  return (Number(value) || 0).toLocaleString('pt-BR')
}

export function parseNumericValue(value) {
  if (typeof value === 'number') return value
  let normalized = String(value ?? '').trim()
  if (normalized.includes(',') && normalized.includes('.')) {
    normalized = normalized.replace(/\./g, '').replace(',', '.')
  } else {
    normalized = normalized.replace(',', '.')
  }
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? parsed : NaN
}

export function calculateTotal(quantity, unitPrice) {
  const q = Number(quantity)
  const p = Number(unitPrice)
  if (!Number.isFinite(q) || !Number.isFinite(p)) return 0
  return q * p
}

export function normalizeText(text) {
  return String(text ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}
