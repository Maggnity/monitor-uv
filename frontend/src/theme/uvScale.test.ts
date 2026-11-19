import { describe, expect, it } from 'vitest'
import { contrastRatio } from './contrast'
import { UV_LEVELS, levelFromUv, type UvLevelKey } from './uvScale'

describe('escala UV', () => {
  it.each(Object.entries(UV_LEVELS))('nível %s mantém contraste de texto >= 4.5', (_key, level) => {
    expect(contrastRatio(level.bg, level.fg)).toBeGreaterThanOrEqual(4.5)
  })

  it.each<[number, UvLevelKey]>([
    [0, 'low'],
    [2.4, 'low'],
    [2.5, 'moderate'],
    [5.5, 'high'],
    [7.5, 'very_high'],
    [10.5, 'extreme'],
  ])('levelFromUv(%s) = %s', (uv, key) => {
    expect(levelFromUv(uv)).toBe(key)
  })

  it('contrastRatio de preto sobre branco é 21', () => {
    expect(contrastRatio('#000000', '#FFFFFF')).toBeCloseTo(21, 1)
  })
})
