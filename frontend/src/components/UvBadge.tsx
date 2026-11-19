import { UV_LEVELS, levelFromUv, type UvLevelKey } from '../theme/uvScale'
import { UvIcon } from './UvIcon'

interface Props {
  uv: number | null
  levelKey?: UvLevelKey
  size?: 'sm' | 'md'
  showLabel?: boolean
}

/** Chip com cor, ícone, número e rótulo do nível. */
export function UvBadge({ uv, levelKey, size = 'md', showLabel = true }: Props) {
  if (uv === null) {
    return <span className="text-sm text-neutral-500">sem dado</span>
  }
  const key = levelKey ?? levelFromUv(uv)
  const level = UV_LEVELS[key]
  const small = size === 'sm'
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full font-semibold ${
        small ? 'px-2 py-0.5 text-xs' : 'px-3 py-1 text-sm'
      }`}
      style={{ backgroundColor: level.bg, color: level.fg }}
      aria-label={`UV ${Math.round(uv)}, ${level.label}`}
    >
      <UvIcon level={key} size={small ? 12 : 14} strokeWidth={2.5} />
      <span aria-hidden="true">{Math.round(uv)}</span>
      {showLabel && <span aria-hidden="true">{level.label}</span>}
    </span>
  )
}
