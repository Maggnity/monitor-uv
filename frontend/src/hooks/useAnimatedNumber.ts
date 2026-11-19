import { useEffect, useRef, useState } from 'react'

function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

/** Anima a troca de um número (ex.: ao mudar de cidade), sem animar se o usuário pedir menos movimento. */
export function useAnimatedNumber(target: number, durationMs = 500): number {
  const [value, setValue] = useState(target)
  const from = useRef(target)

  useEffect(() => {
    if (prefersReducedMotion() || typeof requestAnimationFrame === 'undefined') {
      from.current = target
      setValue(target)
      return
    }
    const start = performance.now()
    const initial = from.current
    let frame = 0
    const tick = (time: number) => {
      const progress = Math.min((time - start) / durationMs, 1)
      const eased = 1 - (1 - progress) ** 3
      setValue(initial + (target - initial) * eased)
      if (progress < 1) frame = requestAnimationFrame(tick)
      else from.current = target
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [target, durationMs])

  return value
}
