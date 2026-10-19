import { useState } from 'react'
import Login from './pages/Login'
import Stock from './pages/Stock'
import { clearSession, loadSession, saveSession } from './utils/storage'

export default function App() {
  const [user, setUser] = useState(() => loadSession())

  const handleLogin = (username) => {
    saveSession(username)
    setUser({ username })
  }

  const handleLogout = () => {
    clearSession()
    setUser(null)
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <div className="min-h-svh bg-slate-100">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-5xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white">
              <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" />
                <path d="m3.3 7 8.7 5 8.7-5" />
                <path d="M12 22V12" />
              </svg>
            </div>
            <span className="text-base font-semibold tracking-tight text-slate-900">
              Sistema de Controle de Estoque
            </span>
          </div>
          <div className="flex items-center justify-between gap-4 sm:justify-end">
            <span className="text-sm text-slate-600">
              Usuário: <span className="font-medium text-slate-900">{user.username}</span>
            </span>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-500"
            >
              Sair
            </button>
          </div>
        </div>
      </header>

      <main>
        <Stock />
      </main>
    </div>
  )
}
