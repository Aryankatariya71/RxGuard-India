import { useMemo, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { RotateCcw } from 'lucide-react'
import type { DailyIngredient, LineItem } from '../../api/types'

interface Props {
  items: LineItem[]
  doses: DailyIngredient[]
}

/** Hero: brands crack open into ingredient chips, then flow into shared nodes. */
export function IngredientXray({ items, doses }: Props) {
  const reduce = useReducedMotion()
  const [playId, setPlayId] = useState(0)

  const graph = useMemo(() => {
    const brands: { name: string; chips: { label: string; ingredient: string }[] }[] = []
    for (const it of items || []) {
      if (!it.matched_brand || !it.resolved) continue
      const chips = (it.ingredients || [])
        .filter((i) => i.ingredient)
        .map((i) => {
          const name = String(i.ingredient)
          const sv = i.strength_value
          const unit = i.unit || ''
          const label = sv != null ? `${name} ${sv}${unit ? ` ${unit}` : ''}` : name
          return { label, ingredient: name }
        })
      if (chips.length) brands.push({ name: it.matched_brand, chips })
    }
    const ingCount: Record<string, number> = {}
    for (const b of brands) {
      for (const c of b.chips) ingCount[c.ingredient] = (ingCount[c.ingredient] || 0) + 1
    }
    for (const d of doses || []) {
      const n = new Set((d.contributions || []).map((c) => c.brand)).size
      if (n > (ingCount[d.ingredient] || 0)) ingCount[d.ingredient] = n
    }
    return {
      brands,
      ingCount,
      ingredients: Object.keys(ingCount).sort(),
    }
  }, [items, doses])

  if (graph.brands.length === 0) return null

  const h = Math.max(200, graph.brands.length * 64, graph.ingredients.length * 52)
  const leftX = 24
  const rightX = 300
  const brandY = (i: number) =>
    36 + (i * (h - 48)) / Math.max(1, graph.brands.length - 1 || 1)
  const ingY = (i: number) =>
    36 + (i * (h - 48)) / Math.max(1, graph.ingredients.length - 1 || 1)

  return (
    <div className="print-report space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
          Ingredient X-ray
        </h3>
        <button
          type="button"
          className="glass glass-hover inline-flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-medium"
          onClick={() => setPlayId((n) => n + 1)}
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden />
          Replay
        </button>
      </div>
      <p className="text-xs text-[var(--muted)]">
        Brands open into their resolved ingredients from the engine. Shared ingredients glow when
        present in 2+ products.
      </p>
      <div className="glass overflow-x-auto rounded-2xl p-4" key={playId}>
        <svg
          viewBox={`0 0 440 ${h}`}
          className="mx-auto w-full max-w-xl"
          role="img"
          aria-label="Brand cards cracking into ingredients then flowing to shared nodes"
        >
          {graph.brands.map((b, bi) =>
            b.chips.map((chip) => {
              const ii = graph.ingredients.indexOf(chip.ingredient)
              if (ii < 0) return null
              const y1 = brandY(bi)
              const y2 = ingY(ii)
              const dup = (graph.ingCount[chip.ingredient] || 0) >= 2
              const path = `M ${leftX + 118} ${y1} C ${leftX + 180} ${y1}, ${rightX - 50} ${y2}, ${rightX} ${y2}`
              return (
                <motion.path
                  key={`${b.name}-${chip.label}-${playId}`}
                  d={path}
                  fill="none"
                  stroke={dup ? 'rgba(244,63,94,0.65)' : 'rgba(99,102,241,0.4)'}
                  strokeWidth={dup ? 2.5 : 1.5}
                  initial={reduce ? false : { pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  transition={{ duration: reduce ? 0 : 0.9, delay: reduce ? 0 : 0.55 + bi * 0.08 }}
                />
              )
            }),
          )}

          {graph.brands.map((b, i) => (
            <motion.g
              key={`${b.name}-${playId}`}
              initial={reduce ? false : { scaleX: 1 }}
              animate={{ scaleX: 1 }}
            >
              <motion.rect
                x={leftX}
                y={brandY(i) - 16}
                width={118}
                height={32}
                rx={10}
                fill="rgba(20,184,166,0.14)"
                stroke="rgba(20,184,166,0.45)"
                initial={reduce ? false : { scaleX: 1, opacity: 1 }}
                animate={
                  reduce
                    ? undefined
                    : {
                        scaleX: [1, 1.04, 0.92, 1],
                        opacity: [1, 1, 0.85, 1],
                      }
                }
                transition={{ duration: 0.7, delay: i * 0.05 }}
                style={{ transformOrigin: `${leftX + 59}px ${brandY(i)}px` }}
              />
              <text
                x={leftX + 59}
                y={brandY(i) + 4}
                textAnchor="middle"
                style={{ fontSize: 9, fill: '#99f6e4' }}
              >
                {b.name.length > 16 ? `${b.name.slice(0, 14)}…` : b.name}
              </text>
              {b.chips.map((chip, ci) => (
                <motion.g
                  key={chip.label}
                  initial={reduce ? false : { opacity: 0, y: -6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: reduce ? 0 : 0.35 + ci * 0.06 + i * 0.04 }}
                >
                  <title>{chip.label}</title>
                </motion.g>
              ))}
            </motion.g>
          ))}

          {graph.ingredients.map((ing, i) => {
            const dup = (graph.ingCount[ing] || 0) >= 2
            const count = graph.ingCount[ing] || 0
            return (
              <motion.g
                key={`${ing}-${playId}`}
                initial={reduce ? false : { opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: reduce ? 0 : 0.75 + i * 0.05 }}
              >
                <rect
                  x={rightX}
                  y={ingY(i) - 16}
                  width={128}
                  height={32}
                  rx={10}
                  fill={dup ? 'rgba(244,63,94,0.18)' : 'rgba(99,102,241,0.12)'}
                  stroke={dup ? 'rgba(244,63,94,0.7)' : 'rgba(99,102,241,0.4)'}
                  className={dup && !reduce ? 'animate-pulse' : undefined}
                />
                <text
                  x={rightX + 56}
                  y={ingY(i) + 4}
                  textAnchor="middle"
                  style={{ fontSize: 9, fill: dup ? '#fda4af' : '#c7d2fe' }}
                >
                  {ing.length > 14 ? `${ing.slice(0, 12)}…` : ing}
                </text>
                {dup && (
                  <g>
                    <circle cx={rightX + 118} cy={ingY(i) - 10} r={9} fill="#e11d48" />
                    <text
                      x={rightX + 118}
                      y={ingY(i) - 7}
                      textAnchor="middle"
                      style={{ fontSize: 8, fill: '#fff', fontWeight: 700 }}
                    >
                      {count}
                    </text>
                    <title>{`in ${count} products`}</title>
                  </g>
                )}
              </motion.g>
            )
          })}
        </svg>

        {/* Chip strip under SVG — cracked-open ingredients with strengths */}
        <div className="mt-4 space-y-2">
          {graph.brands.map((b, bi) => (
            <motion.div
              key={`${b.name}-chips-${playId}`}
              className="flex flex-wrap items-center gap-2"
              initial={reduce ? false : { opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: reduce ? 0 : 0.4 + bi * 0.05 }}
            >
              <span className="text-[11px] font-semibold text-teal-300">{b.name} →</span>
              {b.chips.map((c) => {
                const dup = (graph.ingCount[c.ingredient] || 0) >= 2
                return (
                  <span
                    key={c.label}
                    className={`rounded-lg border px-2 py-1 font-mono text-[11px] ${
                      dup
                        ? 'border-rose-400/40 bg-rose-500/15 text-rose-200'
                        : 'border-indigo-400/30 bg-indigo-500/10 text-indigo-200'
                    }`}
                  >
                    {c.label}
                  </span>
                )
              })}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
