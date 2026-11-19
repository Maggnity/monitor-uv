import { X } from 'lucide-react'
import { useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import type { MapPoint } from '../api/types'
import { UvBadge } from './UvBadge'

const KIND_LABEL = { measured: 'medido agora', estimated: 'estimado agora', forecast: 'previsto' }

interface Props {
  point: MapPoint
  onClose: () => void
}

/** Painel inferior (bottom sheet) com o resumo da cidade. Fecha com Esc e devolve o foco. */
export function CitySheet({ point, onClose }: Props) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    ref.current?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      previous?.focus?.()
    }
  }, [onClose])

  return (
    <div
      ref={ref}
      role="dialog"
      aria-modal="false"
      aria-labelledby="sheet-title"
      tabIndex={-1}
      className="fixed inset-x-0 bottom-16 z-[1050] rounded-t-3xl bg-white p-5 shadow-[0_-8px_30px_rgba(0,0,0,0.18)] outline-none md:absolute md:inset-x-auto md:right-4 md:bottom-4 md:w-80 md:rounded-3xl"
    >
      <div className="mx-auto mb-3 h-1.5 w-10 rounded-full bg-neutral-300 md:hidden" aria-hidden="true" />
      <div className="flex items-start justify-between gap-2">
        <h2 id="sheet-title" className="text-xl font-bold">
          {point.name}
        </h2>
        <button
          type="button"
          onClick={onClose}
          aria-label="Fechar"
          className="flex size-11 items-center justify-center rounded-full hover:bg-neutral-100 focus-visible:outline-3 focus-visible:outline-blue-600"
        >
          <X aria-hidden="true" size={20} />
        </button>
      </div>
      <div className="mt-2 flex items-center gap-2">
        <UvBadge uv={point.uv} levelKey={point.level?.key} />
        {point.kind && <span className="text-sm text-neutral-600">{KIND_LABEL[point.kind]}</span>}
      </div>
      {point.level && <p className="mt-3 font-semibold">{point.level.recommendation}</p>}
      <Link
        to={`/?cidade=${point.city_id}`}
        className="mt-4 inline-flex min-h-11 items-center rounded-xl bg-neutral-900 px-4 font-semibold text-white focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        Ver detalhes
      </Link>
    </div>
  )
}
