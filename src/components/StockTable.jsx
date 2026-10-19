import { calculateTotal, formatCurrency, formatQuantity } from '../utils/format'

export default function StockTable({ materials, hasSearch, searchTerm, onEdit, onDelete }) {
  if (materials.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">
        <p className="font-medium text-slate-600">
          {hasSearch
            ? `Nenhum material encontrado para "${searchTerm}".`
            : 'Nenhum material cadastrado.'}
        </p>
        <p className="mt-1 text-sm text-slate-500">
          {hasSearch
            ? 'Tente pesquisar por outro código ou descrição.'
            : 'Clique em "Adicionar material" para cadastrar o primeiro item.'}
        </p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
          <tr>
            <th className="px-4 py-3 font-semibold">Código</th>
            <th className="px-4 py-3 font-semibold">Descrição</th>
            <th className="px-4 py-3 text-right font-semibold">Quantidade</th>
            <th className="px-4 py-3 text-right font-semibold">Valor unitário</th>
            <th className="px-4 py-3 text-right font-semibold">Valor total</th>
            <th className="px-4 py-3 text-center font-semibold">Ações</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {materials.map((material) => (
            <tr key={material.id} className="hover:bg-slate-50">
              <td className="px-4 py-3 font-mono text-xs font-semibold text-slate-700">
                {material.code}
              </td>
              <td className="px-4 py-3 text-slate-800">{material.description}</td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-800">
                {formatQuantity(material.quantity)}
              </td>
              <td className="px-4 py-3 text-right tabular-nums text-slate-800">
                {formatCurrency(material.unitPrice)}
              </td>
              <td className="px-4 py-3 text-right font-semibold tabular-nums text-slate-900">
                {formatCurrency(calculateTotal(material.quantity, material.unitPrice))}
              </td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-center gap-2">
                  <button
                    type="button"
                    onClick={() => onEdit(material)}
                    className="rounded-lg px-3 py-1.5 text-xs font-medium text-blue-700 ring-1 ring-blue-200 transition hover:bg-blue-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
                  >
                    Editar
                  </button>
                  <button
                    type="button"
                    onClick={() => onDelete(material)}
                    className="rounded-lg px-3 py-1.5 text-xs font-medium text-red-700 ring-1 ring-red-200 transition hover:bg-red-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
                  >
                    Excluir
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
