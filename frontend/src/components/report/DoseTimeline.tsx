import { useMemo } from 'react'
import { useReducedMotion } from 'framer-motion'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { Alert, AnalyzeResponse } from '../../api/types'
import { buildTimeline, timelineColor } from '../../lib/timeline'
import { Pill } from 'lucide-react'

interface Props {
  report: AnalyzeResponse
}

export function DoseTimeline({ report }: Props) {
  const reduce = useReducedMotion()
  const data = useMemo(
    () =>
      buildTimeline(
        report.items || [],
        report.daily_doses?.by_ingredient || [],
        (report.alerts || []) as Alert[],
      ),
    [report],
  )

  return (
    <section className="print-report space-y-3" aria-labelledby="dose-timeline-heading">
      <h3 id="dose-timeline-heading" className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
        Your day
      </h3>
      <div className="glass rounded-2xl p-4">
        <p className="text-xs text-[var(--muted)]">{data.caption}</p>

        {data.unclear.length > 0 && (
          <div className="mt-3 rounded-xl border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-xs text-amber-100">
            <p className="font-semibold">Timeline not drawn: schedule unclear</p>
            <ul className="mt-1 list-inside list-disc">
              {data.unclear.map((u) => (
                <li key={u.brand}>
                  {u.brand} — {u.reason} (listed under checks not run)
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.doses.length === 0 ? (
          <p className="mt-4 text-sm text-[var(--muted)]">
            No illustrative clock times could be mapped from the written frequencies.
          </p>
        ) : (
          <div className="mt-4">
            <div className="relative h-16">
              <div className="absolute left-0 right-0 top-1/2 h-0.5 bg-[var(--card-border)]" />
              {[0, 6, 12, 18, 24].map((h) => (
                <span
                  key={h}
                  className="absolute top-0 -translate-x-1/2 text-[10px] text-[var(--muted)]"
                  style={{ left: `${(h / 24) * 100}%` }}
                >
                  {h === 0 ? '12a' : h < 12 ? `${h}a` : h === 12 ? '12p' : `${h - 12}p`}
                </span>
              ))}
              {data.doses.map((d, i) => (
                <div
                  key={`${d.brand}-${d.hour}-${i}`}
                  className={`absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2 flex-col items-center ${
                    reduce ? '' : 'transition-transform hover:scale-110'
                  }`}
                  style={{ left: `${(d.hour / 24) * 100}%` }}
                  title={`${d.brand} @ ${d.label}`}
                >
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-full border border-white/20 shadow"
                    style={{ background: timelineColor(d.colorIndex) }}
                  >
                    <Pill className="h-3.5 w-3.5 text-white" aria-hidden />
                  </span>
                  <span className="mt-1 max-w-[4.5rem] truncate text-[9px] text-[var(--muted)]">
                    {d.brand}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {data.series.length > 0 && (
          <div className="mt-6 space-y-4">
            <p className="text-xs font-semibold text-[var(--muted)]">
              Cumulative mg/day (engine totals) — dashed line = stored rule limit only
            </p>
            {data.series.map((s) => {
              const chartData = s.points.map((p) => ({
                hour: p.hour,
                cumulative: p.cumulativeMg,
                limit: s.limitMgDay,
              }))
              const stroke = s.crossesLimit ? '#f87171' : s.limitMgDay != null ? '#fbbf24' : '#14b8a6'
              return (
                <div key={s.ingredient}>
                  <p className="mb-1 text-xs font-medium">
                    {s.ingredient}{' '}
                    <span className="text-[var(--muted)]">
                      · {s.totalMgDay} {s.unit}/day
                      {s.limitMgDay != null ? ` · rule limit ${s.limitMgDay}` : ''}
                    </span>
                  </p>
                  <div className="h-36 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.2)" />
                        <XAxis dataKey="hour" tick={{ fontSize: 10 }} domain={[0, 24]} />
                        <YAxis tick={{ fontSize: 10 }} width={36} />
                        <Tooltip />
                        {s.limitMgDay != null && (
                          <ReferenceLine
                            y={s.limitMgDay}
                            stroke="#94a3b8"
                            strokeDasharray="4 4"
                            label={{ value: 'rule limit', fontSize: 10, fill: '#94a3b8' }}
                          />
                        )}
                        <Line
                          type="monotone"
                          dataKey="cumulative"
                          stroke={stroke}
                          strokeWidth={2}
                          dot={!reduce}
                          isAnimationActive={!reduce}
                          name={`${s.ingredient} cumulative`}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </section>
  )
}
