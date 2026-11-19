import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { NOW, makeCurrent } from '../test/fixtures'
import { UvCard } from './UvCard'

describe('UvCard', () => {
  it('ok mostra número grande, nível e recomendação', () => {
    render(<UvCard current={makeCurrent()} now={NOW} />)
    expect(screen.getByTestId('uv-value')).toHaveTextContent('9')
    expect(screen.getByText('Muito alto')).toBeInTheDocument()
    expect(screen.getByText('Evite sol entre 10h e 16h')).toBeInTheDocument()
    expect(screen.getByText(/atualizado há 4 min/)).toBeInTheDocument()
  })

  it('valor estimado é rotulado como estimado', () => {
    render(
      <UvCard
        current={makeCurrent({ display_kind: 'estimated', display_uv: 9.3 })}
        now={NOW}
      />,
    )
    expect(screen.getByText(/estimado agora/i)).toBeInTheDocument()
    expect(screen.getByText(/última medição há 4 min/)).toBeInTheDocument()
  })

  it('noite mostra o pico de amanhã', () => {
    render(
      <UvCard
        current={makeCurrent({
          status: 'night',
          display_uv: 0,
          display_kind: 'estimated',
          level: { key: 'low', label: 'Baixo', recommendation: 'Sem proteção necessária' },
          next_peak: {
            date: '2026-11-19',
            uv_max: 11.4,
            start: '2026-11-19T14:00:00Z',
            end: '2026-11-19T17:00:00Z',
          },
        })}
        now={new Date('2026-11-19T01:00:00Z')}
      />,
    )
    expect(screen.getByText(/o sol já se pôs/i)).toBeInTheDocument()
    expect(screen.getByText(/amanhã o pico deve chegar a 11, das 11h às 14h/i)).toBeInTheDocument()
  })

  it('estação desatualizada mostra o selo Desatualizado', () => {
    render(
      <UvCard
        current={makeCurrent({ status: 'stale', measured_at: '2026-11-18T12:00:00Z' })}
        now={NOW}
      />,
    )
    expect(screen.getByText('Desatualizado')).toBeInTheDocument()
    expect(screen.getByText(/última medição há 5 h/)).toBeInTheDocument()
  })

  it('sem dados explica a ausência de leituras', () => {
    render(
      <UvCard
        current={makeCurrent({
          status: 'no_data',
          display_uv: null,
          display_kind: null,
          measured_uv: null,
          measured_at: null,
          estimated_uv: null,
          level: null,
        })}
        now={NOW}
      />,
    )
    expect(screen.getByText(/ainda não temos leituras/i)).toBeInTheDocument()
  })

  it('com fototipo escolhido mostra o tempo estimado até queimar', () => {
    render(<UvCard current={makeCurrent({ minutes_to_burn: 17 })} now={NOW} />)
    expect(screen.getByText(/você pode se queimar em cerca de 17 min agora/i)).toBeInTheDocument()
  })
})
