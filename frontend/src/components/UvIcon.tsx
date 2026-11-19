import { Glasses, OctagonAlert, ShieldCheck, Sun, TriangleAlert, type LucideProps } from 'lucide-react'
import type { UvLevelKey } from '../theme/uvScale'

const ICONS: Record<UvLevelKey, React.ComponentType<LucideProps>> = {
  low: ShieldCheck,
  moderate: Glasses,
  high: Sun,
  very_high: TriangleAlert,
  extreme: OctagonAlert,
}

/** Ícone do nível de UV: a cor nunca é o único indicador. */
export function UvIcon({ level, ...props }: { level: UvLevelKey } & LucideProps) {
  const Icon = ICONS[level]
  return <Icon aria-hidden="true" {...props} />
}
