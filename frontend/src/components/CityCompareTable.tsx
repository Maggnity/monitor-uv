import { ArrowDown, ArrowRight, ArrowUp, ChevronsUpDown } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { CompareRow, Trend } from '../api/types'
import { Sparkline } from './Sparkline'
import { UvBadge } from './UvBadge'

type SortKey = 'name' | 'current' | 'peak' | 'hours' | 'vulnerability'
type Direction = 'ascending' | 'descending'

const TREND: Record<Trend, { label: string; icon: typeof ArrowUp }> = {
  up: { label: 'subindo', icon: ArrowUp },
  down: { label: 'caindo', icon: ArrowDown },
  stable: { label: 'estável', icon: ArrowRight },
}

function value(row: CompareRow, key: SortKey): number | string | null {
  switch (key) {
    case 'name':
      return row.city.name
    case 'current':
      return row.current_uv
    case 'peak':
      return row.peak_today
    case 'hours':
      return row.hours_above_8
    case 'vulnerability':
      return row.vulnerability ?? null
  }
}

export function CityCompareTable({ rows }: { rows: CompareRow[] }) {
  const [sort, setSort] = useState<{ key: SortKey; direction: Direction } | null>(null)
  const showVulnerability = rows.some((r) => r.vulnerability !== undefined && r.vulnerability !== null)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const factor = sort.direction === 'ascending' ? 1 : -1
    return [...rows].sort((a, b) => {
      const va = value(a, sort.key)
      const vb = value(b, sort.key)
      if (va === null) return 1
      if (vb === null) return -1
      if (typeof va === 'string') return va.localeCompare(String(vb), 'pt-BR') * factor
      return (va - (vb as number)) * factor
    })
  }, [rows, sort])

  const toggle = (key: SortKey) =>
    setSort((s) =>
      s?.key === key
        ? { key, direction: s.direction === 'ascending' ? 'descending' : 'ascending' }
        : { key, direction: 'ascending' },
    )

  const header = (key: SortKey, label: string, align = 'text-left') => {
    const active = sort?.key === key
    const Icon = !active ? ChevronsUpDown : sort.direction === 'ascending' ? ArrowUp : ArrowDown
    return (
      <th scope="col" aria-sort={active ? sort.direction : 'none'} className={`px-3 py-2 ${align}`}>
        <button
          type="button"
          onClick={() => toggle(key)}
          className="inline-flex min-h-11 items-center gap-1 font-semibold focus-visible:outline-3 focus-visible:outline-blue-600"
        >
          {label}
          <Icon aria-hidden="true" size={14} className={active ? '' : 'text-neutral-400'} />
        </button>
      </th>
    )
  }

  return (
    <div className="overflow-x-auto rounded-3xl bg-white shadow-sm">
      <table className="w-full min-w-[640px] text-sm">
        <caption className="sr-only">Comparação do UV entre cidades hoje</caption>
        <thead className="border-b border-neutral-200 text-neutral-700">
          <tr>
            {header('name', 'Cidade')}
            {header('current', 'UV atual')}
            {header('peak', 'Pico previsto')}
            {header('hours', 'Horas acima de 8')}
            <th scope="col" className="px-3 py-2 text-left font-semibold">
              Tendência
            </th>
            {showVulnerability && header('vulnerability', 'Vulnerabilidade (ilustrativa)')}
          </tr>
        </thead>
        <tbody className="divide-y divide-neutral-100">
          {sorted.map((row) => {
            const trend = TREND[row.trend]
            return (
              <tr key={row.city.id}>
                <th scope="row" className="px-3 py-3 text-left font-semibold">
                  {row.city.name}
                </th>
                <td className="px-3 py-3">
                  <span className="flex items-center gap-2">
                    <UvBadge uv={row.current_uv} size="sm" />
                    {(row.current_synthetic || row.current_kind === 'estimated') && (
                      <span className="text-xs text-neutral-600">
                        {row.current_synthetic ? 'simulado' : 'estimado'}
                      </span>
                    )}
                  </span>
                </td>
                <td className="px-3 py-3">
                  <UvBadge uv={row.peak_today} size="sm" />
                </td>
                <td className="px-3 py-3 tabular-nums">{row.hours_above_8} h</td>
                <td className="px-3 py-3">
                  <span className="flex items-center gap-2">
                    <trend.icon aria-hidden="true" size={16} />
                    <span>{trend.label}</span>
                    <Sparkline values={row.sparkline} />
                  </span>
                </td>
                {showVulnerability && (
                  <td className="px-3 py-3 tabular-nums">{row.vulnerability?.toFixed(1) ?? '–'}</td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
