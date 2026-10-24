import { useState } from 'react'
import { Copy, Printer } from 'lucide-react'
import type { Alert, AnalyzeResponse, PatientFormState } from '../../api/types'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { AlertList } from './AlertList'
import { DoseGauges } from './DoseGauges'
import { DoseTimeline } from './DoseTimeline'
import { IngredientFlow } from './IngredientFlow'
import { MedicinesFound } from './MedicinesFound'
import { PipelineAnimation } from './PipelineAnimation'
import { VerdictCard } from './VerdictCard'
import { WhyDrawer } from './WhyDrawer'

interface Props {
  report: AnalyzeResponse | null
  loading: boolean
  patient: PatientFormState
  offline: boolean
  onPickCandidate: (line: string, brandName: string) => void
}

export function ReportPanel({
  report,
  loading,
  patient,
  offline,
  onPickCandidate,
}: Props) {
  const [why, setWhy] = useState<Alert | null>(null)

  const copyReport = async () => {
    if (!report) return
    const lines = [
      `RxGuard India — Safety report`,
      `Verdict: ${report.verdict}`,
      `Critical: ${report.counts.critical} · Review: ${report.counts.review} · Info: ${report.counts.info}`,
      '',
      ...report.alerts.map(
        (a) => `[${a.tier}] ${a.title}\n${a.reason}\nAction: ${a.suggested_action}\nRule: ${a.source_rule_id}`,
      ),
    ]
    await navigator.clipboard.writeText(lines.join('\n\n'))
  }

  return (
    <div className="glass space-y-6 rounded-[1.5rem] p-5 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold tracking-tight">Safety report</h2>
        <div className="no-print flex items-center gap-2">
          {offline && (
            <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-sky-300">
              offline demo data
            </span>
          )}
          <button
            type="button"
            onClick={copyReport}
            disabled={!report}
            className="glass glass-hover flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium disabled:opacity-40"
          >
            <Copy className="h-3.5 w-3.5" aria-hidden />
            Copy report
          </button>
          <button
            type="button"
            onClick={() => window.print()}
            disabled={!report}
            className="glass glass-hover flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-medium disabled:opacity-40"
          >
            <Printer className="h-3.5 w-3.5" aria-hidden />
            Print / PDF
          </button>
        </div>
      </div>

      <PipelineAnimation active={loading} />

      {!report && !loading && (
        <div className="rounded-2xl border border-dashed border-[var(--card-border)] px-6 py-16 text-center text-[var(--muted)]">
          <p className="text-sm">Run Analyze or pick an example to see the safety report.</p>
        </div>
      )}

      {report && (
        <>
          <VerdictCard report={report} />
          <AlertList alerts={report.alerts || []} onWhy={setWhy} />
          <ErrorBoundary label="Your day timeline">
            <DoseTimeline report={report} />
          </ErrorBoundary>
          <MedicinesFound
            items={report.items || []}
            onPickCandidate={onPickCandidate}
          />
          <IngredientFlow
            items={report.items || []}
            doses={report.daily_doses?.by_ingredient || []}
          />
          <DoseGauges
            doses={report.daily_doses?.by_ingredient || []}
            alerts={report.alerts || []}
            patientAge={patient.age_years}
            patientWeight={patient.weight_kg}
          />
        </>
      )}

      <WhyDrawer
        alert={why}
        doses={report?.daily_doses?.by_ingredient || []}
        onClose={() => setWhy(null)}
      />
    </div>
  )
}
