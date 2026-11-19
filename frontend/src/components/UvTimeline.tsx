import {
  Area,
  AreaChart,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Today } from '../api/types'
import { hourLabel, peakLabel } from '../lib/format'
import { UV_LEVELS, UV_LEVEL_ORDER, levelFromUv } from '../theme/uvScale'

interface Props {
  today: Today
  timeZone: string
  now?: Date
}

function localHour(date: Date, timeZone: string): number {
  const parts = new Intl.DateTimeFormat('en-GB', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(date)
  const get = (t: string) => Number(parts.find((p) => p.type === t)?.value ?? 0)
  return get('hour') + get('minute') / 60
}

/** Linha do tempo de hoje (6h–19h) com as faixas da escala ao fundo e o marcador do "agora". */
export function UvTimeline({ today, timeZone, now = new Date() }: Props) {
  const data = today.hourly.map((p) => ({ hour: localHour(new Date(p.time), timeZone), uv: p.uv }))
  const top = Math.max(12, ...data.map((d) => d.uv + 1))
  const nowHour = localHour(now, timeZone)
  const peak = today.peak

  return (
    <section aria-labelledby="timeline-title" className="rounded-3xl bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 id="timeline-title" className="text-lg font-bold">
          Hoje, hora a hora
        </h2>
        {peak && (
          <p className="font-semibold text-neutral-800">
            {peakLabel(peak.uv_max, peak.start, peak.end, timeZone)}
          </p>
        )}
      </div>
      {data.length === 0 ? (
        <p className="mt-3 text-neutral-600">A previsão de hoje ainda não está disponível.</p>
      ) : (
        <>
          <div className="mt-3 h-52" aria-hidden="true">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -24 }}>
                {UV_LEVEL_ORDER.map((key) => {
                  const [min, max] = UV_LEVELS[key].range
                  return (
                    <ReferenceArea
                      key={key}
                      y1={min === 0 ? 0 : min - 0.5}
                      y2={max === null ? top : max + 0.5}
                      fill={UV_LEVELS[key].bg}
                      fillOpacity={0.12}
                      stroke="none"
                    />
                  )
                })}
                <XAxis
                  dataKey="hour"
                  type="number"
                  domain={[6, 19]}
                  ticks={[6, 9, 12, 15, 18]}
                  tickFormatter={(h) => `${h}h`}
                  tickLine={false}
                  axisLine={false}
                  fontSize={12}
                />
                <YAxis domain={[0, top]} ticks={[0, 3, 6, 8, 11]} tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip
                  formatter={(value) => [
                    `${Math.round(Number(value))} – ${UV_LEVELS[levelFromUv(Number(value))].label}`,
                    'UV',
                  ]}
                  labelFormatter={(h) => `${Math.floor(Number(h))}h`}
                />
                <Area
                  type="monotone"
                  dataKey="uv"
                  stroke="#262626"
                  strokeWidth={2}
                  fill="#262626"
                  fillOpacity={0.08}
                  isAnimationActive={false}
                />
                {nowHour >= 6 && nowHour <= 19 && (
                  <ReferenceLine
                    x={nowHour}
                    stroke="#171717"
                    strokeDasharray="4 3"
                    label={{ value: 'agora', position: 'insideTopRight', fontSize: 12, fill: '#171717' }}
                  />
                )}
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <p className="sr-only">
            {peak
              ? `${peakLabel(peak.uv_max, peak.start, peak.end, timeZone)}. O UV fica no pico entre ${hourLabel(peak.start, timeZone)} e ${hourLabel(peak.end, timeZone)}.`
              : 'Sem pico relevante hoje.'}{' '}
            {today.hours_above_8 > 0 && `${today.hours_above_8} horas com UV muito alto ou mais.`}
          </p>
        </>
      )}
    </section>
  )
}
