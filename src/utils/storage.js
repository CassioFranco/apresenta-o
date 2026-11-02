const MATERIALS_KEY = 'estoque_materiais'
const SESSION_KEY = 'estoque_sessao'

export const DEFAULT_MATERIALS = []

export function loadMaterials() {
  try {
    const stored = localStorage.getItem(MATERIALS_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) return parsed
    }
  } catch {
    // dados corrompidos: recomeca com estoque vazio
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
