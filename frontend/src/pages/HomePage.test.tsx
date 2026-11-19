import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { markAskedLocation, setCityId } from '../lib/storage'
import { HomePage } from './HomePage'

function renderHome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('HomePage', () => {
  it('mostra "Tentar de novo" em erro de rede e busca de novo ao clicar', async () => {
    setCityId(1)
    markAskedLocation()
    const fetchMock = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    vi.stubGlobal('fetch', fetchMock)
    renderHome()

    const retryButtons = await screen.findAllByRole('button', { name: /tentar de novo/i })
    const callsBefore = fetchMock.mock.calls.length
    await userEvent.click(retryButtons[0])
    expect(fetchMock.mock.calls.length).toBeGreaterThan(callsBefore)
  })

  it('erro do servidor aparece em linguagem simples, sem código HTTP', async () => {
    setCityId(1)
    markAskedLocation()
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('Bad Gateway', { status: 502 })))
    renderHome()
    expect(await screen.findByText(/não foi possível carregar o uv agora/i)).toBeInTheDocument()
    expect(screen.queryByText(/502/)).not.toBeInTheDocument()
  })

  it('no primeiro acesso explica por que pede a localização', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    renderHome()
    expect(
      await screen.findByText(/usamos sua localização só para mostrar o uv da cidade mais próxima/i),
    ).toBeInTheDocument()
  })
})
