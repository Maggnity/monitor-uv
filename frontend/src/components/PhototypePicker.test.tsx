import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Phototype } from '../api/types'
import { PhototypePicker } from './PhototypePicker'

const TYPES: Phototype[] = [
  { code: 'I', description: 'Pele muito clara: sempre queima, nunca bronzeia', med_j_m2: 200, source: 's' },
  { code: 'II', description: 'Pele clara: queima com facilidade, bronzeia pouco', med_j_m2: 250, source: 's' },
]

describe('PhototypePicker', () => {
  it('escolher um tipo de pele avisa o código escolhido', async () => {
    const onChange = vi.fn()
    render(<PhototypePicker phototypes={TYPES} value={null} onChange={onChange} />)
    await userEvent.click(screen.getByRole('button', { name: /seu tipo de pele/i }))
    await userEvent.click(screen.getByRole('radio', { name: /pele clara/i }))
    expect(onChange).toHaveBeenCalledWith('II')
  })

  it('explica a ligação com a genética', async () => {
    render(<PhototypePicker phototypes={TYPES} value="I" onChange={() => {}} />)
    await userEvent.click(screen.getByRole('button', { name: /seu tipo de pele/i }))
    expect(screen.getByText(/MC1R/)).toBeInTheDocument()
  })
})
