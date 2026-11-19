import { RefreshCw, WifiOff } from 'lucide-react'

interface Props {
  message?: string
  onRetry: () => void
}

export function ErrorState({ message = 'Não foi possível carregar os dados.', onRetry }: Props) {
  return (
    <div
      role="alert"
      className="flex flex-col items-start gap-3 rounded-2xl border border-neutral-300 bg-white p-4"
    >
      <p className="flex items-center gap-2 font-medium text-neutral-800">
        <WifiOff aria-hidden="true" size={18} /> {message}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-neutral-900 px-4 font-semibold text-white focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
      >
        <RefreshCw aria-hidden="true" size={16} /> Tentar de novo
      </button>
    </div>
  )
}
