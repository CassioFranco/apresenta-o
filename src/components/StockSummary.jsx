import { calculateTotal, formatCurrency, formatQuantity } from '../utils/format'

export default function StockSummary({ materials }) {
  const totalItems = materials.length
  const totalQuantity = materials.reduce((sum, item) => sum + item.quantity, 0)
  const totalValue = materials.reduce((sum, item) => sum + calculateTotal(item.quantity, item.unitPrice), 0)

  const cards = [
    {
      label: 'Total de materiais',
      value: formatQuantity(totalItems),
      color: 'bg-blue-50 text-blue-700 ring-blue-200',
    },
    {
      label: 'Quantidade total em estoque',
      value: formatQuantity(totalQuantity),
      color: 'bg-amber-50 text-amber-700 ring-amber-200',
    },
    {
      label: 'Valor total do estoque',
      value: formatCurrency(totalValue),
      color: 'bg-emerald-50 text-emerald-700 ring-emerald-200',
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {cards.map((card) => (
        <div
          key={card.label}
          className={`rounded-xl p-4 ring-1 ${card.color} shadow-sm`}
        >
          <p className="text-sm font-medium opacity-80">{card.label}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">{card.value}</p>
        </div>
      ))}
    </div>
  )
}
