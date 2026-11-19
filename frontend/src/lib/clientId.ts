const KEY = 'monitor-uv:client-id'

/** UUID v4. `crypto.randomUUID` só existe em contexto seguro (HTTPS ou localhost);
 * aberto por HTTP na rede local (ex.: no celular), usamos `getRandomValues`. */
function uuid(): string {
  if (typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  const bytes = crypto.getRandomValues(new Uint8Array(16))
  bytes[6] = (bytes[6] & 0x0f) | 0x40
  bytes[8] = (bytes[8] & 0x3f) | 0x80
  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('')
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`
}

/** Identificador anônimo deste navegador, usado para separar os alertas de cada pessoa. */
export function getClientId(): string {
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = uuid()
    localStorage.setItem(KEY, id)
  }
  return id
}
