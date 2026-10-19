import { parseNumericValue } from './format'

export function validateMaterial(form, materials, editingId = null) {
  const errors = {}

  const code = String(form.code ?? '').trim()
  const description = String(form.description ?? '').trim()

  if (!code) {
    errors.code = 'O código é obrigatório.'
  } else {
    const duplicated = materials.some(
      (item) => item.id !== editingId && item.code.toLowerCase() === code.toLowerCase(),
    )
    if (duplicated) errors.code = 'Já existe um material com este código.'
  }

  if (!description) {
    errors.description = 'A descrição é obrigatória.'
  }

  const quantity = parseNumericValue(form.quantity)
  if (!Number.isFinite(quantity) || quantity < 0) {
    errors.quantity = 'Informe uma quantidade maior ou igual a zero.'
  } else if (!Number.isInteger(quantity)) {
    errors.quantity = 'A quantidade deve ser um número inteiro.'
  }

  const unitPrice = parseNumericValue(form.unitPrice)
  if (!Number.isFinite(unitPrice) || unitPrice < 0) {
    errors.unitPrice = 'Informe um valor unitário maior ou igual a zero.'
  }

  return {
    errors,
    valid: Object.keys(errors).length === 0,
    values: { code, description, quantity, unitPrice },
  }
}
