import { useMemo } from 'react'
import type { DailyIngredient, LineItem } from '../../api/types'

interface Props {
  items: LineItem[]
  doses: DailyIngredient[]
}

export function IngredientFlow({ items, doses }: Props) {
  const graph = useMemo(() => {
    const brands: { name: string; ings: string[] }[] = []
    for (const it of items || []) {
      if (!it.matched_brand) continue
      const ings = (it.ingredients || [])
        .map((i) => i.ingredient)
        .filter(Boolean) as string[]
      brands.push({ name: it.matched_brand, ings })
    }
    const ingCount: Record<string, number> = {}
    for (const b of brands) {
      for (const i of b.ings) ingCount[i] = (ingCount[i] || 0) + 1
    }
    // Also from dose contributions for hidden duplicates
    for (const d of doses || []) {
      const n = new Set((d.contributions || []).map((c) => c.brand)).size
      if (n > (ingCount[d.ingredient] || 0)) ingCount[d.ingredient] = n
    }
    return { brands, ingCount, ingredients: Object.keys(ingCount).sort() }
  }, [items, doses])

  if (graph.brands.length === 0) return null

  const h = Math.max(180, graph.brands.length * 56, graph.ingredients.length * 48)
  const leftX = 20
  const rightX = 280
  const brandY = (i: number) => 30 + (i * (h - 40)) / Math.max(1, graph.brands.length - 1 || 1)
  const ingY = (i: number) => 30 + (i * (h - 40)) / Math.max(1, graph.ingredients.length - 1 || 1)

  return (
    <div className="print-report space-y-3">
      <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
        Ingredient flow
      </h3>
      <div className="glass overflow-x-auto rounded-2xl p-4">
        <svg
          viewBox={`0 0 420 ${h}`}
          className="mx-auto w-full max-w-lg"
          role="img"
          aria-label="Brands connected to ingredients"
        >
          {graph.brands.map((b, bi) =>
            b.ings.map((ing) => {
              const ii = graph.ingredients.indexOf(ing)
              if (ii < 0) return null
              const y1 = brandY(bi)
              const y2 = ingY(ii)
              const dup = (graph.ingCount[ing] || 0) >= 2
              const path = `M ${leftX + 110} ${y1} C ${leftX + 170} ${y1}, ${rightX - 40} ${y2}, ${rightX} ${y2}`
              return (
                <path
                  key={`${b.name}-${ing}`}
                  d={path}
                  fill="none"
                  stroke={dup ? 'rgba(244,63,94,0.55)' : 'rgba(99,102,241,0.35)'}
                  strokeWidth={dup ? 2.5 : 1.5}
                  className={dup ? 'animate-pulse' : undefined}
                />
              )
            }),
          )}
          {graph.brands.map((b, i) => (
            <g key={b.name}>
              <rect
                x={leftX}
                y={brandY(i) - 14}
                width={110}
                height={28}
                rx={8}
                fill="rgba(20,184,166,0.12)"
                stroke="rgba(20,184,166,0.35)"
              />
              <text
                x={leftX + 55}
                y={brandY(i) + 4}
                textAnchor="middle"
                className="fill-current"
                style={{ fontSize: 9, fill: '#99f6e4' }}
              >
                {b.name.length > 16 ? `${b.name.slice(0, 14)}…` : b.name}
              </text>
            </g>
          ))}
          {graph.ingredients.map((ing, i) => {
            const dup = (graph.ingCount[ing] || 0) >= 2
            return (
              <g key={ing}>
                <rect
                  x={rightX}
                  y={ingY(i) - 14}
                  width={120}
                  height={28}
                  rx={8}
                  fill={dup ? 'rgba(244,63,94,0.15)' : 'rgba(99,102,241,0.12)'}
                  stroke={dup ? 'rgba(244,63,94,0.55)' : 'rgba(99,102,241,0.35)'}
                  className={dup ? 'animate-pulse' : undefined}
                />
                <text
                  x={rightX + 60}
                  y={ingY(i) + 4}
                  textAnchor="middle"
                  style={{ fontSize: 9, fill: dup ? '#fda4af' : '#c7d2fe' }}
                >
                  {ing}
                </text>
              </g>
            )
          })}
        </svg>
      </div>
    </div>
  )
}
