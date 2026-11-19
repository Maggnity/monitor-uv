export function Skeleton({ className = '', label }: { className?: string; label?: string }) {
  return (
    <div
      className={`animate-pulse rounded-2xl bg-neutral-200 motion-reduce:animate-none ${className}`}
      role="status"
      aria-label={label ?? 'Carregando'}
    />
  )
}
