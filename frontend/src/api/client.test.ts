import { afterEach, describe, expect, it, vi } from 'vitest'
import { getClientId } from '../lib/clientId'
import { apiGet } from './client'

afterEach(() => vi.unstubAllGlobals())

function ok() {
  return new Response('[]', { headers: { 'Content-Type': 'application/json' } })
}

describe('cliente da API', () => {
  it('gera o id do navegador mesmo sem crypto.randomUUID (HTTP fora de localhost)', () => {
    vi.stubGlobal('crypto', { getRandomValues: (a: Uint8Array) => a.fill(7) })
    expect(getClientId()).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
  })

  it('só envia X-Client-Id nas rotas de alertas', async () => {
    const fetchMock = vi.fn().mockImplementation(async () => ok())
    vi.stubGlobal('fetch', fetchMock)
    await apiGet('/cities')
    await apiGet('/alerts')
    const headers = fetchMock.mock.calls.map(([, init]) => init.headers as Record<string, string>)
    expect(headers[0]['X-Client-Id']).toBeUndefined()
    expect(headers[1]['X-Client-Id']).toBeDefined()
  })
})
