const MATERIALS_KEY = 'estoque_materiais'
const SESSION_KEY = 'estoque_sessao'

export const DEFAULT_MATERIALS = [
  { id: 1, code: 'MAT001', description: 'Parafuso sextavado', quantity: 100, unitPrice: 0.5 },
  { id: 2, code: 'MAT002', description: 'Porca sextavada', quantity: 80, unitPrice: 0.3 },
  { id: 3, code: 'MAT003', description: 'Chapa de aço', quantity: 20, unitPrice: 45 },
  { id: 4, code: 'MAT004', description: 'Rolamento industrial', quantity: 15, unitPrice: 32.9 },
]

export function loadMaterials() {
  try {
    const stored = localStorage.getItem(MATERIALS_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) return parsed
    }
  } catch {
    // dados corrompidos: recarrega os exemplos
  }
  localStorage.setItem(MATERIALS_KEY, JSON.stringify(DEFAULT_MATERIALS))
  return DEFAULT_MATERIALS
}

export function saveMaterials(materials) {
  localStorage.setItem(MATERIALS_KEY, JSON.stringify(materials))
}

export function loadSession() {
  try {
    const stored = localStorage.getItem(SESSION_KEY)
    return stored ? JSON.parse(stored) : null
  } catch {
    return null
  }
}

export function saveSession(username) {
  localStorage.setItem(SESSION_KEY, JSON.stringify({ username }))
}

export function clearSession() {
  localStorage.removeItem(SESSION_KEY)
}

export function nextMaterialId(materials) {
  return materials.reduce((max, item) => Math.max(max, Number(item.id) || 0), 0) + 1
}
