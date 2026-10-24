import { useMemo, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ErrorBoundary } from '../components/common/ErrorBoundary'
import { AppLayout } from '../components/layout/AppLayout'

const N_OPTIONS = [100, 500, 1000, 2000] as const

interface HistBin {
  alerts: number
  count: number
}

interface StressResult {
  ok: boolean
  seed: number
  n: number
  elapsed_ms: number
  prescriptions_per_second: number
  had_duplicates: number
  had_interactions: number
  had_dose_rule_matches: number
  had_unresolved_items: number
  had_check_not_run: number
  alerts_per_prescription: {
    naive: HistBin[]
    rxguard_merged: HistBin[]
    naive_mean: number
    merged_mean: number
  }
  caption: string
  error?: string
}

function AnimatedNumber({ value, reduce }: { value: number; reduce: boolean | null }) {
  return (
    <motion.span
      key={value}
      initial={reduce ? false : { opacity: 0.4, y: 4 }}
      animate={{ opacity: 1, y: 0 }}
      className="tabular-nums"
    >
      {typeof value === 'number' && !Number.isInteger(value) ? value.toFixed(1) : value}
    </motion.span>
  )
}

export function StressTestPage() {
  const reduce = useReducedMotion()
  const [n, setN] = useState<(typeof N_OPTIONS)[number]>(500)
  const [seed, setSeed] = useState<string>('')
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState<StressResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const chartData = useMemo(() => {
    if (!result?.ok) return []
    const map = new Map<number, { alerts: number; naive: number; rxguard: number }>()
    for (const b of result.alerts_per_prescription.naive) {
      map.set(b.alerts, { alerts: b.alerts, naive: b.count, rxguard: 0 })
    }
    for (const b of result.alerts_per_prescription.rxguard_merged) {
      const cur = map.get(b.alerts) || { alerts: b.alerts, naive: 0, rxguard: 0 }
      cur.rxguard = b.count
      map.set(b.alerts, cur)
    }
    return [...map.values()].sort((a, b) => a.alerts - b.alerts)
  }, [result])

  const run = async () => {
    setRunning(true)
    setError(null)
    try {
      const body: { n: number; seed?: number } = { n }
      const parsed = seed.trim() === '' ? null : Number(seed)
      if (parsed != null && !Number.isNaN(parsed)) body.seed = Math.trunc(parsed)
      const res = await fetch('/api/stress-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`API ${res.status}`)
      const data = (await res.json()) as StressResult
      if (!data.ok) throw new Error(data.error || 'Stress test failed')
      setResult(data)
      setSeed(String(data.seed))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <AppLayout title="Stress test" subtitle="Synthetic performance demonstration">
    <div className="rx-container max-w-5xl py-10" data-testid="stress-test-page">
        <ErrorBoundary label="Stress test dashboard">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#123C38]">Stress test</h1>
          <p className="mt-2 text-[#64748B]">
            Run synthetic prescriptions through the rules engines — performance and alert-load
            demo only.
          </p>

          <div className="rx-card mt-6 space-y-4 p-5">
            <fieldset>
              <legend className="text-sm font-semibold">Run synthetic prescriptions</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {N_OPTIONS.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setN(opt)}
                    className={`rounded-xl border px-3 py-1.5 text-sm ${
                      n === opt
                        ? 'border-[#0D9B78] bg-[#ECFDF5] text-[#123C38]'
                        : 'border-[var(--card-border)] bg-[var(--input-bg)]'
                    }`}
                    aria-pressed={n === opt}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </fieldset>
            <label className="block text-sm">
              Seed (optional, for reproducibility)
              <input
                value={seed}
                onChange={(e) => setSeed(e.target.value)}
                className="rx-input mt-1 w-full max-w-xs px-3 py-2 font-mono text-sm"
                placeholder="auto"
              />
            </label>
            <button
              type="button"
              onClick={() => void run()}
              disabled={running}
              className="btn-primary px-5 py-3 text-sm disabled:opacity-50"
            >
              {running ? 'Running…' : 'Run'}
            </button>
            {running && (
              <p className="text-sm text-[#B45309]" role="status">
                Progress: generating and evaluating {n} synthetic prescriptions…
              </p>
            )}
            {error && <p className="text-sm text-[#B91C1C]">{error}</p>}
          </div>

          {result?.ok && (
            <div className="mt-8 space-y-6">
              <p className="text-xs text-[var(--muted)]">{result.caption}</p>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <Stat label="Total" value={result.n} reduce={reduce} />
                <Stat label="Elapsed ms" value={result.elapsed_ms} reduce={reduce} />
                <Stat
                  label="Rx / second"
                  value={result.prescriptions_per_second}
                  reduce={reduce}
                />
                <Stat label="Seed" value={result.seed} reduce={reduce} />
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                <Stat label="Had duplicates" value={result.had_duplicates} reduce={reduce} />
                <Stat label="Had interactions" value={result.had_interactions} reduce={reduce} />
                <Stat
                  label="Had dose-rule matches"
                  value={result.had_dose_rule_matches}
                  reduce={reduce}
                />
                <Stat
                  label="Had unresolved items"
                  value={result.had_unresolved_items}
                  reduce={reduce}
                />
                <Stat
                  label="CHECK_NOT_RUN / incomplete"
                  value={result.had_check_not_run}
                  reduce={reduce}
                />
                <Stat
                  label="Mean alerts (naive → merged)"
                  value={result.alerts_per_prescription.merged_mean}
                  reduce={reduce}
                  hint={`naive ${result.alerts_per_prescription.naive_mean}`}
                />
              </div>

              <section className="rx-card p-4">
                <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
                  Alerts per prescription: naive vs RxGuard
                </h2>
                <div className="mt-4 h-72 w-full" role="img" aria-label="Histogram of alert counts">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                      <XAxis dataKey="alerts" label={{ value: 'Alerts', position: 'insideBottom', offset: -2 }} />
                      <YAxis allowDecimals={false} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="naive" name="Naive (pre-merge)" fill="#f59e0b" />
                      <Bar dataKey="rxguard" name="RxGuard (merged)" fill="#14b8a6" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </section>
            </div>
          )}
        </ErrorBoundary>
    </div>
    </AppLayout>
  )
}

function Stat({
  label,
  value,
  reduce,
  hint,
}: {
  label: string
  value: number
  reduce: boolean | null
  hint?: string
}) {
  return (
    <div className="rx-card p-4">
      <p className="text-2xl font-bold text-[var(--heading)]">
        <AnimatedNumber value={value} reduce={reduce} />
      </p>
      <p className="mt-1 text-xs text-[var(--muted)]">{label}</p>
      {hint && <p className="text-[10px] text-[var(--muted)]">{hint}</p>}
    </div>
  )
}

export default StressTestPage
