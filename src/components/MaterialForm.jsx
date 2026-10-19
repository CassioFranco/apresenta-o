import { useEffect, useState } from 'react'
import { calculateTotal, formatCurrency, parseNumericValue } from '../utils/format'
import { validateMaterial } from '../utils/validate'

const emptyForm = { code: '', description: '', quantity: '', unitPrice: '' }

const inputClasses = (hasError) =>
  `w-full rounded-lg border bg-white px-3 py-2 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 ${
    hasError
      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
      : 'border-slate-300 focus:border-blue-500 focus:ring-blue-500'
  }`

export default function MaterialForm({ open, material, materials, onSave, onClose }) {
  if (!open) return null

  return (
    <MaterialFormContent
      key={material?.id ?? 'novo'}
      material={material}
      materials={materials}
      onSave={onSave}
      onClose={onClose}
    />
  )
}

function MaterialFormContent({ material, materials, onSave, onClose }) {
  const [form, setForm] = useState(() =>
    material
      ? {
          code: material.code,
          description: material.description,
          quantity: String(material.quantity),
          unitPrice: String(material.unitPrice).replace('.', ','),
        }
      : emptyForm,
  )
  const [errors, setErrors] = useState({})

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [onClose])

  const isEditing = Boolean(material)
  const quantity = parseNumericValue(form.quantity)
  const unitPrice = parseNumericValue(form.unitPrice)
  const totalValue =
    Number.isFinite(quantity) && Number.isFinite(unitPrice)
      ? calculateTotal(quantity, unitPrice)
      : 0

  const handleChange = (field) => (event) => {
    setForm((previous) => ({ ...previous, [field]: event.target.value }))
    setErrors((previous) => ({ ...previous, [field]: undefined }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    const result = validateMaterial(form, materials, material?.id)
    if (!result.valid) {
      setErrors(result.errors)
      return
    }
    onSave(result.values)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose()
      }}
    >
      <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-xl">
        <div className="mb-5 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">
              {isEditing ? 'Editar material' : 'Novo material'}
            </h2>
            <p className="text-sm text-slate-500">
              Preencha os campos e salve para confirmar.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar formulário"
            className="rounded-lg p-1.5 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label htmlFor="material-code" className="mb-1 block text-sm font-medium text-slate-700">
              Código <span className="text-red-500">*</span>
            </label>
            <input
              id="material-code"
              type="text"
              value={form.code}
              onChange={handleChange('code')}
              placeholder="Ex.: MAT005"
              className={inputClasses(errors.code)}
            />
            {errors.code && <p className="mt-1 text-xs text-red-600">{errors.code}</p>}
          </div>

          <div>
            <label
              htmlFor="material-description"
              className="mb-1 block text-sm font-medium text-slate-700"
            >
              Descrição <span className="text-red-500">*</span>
            </label>
            <input
              id="material-description"
              type="text"
              value={form.description}
              onChange={handleChange('description')}
              placeholder="Ex.: Cimento Portland"
              className={inputClasses(errors.description)}
            />
            {errors.description && (
              <p className="mt-1 text-xs text-red-600">{errors.description}</p>
            )}
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="material-quantity"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                Quantidade <span className="text-red-500">*</span>
              </label>
              <input
                id="material-quantity"
                type="text"
                inputMode="numeric"
                value={form.quantity}
                onChange={handleChange('quantity')}
                placeholder="Ex.: 100"
                className={inputClasses(errors.quantity)}
              />
              {errors.quantity && (
                <p className="mt-1 text-xs text-red-600">{errors.quantity}</p>
              )}
            </div>

            <div>
              <label
                htmlFor="material-unit-price"
                className="mb-1 block text-sm font-medium text-slate-700"
              >
                Valor unitário (R$) <span className="text-red-500">*</span>
              </label>
              <input
                id="material-unit-price"
                type="text"
                inputMode="decimal"
                value={form.unitPrice}
                onChange={handleChange('unitPrice')}
                placeholder="Ex.: 45,00"
                className={inputClasses(errors.unitPrice)}
              />
              {errors.unitPrice && (
                <p className="mt-1 text-xs text-red-600">{errors.unitPrice}</p>
              )}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 px-3 py-2.5 ring-1 ring-slate-200">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Valor total (calculado)
            </p>
            <p className="mt-0.5 text-lg font-semibold tabular-nums text-slate-900">
              {formatCurrency(totalValue)}
            </p>
          </div>

          <div className="flex flex-col-reverse gap-2 pt-2 sm:flex-row sm:justify-end">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            >
              {isEditing ? 'Salvar alterações' : 'Cadastrar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
