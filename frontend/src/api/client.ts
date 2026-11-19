import { getClientId } from '../lib/clientId'

export const API_BASE = '/api/v1'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers: {
        'X-Client-Id': getClientId(),
        ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'Sem conexão com o servidor')
  }
  if (!response.ok) {
    let message = `Erro ${response.status}`
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
    } catch {
      /* corpo sem JSON */
    }
    throw new ApiError(response.status, message)
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

export const apiGet = <T>(path: string) => request<T>('GET', path)
export const apiSend = <T>(method: 'POST' | 'PATCH' | 'DELETE', path: string, body?: unknown) =>
  request<T>(method, path, body)
