import type { Alert, DailyIngredient } from '../../api/types'

/** Known adult draft limits mirrored from max_dose.json for gauge markers when alert lacks limit. */
const FALLBACK_LIMITS: Record<string, number> = {
  paracetamol: 4000,
  ibuprofen: 3200,
  diclofenac: 150,
  tramadol: 400,
  pantoprazole: 80,
  omeprazole: 80,
  atorvastatin: 80,
  amlodipine: 10,
  aspirin: 4000,
  metformin: 2550,
  cetirizine: 10,
  montelukast: 10,
}

interface Props {
  doses: DailyIngredient[]
  alerts: Alert[]
  patientAge?: number
  patientWeight?: number | null
}

export function DoseGauges({ doses, alerts, patientAge, patientWeight }: Props) {
  if (!doses?.length) return null

  return (
    <div className="print-report space-y-3">
      <h3 className="text-sm font-bold uppercase tracking-wider text-[var(--muted)]">
        Daily dose
      </h3>
      <ul className="space-y-3">
        {doses.map((d) => {
          if (d.unit !== 'mg') {
            return (
              <li key={d.ingredient} className="glass rounded-2xl p-4 text-sm">
                <span className="font-semibold capitalize">{d.ingredient}</span>
                <span className="ml-2 font-mono text-[var(--muted)]">
                  {d.total_mg_per_day} {d.unit}/day
                </span>
              </li>
            )
          }

          const alert = alerts.find(
            (a) =>
              (a.ingredients || []).includes(d.ingredient) &&
              (a.type === 'dose' || a.type === 'duplicate_dose') &&
              a.limit_mg_day != null,
          )
          let limit = alert?.limit_mg_day ?? FALLBACK_LIMITS[d.ingredient] ?? null

          // Pediatric formula display
          let formula: string | null = null
          if (
            patientAge != null &&
            patientAge < 18 &&
            patientWeight &&
            d.ingredient === 'paracetamol'
          ) {
            const ped = 60
            const lim = patientWeight * ped
            formula = `${patientWeight} kg × ${ped} mg/kg = ${lim} mg/day`
            if (alert?.limit_mg_day == null) limit = lim
          }
          const reasonFormula = alerts
            .map((a) => a.reason)
            .find((r) => r && /kg x|kg ×/i.test(r))
          if (reasonFormula) {
            const m = reasonFormula.match(/(\d+(?:\.\d+)?\s*kg\s*[x×]\s*\d+(?:\.\d+)?\s*mg\/kg\s*=\s*\d+(?:\.\d+)?\s*mg\/day)/i)
            if (m) formula = m[1]
          }

          const total = d.total_mg_per_day
          const pct = limit && limit > 0 ? Math.min(150, (total / limit) * 100) : null
          const over = limit != null && total > limit
          const near = pct != null && pct >= 80 && !over
          const barColor = over ? 'bg-rose-500' : near ? 'bg-amber-500' : 'bg-teal-500'

          return (
            <li key={d.ingredient} className="glass rounded-2xl p-4">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="font-semibold capitalize">{d.ingredient}</p>
                <p className="font-mono text-sm">
                  {total} mg/day
                  {limit != null && (
                    <span className="text-[var(--muted)]"> / {limit} mg limit</span>
                  )}
                </p>
              </div>
              {formula && (
                <p className="mt-1 font-mono text-xs text-sky-300">{formula}</p>
              )}
              {limit != null ? (
                <div className="mt-3">
                  <div className="relative h-3 overflow-hidden rounded-full bg-white/10">
                    <div
                      className={`h-full rounded-full ${barColor} transition-all`}
                      style={{ width: `${Math.min(100, pct || 0)}%` }}
                    />
                    <div
                      className="absolute top-0 h-full w-0.5 bg-white/80"
                      style={{ left: '100%' }}
                      title="Limit"
                    />
                  </div>
                  <p className="mt-1 text-xs text-[var(--muted)]">
                    {pct != null ? `${Math.round(pct)}% of limit` : ''}
                    {over ? ' · over limit' : near ? ' · near limit' : ''}
                  </p>
                </div>
              ) : (
                <p className="mt-2 text-xs text-[var(--muted)]">No draft limit in rules for this ingredient</p>
              )}
              <p className="mt-2 text-[11px] text-[var(--muted)]">
                {(d.contributions || []).map((c) => `${c.brand} (${c.mg_per_day})`).join(' · ')}
              </p>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
