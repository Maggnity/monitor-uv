import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { Alert } from '../api/types'
import { SAO_PAULO } from '../test/fixtures'
import { AlertsPage } from './AlertsPage'

const ALERT: Alert = {
  id: 7,
  city: SAO_PAULO,
  threshold: 8,
  active: true,
  created_at: '2026-11-18T12:00:00Z',
  last_triggered_at: null,
}

function json(body: unknown) {
  return new Response(JSON.stringify(body), { headers: { 'Content-Type': 'application/json' } })
}

afterEach(() => vi.unstubAllGlobals())

describe('AlertsPage', () => {
  it('desligar o interruptor envia PATCH com active=false', async () => {
    const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/alerts') && (!init?.method || init.method === 'GET')) return json([ALERT])
      if (url.includes('/alerts/7') && init?.method === 'PATCH') return json({ ...ALERT, active: false })
      if (url.endsWith('/cities')) return json([SAO_PAULO])
      return json([])
    })
    vi.stubGlobal('fetch', fetchMock)
    render(
      <QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
        <MemoryRouter>
          <AlertsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    )

    const toggle = await screen.findByRole('switch', { name: /são paulo/i })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    await userEvent.click(toggle)

    const patch = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH')
    expect(patch?.[0]).toBe('/api/v1/alerts/7')
    expect(JSON.parse(String(patch?.[1]?.body))).toEqual({ active: false })
  })
})
