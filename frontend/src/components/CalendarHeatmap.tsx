import type { HistoryDay } from '../api/types'
import { UV_LEVELS, UV_LEVEL_ORDER } from '../theme/uvScale'

const CELL = 14
const GAP = 3
const WEEKDAYS = ['Dom', '', 'Ter', '', 'Qui', '', 'Sáb']

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('pt-BR', { day: '2-digit', month: 'short', timeZone: 'UTC' }).format(
    new Date(`${iso}T12:00:00Z`),
  )
}

/** Mapa de calor tipo calendário: colunas = semanas, linhas = dias da semana, cor = nível do UV máximo. */
export function CalendarHeatmap({ days }: { days: HistoryDay[] }) {
  if (days.length === 0) return <p className="text-neutral-600">Sem histórico para o período.</p>

  const first = new Date(`${days[0].date}T12:00:00Z`)
  const offset = first.getUTCDay()
  const cells = days.map((day, index) => {
    const position = index + offset
    return { day, col: Math.floor(position / 7), row: position % 7 }
  })
  const columns = (cells.at(-1)?.col ?? 0) + 1
  const width = 32 + columns * (CELL + GAP)
  const height = 7 * (CELL + GAP)
  const max = days.reduce((a, b) => (b.uv_max > a.uv_max ? b : a))

  return (
    <div>
      <div className="overflow-x-auto">
        <svg
          width={width}
          height={height}
          role="img"
          aria-label={`UV máximo diário de ${formatDate(days[0].date)} a ${formatDate(days.at(-1)!.date)}. Maior valor: ${Math.round(max.uv_max)} em ${formatDate(max.date)}.`}
        >
          {WEEKDAYS.map((label, row) => (
            <text key={row} x={0} y={row * (CELL + GAP) + CELL - 3} fontSize={10} fill="#525252">
              {label}
            </text>
          ))}
          {cells.map(({ day, col, row }) => (
            <rect
              key={day.date}
              x={32 + col * (CELL + GAP)}
              y={row * (CELL + GAP)}
              width={CELL}
              height={CELL}
              rx={3}
              fill={UV_LEVELS[day.level_key].bg}
              opacity={day.origin === 'forecast' ? 0.5 : 1}
            >
              <title>
                {`${formatDate(day.date)}: UV ${Math.round(day.uv_max)} (${UV_LEVELS[day.level_key].label})${
                  day.origin === 'sintetico' ? ' · dado de demonstração' : day.origin === 'forecast' ? ' · previsto' : ''
                }`}
              </title>
            </rect>
          ))}
        </svg>
      </div>
      <ul className="mt-3 flex flex-wrap gap-3 text-xs text-neutral-700" aria-label="Legenda">
        {UV_LEVEL_ORDER.map((key) => (
          <li key={key} className="flex items-center gap-1">
            <span aria-hidden="true" className="inline-block size-3 rounded-sm" style={{ background: UV_LEVELS[key].bg }} />
            {UV_LEVELS[key].label}
          </li>
        ))}
      </ul>
    </div>
  )
}
