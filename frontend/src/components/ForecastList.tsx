import {
  Cloud,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSun,
  Snowflake,
  Sun,
  type LucideIcon,
} from 'lucide-react'
import type { ForecastDay } from '../api/types'
import { weekdayLabel } from '../lib/format'
import { UvBadge } from './UvBadge'

function weather(code: number | null): { icon: LucideIcon; label: string } {
  if (code === null) return { icon: Cloud, label: 'Sem previsão do tempo' }
  if (code === 0) return { icon: Sun, label: 'Céu limpo' }
  if (code <= 2) return { icon: CloudSun, label: 'Poucas nuvens' }
  if (code === 3) return { icon: Cloud, label: 'Nublado' }
  if (code === 45 || code === 48) return { icon: CloudFog, label: 'Neblina' }
  if (code >= 71 && code <= 77) return { icon: Snowflake, label: 'Neve' }
  if (code >= 95) return { icon: CloudLightning, label: 'Tempestade' }
  return { icon: CloudRain, label: 'Chuva' }
}

export function ForecastList({ days, today }: { days: ForecastDay[]; today: string }) {
  return (
    <section aria-labelledby="forecast-title" className="rounded-3xl bg-white p-5 shadow-sm">
      <h2 id="forecast-title" className="text-lg font-bold">
        Próximos dias
      </h2>
      {days.length === 0 ? (
        <p className="mt-2 text-neutral-600">Previsão indisponível no momento.</p>
      ) : (
        <ul className="mt-2 divide-y divide-neutral-100">
          {days.map((day) => {
            const { icon: Icon, label } = weather(day.weather_code)
            return (
              <li key={day.date} className="flex min-h-12 items-center gap-3 py-2">
                <span className="w-12 font-semibold">{weekdayLabel(day.date, today)}</span>
                <Icon aria-hidden="true" size={22} className="text-neutral-600" />
                <span className="flex-1 text-sm text-neutral-700">{label}</span>
                <span className="sr-only">UV máximo</span>
                <UvBadge uv={day.uv_max} levelKey={day.level.key} size="sm" />
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
