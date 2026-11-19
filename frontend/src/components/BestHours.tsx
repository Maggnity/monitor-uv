import { Footprints } from 'lucide-react'
import type { Today } from '../api/types'
import { hourLabel } from '../lib/format'

export function BestHours({ today, timeZone }: { today: Today; timeZone: string }) {
  return (
    <section aria-labelledby="best-hours-title" className="rounded-3xl bg-white p-5 shadow-sm">
      <h2 id="best-hours-title" className="flex items-center gap-2 text-lg font-bold">
        <Footprints aria-hidden="true" size={20} /> Melhores horários para sair
      </h2>
      {today.best_windows.length === 0 ? (
        <p className="mt-2 text-neutral-700">
          Hoje não há períodos com UV baixo entre 6h e 19h.
        </p>
      ) : (
        <ul className="mt-3 flex flex-wrap gap-2">
          {today.best_windows.map((w) => (
            <li
              key={w.start}
              className="rounded-full border border-neutral-300 px-4 py-2 font-semibold tabular-nums"
            >
              {hourLabel(w.start, timeZone)} – {hourLabel(w.end, timeZone)}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-sm text-neutral-600">Períodos com UV baixo (até 2).</p>
    </section>
  )
}
