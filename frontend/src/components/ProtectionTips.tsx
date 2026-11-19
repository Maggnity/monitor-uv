import { ChevronDown, ShieldPlus } from 'lucide-react'
import type { UvLevelKey } from '../theme/uvScale'

const TIPS: Record<UvLevelKey, string[]> = {
  low: [
    'Pode aproveitar o ar livre normalmente.',
    'Óculos escuros ajudam em dias muito claros.',
    'Se for ficar muitas horas fora, passe protetor solar.',
  ],
  moderate: [
    'Passe protetor solar FPS 30 ou mais nas áreas expostas.',
    'Use óculos escuros com proteção UV.',
    'Perto do meio-dia, prefira a sombra.',
  ],
  high: [
    'Protetor FPS 30 ou mais, reaplicado a cada 2 horas e após suar ou nadar.',
    'Chapéu de aba larga e óculos escuros.',
    'Procure sombra entre 10h e 16h.',
  ],
  very_high: [
    'Evite ficar ao sol entre 10h e 16h.',
    'Protetor FPS 50, reaplicado a cada 2 horas.',
    'Camisa de manga longa, chapéu e óculos escuros.',
    'Beba água com frequência.',
  ],
  extreme: [
    'Evite sair entre 10h e 16h. Pele desprotegida pode queimar em poucos minutos.',
    'Se precisar sair: protetor FPS 50+, roupa que cubra o corpo, chapéu e óculos.',
    'Crianças, idosos e pessoas de pele clara devem ficar na sombra.',
  ],
}

export function ProtectionTips({ level }: { level: UvLevelKey }) {
  return (
    <details className="group rounded-3xl bg-white p-5 shadow-sm">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-2 text-lg font-bold focus-visible:outline-3 focus-visible:outline-blue-600">
        <span className="flex items-center gap-2">
          <ShieldPlus aria-hidden="true" size={20} /> Como se proteger agora
        </span>
        <ChevronDown
          aria-hidden="true"
          size={20}
          className="transition-transform group-open:rotate-180"
        />
      </summary>
      <ul className="mt-3 list-disc space-y-1 pl-6 text-neutral-800">
        {TIPS[level].map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </details>
  )
}
