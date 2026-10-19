export default function Toast({ toast, onClose }) {
  if (!toast) return null

  const isSuccess = toast.type === 'success'

  return (
    <div className="pointer-events-none fixed top-4 right-4 z-[60] w-full max-w-sm">
      <div
        className={`pointer-events-auto flex items-start gap-3 rounded-xl p-4 shadow-lg ring-1 ${
          isSuccess
            ? 'bg-emerald-50 text-emerald-900 ring-emerald-200'
            : 'bg-red-50 text-red-900 ring-red-200'
        }`}
        role="status"
      >
        <div className="flex-1 text-sm font-medium">{toast.message}</div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Fechar mensagem"
          className={`rounded-md p-0.5 transition hover:opacity-70 ${
            isSuccess ? 'text-emerald-700' : 'text-red-700'
          }`}
        >
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M6.28 5.22a.75.75 0 0 0-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 1 0 1.06 1.06L10 11.06l3.72 3.72a.75.75 0 1 0 1.06-1.06L11.06 10l3.72-3.72a.75.75 0 0 0-1.06-1.06L10 8.94 6.28 5.22Z" />
          </svg>
        </button>
      </div>
    </div>
  )
}
