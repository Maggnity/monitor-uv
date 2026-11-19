import type { City, Current } from '../api/types'

export const SAO_PAULO: City = {
  id: 1,
  name: 'São Paulo',
  state: 'SP',
  lat: -23.5505,
  lng: -46.6333,
  timezone: 'America/Sao_Paulo',
  station_code: 'SP-01',
}

export const NOW = new Date('2026-11-18T17:00:00Z') // 14h em São Paulo

export function makeCurrent(overrides: Partial<Current> = {}): Current {
  return {
    city: SAO_PAULO,
    status: 'ok',
    display_uv: 9,
    display_kind: 'measured',
    display_synthetic: false,
    measured_uv: 9,
    measured_at: '2026-11-18T16:56:00Z',
    estimated_uv: 9.3,
    level: {
      key: 'very_high',
      label: 'Muito alto',
      recommendation: 'Evite sol entre 10h e 16h',
    },
    next_peak: null,
    ...overrides,
  }
}
