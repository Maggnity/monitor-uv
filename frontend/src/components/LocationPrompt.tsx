import { LocateFixed } from 'lucide-react'

interface Props {
  onAllow: () => void
  onDismiss: () => void
}

export function LocationPrompt({ onAllow, onDismiss }: Props) {
  return (
    <section
      aria-labelledby="location-title"
      className="rounded-3xl border border-neutral-300 bg-white p-5"
    >
      <h2 id="location-title" className="flex items-center gap-2 text-lg font-bold">
        <LocateFixed aria-hidden="true" size={20} /> Ver o UV da sua cidade
      </h2>
      <p className="mt-1 text-neutral-700">
        Usamos sua localização só para mostrar o UV da cidade mais próxima.
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={onAllow}
          className="min-h-11 rounded-xl bg-neutral-900 px-4 font-semibold text-white focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        >
          Permitir localização
        </button>
        <button
          type="button"
          onClick={onDismiss}
          className="min-h-11 rounded-xl border border-neutral-300 px-4 font-semibold focus-visible:outline-3 focus-visible:outline-blue-600"
        >
          Escolher cidade
        </button>
      </div>
    </section>
  )
}
