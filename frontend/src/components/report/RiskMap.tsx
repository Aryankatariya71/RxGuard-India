import { useId, useMemo, useState } from 'react'
import { AlertTriangle, Copy, Link2 } from 'lucide-react'
import type { AnalyzeResponse } from '../../api/types'
import {
  buildRiskMap,
  circularLayout,
  tierStroke,
  type RiskEdge,
} from '../../lib/riskMap'

interface Props {
  report: AnalyzeResponse
}

const W = 560
const H = 360

export function RiskMap({ report }: Props) {
  const uid = useId()
  const data = useMemo(
    () => buildRiskMap(report.items || [], report.alerts || []),
    [report.items, report.alerts],
  )
  const positions = useMemo(
    () => circularLayout(data.nodes, W, H),
    [data.nodes],
  )
  const [selected, setSelected] = useState<RiskEdge | null>(null)
  const [focusEdge, setFocusEdge] = useState<string | null>(null)

  return (
    <section
      className="print-report space-y-3"
      aria-labelledby={`${uid}-heading`}
      data-testid="risk-map"
    >
      <h3
        id={`${uid}-heading`}
        className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]"
      >
        Risk map
      </h3>
      <div className="glass rounded-2xl p-4">
        <Legend />

        {data.emptyMessage ? (
          <p className="mt-4 text-sm text-[var(--muted)]" role="status">
            {data.emptyMessage}
          </p>
        ) : (
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="mt-3 w-full max-w-full"
            role="img"
            aria-label="Ingredient interaction and duplicate risk map"
          >
            <title>Risk map graph</title>
            {data.edges.map((e) => {
              const a = positions.get(e.source)
              const b = positions.get(e.target)
              if (!a || !b) return null
              const stroke = tierStroke(e.tier)
              const active = focusEdge === e.id || selected?.id === e.id
              const self = e.source === e.target
              const d = self
                ? `M ${a.x} ${a.y - 12} C ${a.x + 50} ${a.y - 70}, ${a.x - 50} ${a.y - 70}, ${a.x} ${a.y - 12}`
                : undefined
              return (
                <g key={e.id}>
                  {self ? (
                    <path
                      d={d}
                      fill="none"
                      stroke={stroke}
                      strokeWidth={active ? 3.5 : 2}
                      strokeDasharray={e.dashed ? '6 4' : undefined}
                      tabIndex={0}
                      role="button"
                      aria-label={`${e.kind} ${e.title}, rule ${e.ruleId}`}
                      onClick={() => setSelected(e)}
                      onKeyDown={(ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                          ev.preventDefault()
                          setSelected(e)
                        }
                      }}
                      onFocus={() => setFocusEdge(e.id)}
                      onBlur={() => setFocusEdge(null)}
                      onMouseEnter={() => setFocusEdge(e.id)}
                      onMouseLeave={() => setFocusEdge(null)}
                      className="cursor-pointer outline-none focus:opacity-100"
                    />
                  ) : (
                    <line
                      x1={a.x}
                      y1={a.y}
                      x2={b.x}
                      y2={b.y}
                      stroke={stroke}
                      strokeWidth={active ? 3.5 : 2}
                      strokeDasharray={e.dashed ? '6 4' : undefined}
                      tabIndex={0}
                      role="button"
                      aria-label={`${e.kind} ${e.title}, rule ${e.ruleId}`}
                      onClick={() => setSelected(e)}
                      onKeyDown={(ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                          ev.preventDefault()
                          setSelected(e)
                        }
                      }}
                      onFocus={() => setFocusEdge(e.id)}
                      onBlur={() => setFocusEdge(null)}
                      onMouseEnter={() => setFocusEdge(e.id)}
                      onMouseLeave={() => setFocusEdge(null)}
                      className="cursor-pointer outline-none"
                    />
                  )}
                </g>
              )
            })}
            {data.nodes.map((n) => {
              const p = positions.get(n.id)
              if (!p) return null
              return (
                <g key={n.id} transform={`translate(${p.x}, ${p.y})`}>
                  <circle r={18} className="fill-[var(--bg)] stroke-teal-400/60" strokeWidth={2} />
                  <text
                    textAnchor="middle"
                    dy="0.35em"
                    className="fill-[var(--fg)] text-[10px] font-semibold"
                  >
                    {n.label.length > 10 ? `${n.label.slice(0, 9)}…` : n.label}
                  </text>
                  <title>
                    {n.label} — {n.brands.join(', ')}
                  </title>
                </g>
              )
            })}
          </svg>
        )}

        {selected && (
          <div
            className="mt-3 rounded-xl border border-white/10 bg-black/20 px-3 py-2 text-sm"
            role="status"
          >
            <p className="font-semibold">{selected.title}</p>
            <ul className="mt-1 space-y-0.5 text-xs text-[var(--muted)]">
              <li>Rule id: {selected.ruleId}</li>
              {selected.mechanism && <li>Mechanism: {selected.mechanism}</li>}
              <li>Source: {selected.sourceLabel}</li>
              {selected.version && <li>Version: {selected.version}</li>}
              <li>Status: {selected.status}</li>
              <li>
                Tier: {selected.tier}
                {selected.dashed ? ' · dashed = duplicate' : ''}
              </li>
            </ul>
            <button
              type="button"
              className="mt-2 text-xs underline"
              onClick={() => setSelected(null)}
            >
              Close
            </button>
          </div>
        )}

        {data.edges.length > 0 && (
          <div className="mt-4">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              Edge list (accessible fallback)
            </h4>
            <ul className="mt-2 space-y-2">
              {data.edges.map((e) => (
                <li key={e.id}>
                  <button
                    type="button"
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left text-sm hover:bg-white/10"
                    onClick={() => setSelected(e)}
                  >
                    <span className="inline-flex items-center gap-2">
                      <EdgeIcon edge={e} />
                      <span className="font-medium">{e.title}</span>
                      <span
                        className="rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase"
                        style={{
                          background: `${tierStroke(e.tier)}33`,
                          color: tierStroke(e.tier),
                        }}
                      >
                        {e.tier}
                        {e.dashed ? ' · duplicate' : ' · interaction'}
                      </span>
                    </span>
                    <span className="mt-1 block text-xs text-[var(--muted)]">
                      {e.ruleId} · {e.status} · {e.sourceLabel}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}

function EdgeIcon({ edge }: { edge: RiskEdge }) {
  if (edge.icon === 'copy') return <Copy className="h-3.5 w-3.5" aria-hidden />
  if (edge.icon === 'alert') return <AlertTriangle className="h-3.5 w-3.5" aria-hidden />
  return <Link2 className="h-3.5 w-3.5" aria-hidden />
}

function Legend() {
  return (
    <ul className="flex flex-wrap gap-3 text-[11px] text-[var(--muted)]" aria-label="Legend">
      <li className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-5 bg-rose-500" aria-hidden />
        Critical (+ alert icon)
      </li>
      <li className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-5 bg-amber-500" aria-hidden />
        Review
      </li>
      <li className="inline-flex items-center gap-1.5">
        <span className="inline-block h-0.5 w-5 bg-sky-500" aria-hidden />
        Info
      </li>
      <li className="inline-flex items-center gap-1.5">
        <span
          className="inline-block h-0.5 w-5 border-t-2 border-dashed border-[var(--muted)]"
          aria-hidden
        />
        Duplicate (dashed + copy icon)
      </li>
    </ul>
  )
}
