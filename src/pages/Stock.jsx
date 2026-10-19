import { useEffect, useMemo, useRef, useState } from 'react'
import ConfirmDialog from '../components/ConfirmDialog'
import MaterialForm from '../components/MaterialForm'
import StockSummary from '../components/StockSummary'
import StockTable from '../components/StockTable'
import Toast from '../components/Toast'
import { normalizeText } from '../utils/format'
import { loadMaterials, nextMaterialId, saveMaterials } from '../utils/storage'

export default function Stock() {
  const [materials, setMaterials] = useState(() => loadMaterials())
  const [searchTerm, setSearchTerm] = useState('')
  const [formOpen, setFormOpen] = useState(false)
  const [editingMaterial, setEditingMaterial] = useState(null)
  const [materialToDelete, setMaterialToDelete] = useState(null)
  const [toast, setToast] = useState(null)
  const toastTimer = useRef(null)

  useEffect(() => {
    saveMaterials(materials)
  }, [materials])

  useEffect(() => () => clearTimeout(toastTimer.current), [])

  const showToast = (message, type = 'success') => {
    clearTimeout(toastTimer.current)
    setToast({ message, type })
    toastTimer.current = setTimeout(() => setToast(null), 3500)
  }

  const hasSearch = searchTerm.trim() !== ''
  const filteredMaterials = useMemo(() => {
    if (!hasSearch) return materials
    const term = normalizeText(searchTerm.trim())
    return materials.filter(
      (item) =>
        normalizeText(item.code).includes(term) ||
        normalizeText(item.description).includes(term),
    )
  }, [materials, searchTerm, hasSearch])

  const handleOpenCreate = () => {
    setEditingMaterial(null)
    setFormOpen(true)
  }

  const handleOpenEdit = (material) => {
    setEditingMaterial(material)
    setFormOpen(true)
  }

  const handleSave = (values) => {
    if (editingMaterial) {
      setMaterials((previous) =>
        previous.map((item) => (item.id === editingMaterial.id ? { ...item, ...values } : item)),
      )
      showToast(`Material "${values.code}" atualizado com sucesso.`)
    } else {
      setMaterials((previous) => [
        ...previous,
        { id: nextMaterialId(previous), ...values },
      ])
      showToast(`Material "${values.code}" cadastrado com sucesso.`)
    }
    setFormOpen(false)
    setEditingMaterial(null)
  }

  const handleConfirmDelete = () => {
    const target = materialToDelete
    setMaterials((previous) => previous.filter((item) => item.id !== target.id))
    setMaterialToDelete(null)
    showToast(`Material "${target.code}" excluído com sucesso.`)
  }

  return (
    <div className="mx-auto w-full max-w-5xl px-4 py-8 sm:px-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
            Controle de Estoque
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Cadastre, pesquise, edite e exclua materiais do estoque.
          </p>
        </div>
        <button
          type="button"
          onClick={handleOpenCreate}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
        >
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M10.75 4.75a.75.75 0 0 0-1.5 0v4.5h-4.5a.75.75 0 0 0 0 1.5h4.5v4.5a.75.75 0 0 0 1.5 0v-4.5h4.5a.75.75 0 0 0 0-1.5h-4.5v-4.5Z" />
          </svg>
          Adicionar material
        </button>
      </div>

      <StockSummary materials={materials} />

      <div className="mt-6">
        <label htmlFor="stock-search" className="sr-only">
          Pesquisar materiais
        </label>
        <div className="relative">
          <svg
            className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M9 3.5a5.5 5.5 0 1 0 3.4 9.84l2.6 2.6a.75.75 0 1 0 1.06-1.06l-2.6-2.6A5.5 5.5 0 0 0 9 3.5ZM6.5 9a2.5 2.5 0 1 1 5 0 2.5 2.5 0 0 1-5 0Z"
              clipRule="evenodd"
            />
          </svg>
          <input
            id="stock-search"
            type="search"
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            placeholder="Pesquisar por código ou descrição..."
            className="w-full rounded-xl border border-slate-300 bg-white py-2.5 pr-4 pl-9 text-sm text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="mt-4">
        <StockTable
          materials={filteredMaterials}
          hasSearch={hasSearch}
          searchTerm={searchTerm.trim()}
          onEdit={handleOpenEdit}
          onDelete={setMaterialToDelete}
        />
      </div>

      <MaterialForm
        open={formOpen}
        material={editingMaterial}
        materials={materials}
        onSave={handleSave}
        onClose={() => {
          setFormOpen(false)
          setEditingMaterial(null)
        }}
      />

      <ConfirmDialog
        open={Boolean(materialToDelete)}
        title="Excluir material"
        message={
          materialToDelete
            ? `Deseja realmente excluir o material "${materialToDelete.code}" (${materialToDelete.description})? Esta ação não pode ser desfeita.`
            : ''
        }
        onConfirm={handleConfirmDelete}
        onCancel={() => setMaterialToDelete(null)}
      />

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  )
}
