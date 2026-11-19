import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { CompareRow } from '../api/types'
import { SAO_PAULO } from '../test/fixtures'
import { CityCompareTable } from './CityCompareTable'

function row(id: number, name: string, peak: number): CompareRow {
  return {
    city: { ...SAO_PAULO, id, name },
    current_uv: peak - 1,
    current_kind: 'measured',
    current_synthetic: false,
    peak_today: peak,
    hours_above_8: 2,
    trend: 'stable',
    sparkline: [peak, peak],
  }
}

const ROWS = [row(1, 'São Paulo', 8), row(2, 'Fortaleza', 13), row(3, 'Rio de Janeiro', 10)]

function cityOrder() {
  return screen
    .getAllByRole('row')
    .slice(1)
    .map((r) => within(r).getByRole('rowheader').textContent)
}

describe('CityCompareTable', () => {
  it('ordena pelo pico em ordem decrescente ao clicar duas vezes no cabeçalho', async () => {
    render(<CityCompareTable rows={ROWS} />)
    const peakButton = screen.getByRole('button', { name: /pico previsto/i })
    await userEvent.click(peakButton)
    await userEvent.click(peakButton)
    expect(cityOrder()).toEqual(['Fortaleza', 'Rio de Janeiro', 'São Paulo'])
    expect(peakButton.closest('th')).toHaveAttribute('aria-sort', 'descending')
  })

  it('mostra a tendência em texto, não só com seta', () => {
    render(<CityCompareTable rows={[{ ...ROWS[0], trend: 'up' }]} />)
    expect(screen.getByText('subindo')).toBeInTheDocument()
  })
})
