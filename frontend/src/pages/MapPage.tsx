import { useCallback, useState } from 'react'
import { useMap } from '../api/hooks'
import type { MapPoint, MapWhen } from '../api/types'
import { CitySheet } from '../components/CitySheet'
import { ErrorState } from '../components/ErrorState'
import { Skeleton } from '../components/Skeleton'
import { UvBadge } from '../components/UvBadge'
import { UvMap } from '../components/UvMap'
import { UV_LEVELS, UV_LEVEL_ORDER } from '../theme/uvScale'

const FILTERS: { value: MapWhen; label: string }[] = [
  { value: 'now', label: 'Agora' },
  { value: 'peak_today', label: 'Pico de hoje' },
  { value: 'tomorrow', label: 'Amanhã' },
]

function Legend() {
  return (
    <ul
      aria-label="Legenda da escala de UV"
      className="flex flex-wrap gap-x-3 gap-y-1 text-xs text-neutral-700"
    >
      {UV_LEVEL_ORDER.map((key) => (
        <li key={key} className="flex items-center gap-1.5">
          <span aria-hidden="true" className="inline-block size-3 rounded-full" style={{ background: UV_LEVELS[key].bg }} />
          {UV_LEVELS[key].label}
        </li>
      ))}
    </ul>
  )
}

export function MapPage() {
  const [when, setWhen] = useState<MapWhen>('now')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const map = useMap(when)
  const selected = map.data?.find((p) => p.city_id === selectedId) ?? null
  const close = useCallback(() => setSelectedId(null), [])
  const select = (point: MapPoint) => setSelectedId(point.city_id)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Mapa</h1>
        <div role="radiogroup" aria-label="Horário" className="inline-flex rounded-xl border border-neutral-300 bg-white p-1">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              role="radio"
              aria-checked={when === f.value}
              onClick={() => setWhen(f.value)}
              className={`min-h-11 rounded-lg px-3 font-semibold focus-visible:outline-3 focus-visible:outline-blue-600 ${
                when === f.value ? 'bg-neutral-900 text-white' : 'text-neutral-700'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {map.isPending ? (
        <Skeleton className="h-[60dvh]" label="Carregando o mapa" />
      ) : map.isError ? (
        <ErrorState message="Não foi possível carregar o mapa." onRetry={() => map.refetch()} />
      ) : (
        <>
          <Legend />
          <div className="relative isolate -mt-2 h-[60dvh] overflow-hidden rounded-3xl shadow-sm md:h-[65vh]">
            <UvMap points={map.data} onSelect={select} />
            {selected && <CitySheet point={selected} onClose={close} />}
          </div>

          <section aria-labelledby="city-list-title">
            <h2 id="city-list-title" className="mb-2 text-lg font-bold">
              Cidades
            </h2>
            <ul className="divide-y divide-neutral-100 rounded-3xl bg-white shadow-sm">
              {map.data.map((point) => (
                <li key={point.city_id}>
                  <button
                    type="button"
                    onClick={() => select(point)}
                    className="flex min-h-12 w-full items-center justify-between gap-3 px-4 py-2 text-left font-medium hover:bg-neutral-50 focus-visible:outline-3 focus-visible:-outline-offset-2 focus-visible:outline-blue-600"
                  >
                    {point.name}
                    <UvBadge uv={point.uv} levelKey={point.level?.key} size="sm" />
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </div>
  )
}
