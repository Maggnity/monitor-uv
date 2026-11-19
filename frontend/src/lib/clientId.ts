const KEY = 'monitor-uv:client-id'

/** Identificador anônimo deste navegador, usado para separar os alertas de cada pessoa. */
export function getClientId(): string {
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(KEY, id)
  }
  return id
}
