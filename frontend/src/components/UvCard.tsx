import { Clock, Moon, WifiOff } from 'lucide-react'
import type { Current } from '../api/types'
import { useAnimatedNumber } from '../hooks/useAnimatedNumber'
import { hourLabel, relativeTime } from '../lib/format'
import { UV_LEVELS } from '../theme/uvScale'
import { UvIcon } from './UvIcon'

interface Props {
  current: Current
  now?: Date
  children?: React.ReactNode
}

function NightPeak({ current }: { current: Current }) {
  const peak = current.next_peak
  if (!peak) return null
  const tz = current.city.timezone
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: tz }).format(new Date())
  const when = peak.date === today ? 'Hoje' : 'Amanhã'
  const range = peak.start && peak.end ? `, das ${hourLabel(peak.start, tz)} às ${hourLabel(peak.end, tz)}` : ''
  return (
    <p className="text-lg font-medium">
      {when} o pico deve chegar a {Math.round(peak.uv_max)}
      {range}.
    </p>
  )
}

/** Card principal: um número grande, uma cor, uma frase. */
export function UvCard({ current, now = new Date(), children }: Props) {
  const uv = current.display_uv ?? 0
  const animated = useAnimatedNumber(uv)

  if (current.status === 'no_data' || !current.level) {
    return (
      <section
        aria-labelledby="uv-card-title"
        className="rounded-3xl border border-neutral-300 bg-white p-6"
      >
        <h2 id="uv-card-title" className="text-lg font-semibold">
          UV agora em {current.city.name}
        </h2>
        <p className="mt-2 text-neutral-700">
          Ainda não temos leituras para esta cidade. Assim que a estação enviar dados, eles
          aparecem aqui.
        </p>
      </section>
    )
  }

  const level = UV_LEVELS[current.level.key]
  const measuredAgo = current.measured_at ? relativeTime(current.measured_at, now) : null
  const isNight = current.status === 'night'
  const isStale = current.status === 'stale'

  return (
    <section
      aria-labelledby="uv-card-title"
      className="rounded-3xl p-6 shadow-sm transition-colors duration-500 md:p-8"
      style={{ backgroundColor: level.bg, color: level.fg }}
    >
      <div className="flex items-start justify-between gap-4">
        <h2 id="uv-card-title" className="text-base font-semibold opacity-90">
          UV agora em {current.city.name}
        </h2>
        {isStale && (
          <span className="inline-flex items-center gap-1 rounded-full bg-black/25 px-3 py-1 text-sm font-semibold text-white">
            <WifiOff aria-hidden="true" size={14} /> Desatualizado
          </span>
        )}
      </div>

      <div className="mt-2 flex items-center gap-4">
        <span
          data-testid="uv-value"
          className="text-[88px] leading-none font-extrabold tabular-nums md:text-[96px]"
          aria-label={`Índice UV ${Math.round(uv)}`}
        >
          {Math.round(animated)}
        </span>
        <div className="flex flex-col gap-1">
          <span className="flex items-center gap-2 text-2xl font-bold">
            {isNight ? <Moon aria-hidden="true" size={26} /> : <UvIcon level={current.level.key} size={26} />}
            {current.level.label}
          </span>
        </div>
      </div>

      <div className="mt-4 space-y-1">
        {isNight ? (
          <>
            <p className="text-xl font-semibold">O sol já se pôs. UV zero agora.</p>
            <NightPeak current={current} />
          </>
        ) : (
          <>
            <p className="text-xl font-semibold">{current.level.recommendation}</p>
            {current.minutes_to_burn != null && (
              <p className="text-lg font-medium">
                Você pode se queimar em cerca de {current.minutes_to_burn} min agora.
              </p>
            )}
          </>
        )}
      </div>

      {children}

      <p className="mt-4 flex items-center gap-1.5 text-sm opacity-90">
        <Clock aria-hidden="true" size={14} />
        {isStale && measuredAgo && `Estação sem dados novos · última medição ${measuredAgo}`}
        {!isStale &&
          current.display_kind === 'estimated' &&
          `Estimado agora pela previsão${measuredAgo ? ` · última medição ${measuredAgo}` : ''}`}
        {!isStale && current.display_kind === 'measured' && measuredAgo && `Medido · atualizado ${measuredAgo}`}
      </p>
    </section>
  )
}
