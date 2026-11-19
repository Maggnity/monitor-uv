import { describe, expect, it } from 'vitest'
import { hourLabel, peakLabel, relativeTime } from './format'

const NOW = new Date('2026-11-18T17:00:00Z')

describe('format', () => {
  it('relativeTime', () => {
    expect(relativeTime('2026-11-18T16:59:40Z', NOW)).toBe('agora mesmo')
    expect(relativeTime('2026-11-18T16:56:00Z', NOW)).toBe('há 4 min')
    expect(relativeTime('2026-11-18T14:50:00Z', NOW)).toBe('há 2 h')
  })

  it('hourLabel usa o fuso da cidade', () => {
    expect(hourLabel('2026-11-18T14:00:00Z', 'America/Sao_Paulo')).toBe('11h')
    expect(hourLabel('2026-11-18T15:30:00Z', 'America/Sao_Paulo')).toBe('12h30')
  })

  it('peakLabel mostra o valor e o meio da janela de pico', () => {
    expect(peakLabel(11, '2026-11-18T14:00:00Z', '2026-11-18T17:00:00Z', 'America/Sao_Paulo')).toBe(
      'Pico: 11 às 12h30',
    )
  })
})
