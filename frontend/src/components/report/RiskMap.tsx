import { useEffect, useId, useMemo, useState } from 'react'
import { AlertTriangle, Copy, Link2 } from 'lucide-react'
import type { AnalyzeResponse } from '../../api/types'
import {
  buildRiskMap,
  circularLayout,
  edgePath,
  tierStroke,
  type RiskEdge,
} from '../../lib/riskMap'

interface Props {
  report: AnalyzeResponse
}

const W = 640
const H = 420

export function RiskMap({ report }: Props) {
  const uid = useId()
  const data = useMemo(
    () => buildRiskMap(report.items || [], report.alerts || []),
    [report.items, report.alerts],
  )
  // Prefer connected nodes; keep isolates so what-if still shows active ingredients
  const layoutNodes = useMemo(() => {
    if (!data.edges.length) return data.nodes
    const connected = new Set<string>()
    for (const e of data.edges) {
      connected.add(e.source)
      connected.add(e.target)
    }
    const primary = data.nodes.filter((n) => connected.has(n.id))
    const rest = data.nodes.filter((n) => !connected.has(n.id))
    return [...primary, ...rest]
  }, [data.nodes, data.edges])

  const positions = useMemo(
    () => circularLayout(layoutNodes, W, H),
    [layoutNodes],
  )
  const [selected, setSelected] = useState<RiskEdge | null>(null)
  const [focusEdge, setFocusEdge] = useState<string | null>(null)

  // Clear selection when what-if re-analysis changes the report
  useEffect(() => {
    setSelected(null)
    setFocusEdge(null)
  }, [report.verdict, report.counts?.critical, report.counts?.review, report.items?.length])

  const lineEdges = data.edges.filter((e) => !e.selfLoop)
  const ringEdges = data.edges.filter((e) => e.selfLoop)

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

        {layoutNodes.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--muted)]" role="status">
            No resolved ingredients to map yet.
          </p>
        ) : (
          <svg
            viewBox={`0 0 ${W} ${H}`}
            className="mt-3 w-full max-w-full rounded-xl bg-black/20"
            role="img"
            aria-label="Ingredient interaction and duplicate risk map"
          >
            <title>Risk map graph</title>

            {/* Interaction / multi-ingredient duplicate edges */}
            {lineEdges.map((e, idx) => {
              const a = positions.get(e.source)
              const b = positions.get(e.target)
              if (!a || !b) return null
              const stroke = tierStroke(e.tier)
              const active = focusEdge === e.id || selected?.id === e.id
              const bend = 0.12 + (idx % 3) * 0.06
              const d = edgePath(a.x, a.y, b.x, b.y, bend)
              return (
                <g key={e.id}>
                  {/* Wide invisible hit target */}
                  <path
                    d={d}
                    fill="none"
                    stroke="transparent"
                    strokeWidth={18}
                    className="cursor-pointer"
                    tabIndex={0}
                    role="button"
                    aria-label={`${e.kind} ${e.title}, rule ${e.ruleId}, tier ${e.tier}`}
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
                  />
                  <path
                    d={d}
                    fill="none"
                    stroke={stroke}
                    strokeWidth={active ? 4 : 2.5}
                    strokeDasharray={e.dashed ? '7 5' : undefined}
                    strokeLinecap="round"
                    pointerEvents="none"
                    opacity={active ? 1 : 0.9}
                  />
                </g>
              )
            })}

            {/* Nodes */}
            {layoutNodes.map((n) => {
              const p = positions.get(n.id)
              if (!p) return null
              const ring = ringEdges.find((e) => e.source === n.id)
              const ringStroke = ring ? tierStroke(ring.tier) : undefined
              const label =
                n.label.length > 16 ? `${n.label.slice(0, 15)}…` : n.label
              const brands =
                n.brands.length > 2
                  ? `${n.brands.slice(0, 2).join(', ')} +${n.brands.length - 2}`
                  : n.brands.join(', ')
              return (
                <g key={n.id} transform={`translate(${p.x}, ${p.y})`}>
                  {ring && (
                    <circle
                      r={28}
                      fill="none"
                      stroke={ringStroke}
                      strokeWidth={2.5}
                      strokeDasharray="6 4"
                      className="cursor-pointer"
                      tabIndex={0}
                      role="button"
                      aria-label={`Duplicate ${ring.title}, rule ${ring.ruleId}`}
                      onClick={() => setSelected(ring)}
                      onKeyDown={(ev) => {
                        if (ev.key === 'Enter' || ev.key === ' ') {
                          ev.preventDefault()
                          setSelected(ring)
                        }
                      }}
                      onFocus={() => setFocusEdge(ring.id)}
                      onBlur={() => setFocusEdge(null)}
                      onMouseEnter={() => setFocusEdge(ring.id)}
                      onMouseLeave={() => setFocusEdge(null)}
                    />
                  )}
                  <circle
                    r={20}
                    className="fill-slate-900 stroke-teal-400"
                    strokeWidth={2.5}
                  />
                  <text
                    textAnchor="middle"
                    y={36}
                    className="fill-slate-100 text-[11px] font-semibold"
                  >
                    {label}
                  </text>
                  {brands && (
                    <text
                      textAnchor="middle"
                      y={50}
                      className="fill-slate-400 text-[9px]"
                    >
                      {brands.length > 28 ? `${brands.slice(0, 27)}…` : brands}
                    </text>
                  )}
                  <title>
                    {n.label}
                    {n.brands.length ? ` — ${n.brands.join(', ')}` : ''}
                  </title>
                </g>
              )
            })}
          </svg>
        )}

        {data.emptyMessage && (
          <p className="mt-3 text-sm text-[var(--muted)]" role="status">
            {data.emptyMessage}
          </p>
        )}

        {selected && (
          <div
            className="mt-3 rounded-xl border border-white/10 bg-black/30 px-3 py-2 text-sm"
            role="status"
          >
            <p className="font-semibold">{selected.title}</p>
            <ul className="mt-1 space-y-0.5 text-xs text-[var(--muted)]">
              <li>
                <span className="text-[var(--fg)]">Rule id:</span> {selected.ruleId}
              </li>
              {selected.mechanism && (
                <li>
                  <span className="text-[var(--fg)]">Mechanism:</span>{' '}
                  {selected.mechanism}
                </li>
              )}
              <li>
                <span className="text-[var(--fg)]">Source:</span> {selected.sourceLabel}
              </li>
              {selected.version && (
                <li>
                  <span className="text-[var(--fg)]">Version:</span> {selected.version}
                </li>
              )}
              <li>
                <span className="text-[var(--fg)]">Status:</span> {selected.status}
              </li>
              <li>
                Tier: {selected.tier}
                {selected.dashed ? ' · dashed = duplicate' : ' · solid = interaction'}
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

        <div className="mt-4">
          <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
            Edge list (accessible fallback)
          </h4>
          {data.edges.length === 0 ? (
            <p className="mt-1 text-sm text-[var(--muted)]">
              No interaction or duplicate edges for the active medicines.
            </p>
          ) : (
            <ul className="mt-2 space-y-2">
              {data.edges.map((e) => (
                <li key={e.id}>
                  <button
                    type="button"
                    className={`w-full rounded-xl border px-3 py-2 text-left text-sm transition ${
                      selected?.id === e.id
                        ? 'border-teal-400/50 bg-teal-500/15'
                        : 'border-white/10 bg-white/5 hover:bg-white/10'
                    }`}
                    onClick={() => setSelected(e)}
                  >
                    <span className="inline-flex flex-wrap items-center gap-2">
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
          )}
        </div>
      </div>
    </section>
  )
}

function EdgeIcon({ edge }: { edge: RiskEdge }) {
  if (edge.icon === 'copy') return <Copy className="h-3.5 w-3.5 shrink-0" aria-hidden />
  if (edge.icon === 'alert')
    return <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
  return <Link2 className="h-3.5 w-3.5 shrink-0" aria-hidden />
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
        Duplicate (dashed ring / edge + copy icon)
      </li>
    </ul>
  )
}
