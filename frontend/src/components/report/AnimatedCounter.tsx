import { useEffect, useState } from 'react'
import { useReducedMotion } from 'framer-motion'

export function AnimatedCounter({ value, duration = 700 }: { value: number; duration?: number }) {
  const reduce = useReducedMotion()
  const [n, setN] = useState(reduce ? value : 0)

  useEffect(() => {
    if (reduce) {
      setN(value)
      return
    }
    const start = performance.now()
    const from = 0
    let raf = 0
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / duration)
      setN(Math.round(from + (value - from) * (1 - Math.pow(1 - p, 3))))
      if (p < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [value, duration, reduce])

  return <span className="tabular-nums">{n}</span>
}
