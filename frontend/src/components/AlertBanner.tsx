import { BellRing } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAlertTriggers } from '../api/hooks'
import { hourLabel } from '../lib/format'

/** Aviso no Início quando um alerta desta cidade disparou hoje. */
export function AlertBanner({ cityId, timeZone }: { cityId: number; timeZone: string }) {
  const triggers = useAlertTriggers()
  const latest = triggers.data?.find((t) => t.city_id === cityId)
  if (!latest) return null
  return (
    <div role="status" className="flex items-center gap-3 rounded-2xl border-2 border-neutral-900 bg-white p-4">
      <BellRing aria-hidden="true" size={22} />
      <p className="flex-1 font-semibold">
        Alerta: UV passou de {latest.threshold} em {latest.city_name} às {hourLabel(latest.triggered_at, timeZone)}
      </p>
      <Link to="/alertas" className="min-h-11 content-center font-semibold underline">
        Ver alertas
      </Link>
    </div>
  )
}
