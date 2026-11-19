import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { MapPoint } from '../api/types'
import { MapPage } from './MapPage'

const POINTS: MapPoint[] = [
  {
    city_id: 5,
    name: 'Fortaleza',
    lat: -3.73,
    lng: -38.52,
    uv: 12.4,
    level: { key: 'extreme', label: 'Extremo', recommendation: 'Evite exposição; proteção máxima' },
    kind: 'measured',
  },
]

afterEach(() => vi.unstubAllGlobals())

describe('MapPage', () => {
  it('abre o painel da cidade pela lista e fecha com Esc', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(POINTS))))
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter>
          <MapPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const list = await screen.findByRole('region', { name: 'Cidades' })
    await userEvent.click(within(list).getByRole('button', { name: /fortaleza/i }))

    const dialog = screen.getByRole('dialog', { name: 'Fortaleza' })
    expect(within(dialog).getByText('Evite exposição; proteção máxima')).toBeInTheDocument()
    expect(within(dialog).getByRole('link', { name: 'Ver detalhes' })).toHaveAttribute('href', '/?cidade=5')

    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
})
