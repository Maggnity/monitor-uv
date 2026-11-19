import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { City, Compare } from '../api/types'
import { hourLabel } from '../lib/format'

/** Cores das linhas: neutras em relação à escala de UV, com traço diferente para não depender só da cor. */
const SERIES_STYLE = [
  { color: '#1D4ED8', dash: undefined },
  { color: '#0F766E', dash: '6 3' },
  { color: '#BE185D', dash: '2 3' },
  { color: '#404040', dash: '10 4' },
]

export const MAX_COMPARE = 4

interface Props {
  cities: City[]
  selected: number[]
  onToggle: (id: number) => void
  series: Compare['series']
}

export function CompareChart({ cities, selected, onToggle, series }: Props) {
  const timeZone = cities[0]?.timezone ?? 'America/Sao_Paulo'
  const byTime = new Map<string, Record<string, number | string>>()
  for (const s of series) {
    for (const p of s.points) {
      const label = hourLabel(p.time, timeZone)
      const entry = byTime.get(label) ?? { hora: label }
      entry[`c${s.city_id}`] = p.uv
      byTime.set(label, entry)
    }
  }
  const data = [...byTime.values()]
  const name = (id: number) => cities.find((c) => c.id === id)?.name ?? `Cidade ${id}`

  return (
    <section aria-labelledby="compare-chart-title" className="rounded-3xl bg-white p-5 shadow-sm">
      <h2 id="compare-chart-title" className="text-lg font-bold">
        UV ao longo de hoje
      </h2>
      <fieldset className="mt-3">
        <legend className="text-sm text-neutral-700">Escolha até {MAX_COMPARE} cidades</legend>
        <div className="mt-2 flex flex-wrap gap-2">
          {cities.map((city) => {
            const checked = selected.includes(city.id)
            const disabled = !checked && selected.length >= MAX_COMPARE
            return (
              <label
                key={city.id}
                className={`inline-flex min-h-11 cursor-pointer items-center gap-2 rounded-xl border px-3 has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-blue-600 ${
                  checked ? 'border-neutral-900 bg-neutral-900 text-white' : 'border-neutral-300'
                } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
                title={disabled ? `Máximo de ${MAX_COMPARE} cidades` : undefined}
              >
                <input
                  type="checkbox"
                  className="sr-only"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => onToggle(city.id)}
                />
                {city.name}
              </label>
            )
          })}
        </div>
      </fieldset>
      <div className="mt-4 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -20 }}>
            <CartesianGrid vertical={false} stroke="#E5E5E5" />
            <XAxis dataKey="hora" tickLine={false} axisLine={false} fontSize={12} interval={2} />
            <YAxis tickLine={false} axisLine={false} fontSize={12} />
            <Tooltip />
            <Legend />
            {series.map((s, i) => (
              <Line
                key={s.city_id}
                dataKey={`c${s.city_id}`}
                name={name(s.city_id)}
                stroke={SERIES_STYLE[i % SERIES_STYLE.length].color}
                strokeDasharray={SERIES_STYLE[i % SERIES_STYLE.length].dash}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}
