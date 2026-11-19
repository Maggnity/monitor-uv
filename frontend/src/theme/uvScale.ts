/**
 * Escala do índice UV da OMS — fonte única de cores para cards, gráficos, mapa e alertas.
 * O nível oficial vem da API (`level.key`); `levelFromUv` só é usado onde a API manda o
 * número cru (pontos de gráfico, histórico, mapa) e segue a mesma regra de arredondamento.
 */
export type UvLevelKey = 'low' | 'moderate' | 'high' | 'very_high' | 'extreme'

export interface UvLevelToken {
  label: string
  /** Cor de fundo da escala */
  bg: string
  /** Cor do texto sobre `bg` (contraste >= 4.5:1) */
  fg: string
  /** Faixa do índice [mín, máx]; `null` = sem limite */
  range: [number, number | null]
  recommendation: string
}

export const UV_LEVELS: Record<UvLevelKey, UvLevelToken> = {
  low: {
    label: 'Baixo',
    bg: '#2E7D32',
    fg: '#FFFFFF',
    range: [0, 2],
    recommendation: 'Sem proteção necessária',
  },
  moderate: {
    label: 'Moderado',
    bg: '#F9D71C',
    fg: '#1A1A1A',
    range: [3, 5],
    recommendation: 'Use protetor solar e óculos',
  },
  high: {
    label: 'Alto',
    bg: '#EF6C00',
    fg: '#1A1A1A',
    range: [6, 7],
    recommendation: 'Protetor, chapéu, procure sombra',
  },
  very_high: {
    label: 'Muito alto',
    bg: '#C62828',
    fg: '#FFFFFF',
    range: [8, 10],
    recommendation: 'Evite sol entre 10h e 16h',
  },
  extreme: {
    label: 'Extremo',
    bg: '#6A1B9A',
    fg: '#FFFFFF',
    range: [11, null],
    recommendation: 'Evite exposição; proteção máxima',
  },
}

export const UV_LEVEL_ORDER: UvLevelKey[] = ['low', 'moderate', 'high', 'very_high', 'extreme']

export function levelFromUv(uv: number): UvLevelKey {
  const rounded = Math.floor(uv + 0.5)
  if (rounded <= 2) return 'low'
  if (rounded <= 5) return 'moderate'
  if (rounded <= 7) return 'high'
  if (rounded <= 10) return 'very_high'
  return 'extreme'
}
