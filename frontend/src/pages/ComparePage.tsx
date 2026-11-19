import { Download, FlaskConical } from 'lucide-react'
import { useState } from 'react'
import { API_BASE } from '../api/client'
import { useCities, useCompare, useHistory } from '../api/hooks'
import type { Period } from '../api/types'
import { CalendarHeatmap } from '../components/CalendarHeatmap'
import { CityCompareTable } from '../components/CityCompareTable'
import { CompareChart, MAX_COMPARE } from '../components/CompareChart'
import { ErrorState } from '../components/ErrorState'
import { Skeleton } from '../components/Skeleton'

const PERIODS: { value: Period; label: string }[] = [
  { value: '7d', label: '7 dias' },
  { value: '30d', label: '30 dias' },
  { value: '12m', label: '12 meses' },
]

function SyntheticNotice() {
  return (
    <p className="flex items-center gap-1.5 text-sm text-neutral-600">
      <FlaskConical aria-hidden="true" size={14} />
      Inclui dados sintéticos de demonstração.
    </p>
  )
}

export function ComparePage() {
  const cities = useCities()
  const [selected, setSelected] = useState<number[]>([1, 2, 3, 4])
  const compare = useCompare(selected)
  const [historyCity, setHistoryCity] = useState(1)
  const [period, setPeriod] = useState<Period>('12m')
  const history = useHistory(historyCity, period)

  const toggle = (id: number) =>
    setSelected((ids) =>
      ids.includes(id) ? ids.filter((i) => i !== id) : ids.length < MAX_COMPARE ? [...ids, id] : ids,
    )

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">Comparar cidades</h1>
          <p className="text-neutral-700">Situação de hoje e histórico, para acompanhamento.</p>
        </div>
        <a
          href={`${API_BASE}/compare/export.csv`}
          download
          className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-neutral-900 px-4 font-semibold text-white focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          <Download aria-hidden="true" size={18} /> Exportar CSV
        </a>
      </div>

      {compare.isPending ? (
        <Skeleton className="h-64" label="Carregando a comparação" />
      ) : compare.isError ? (
        <ErrorState message="Não foi possível carregar a comparação." onRetry={() => compare.refetch()} />
      ) : (
        <>
          <CityCompareTable rows={compare.data.rows} />
          {compare.data.contains_synthetic && <SyntheticNotice />}
          <CompareChart
            cities={cities.data ?? compare.data.rows.map((r) => r.city)}
            selected={selected}
            onToggle={toggle}
            series={compare.data.series}
          />
        </>
      )}

      <section aria-labelledby="history-title" className="rounded-3xl bg-white p-5 shadow-sm">
        <h2 id="history-title" className="text-lg font-bold">
          Histórico do UV máximo
        </h2>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2">
            <span className="text-sm text-neutral-700">Cidade</span>
            <select
              value={historyCity}
              onChange={(e) => setHistoryCity(Number(e.target.value))}
              className="min-h-11 rounded-xl border border-neutral-300 bg-white px-3 font-medium focus:outline-3 focus:outline-blue-600"
            >
              {(cities.data ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          <div role="radiogroup" aria-label="Período" className="inline-flex rounded-xl border border-neutral-300 p-1">
            {PERIODS.map((p) => (
              <button
                key={p.value}
                type="button"
                role="radio"
                aria-checked={period === p.value}
                onClick={() => setPeriod(p.value)}
                className={`min-h-11 rounded-lg px-3 font-semibold focus-visible:outline-3 focus-visible:outline-blue-600 ${
                  period === p.value ? 'bg-neutral-900 text-white' : 'text-neutral-700'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-4">
          {history.isPending ? (
            <Skeleton className="h-32" label="Carregando o histórico" />
          ) : history.isError ? (
            <ErrorState message="Não foi possível carregar o histórico." onRetry={() => history.refetch()} />
          ) : (
            <>
              <CalendarHeatmap days={history.data.days} />
              {history.data.contains_synthetic && (
                <div className="mt-2">
                  <SyntheticNotice />
                </div>
              )}
            </>
          )}
        </div>
      </section>
    </div>
  )
}
