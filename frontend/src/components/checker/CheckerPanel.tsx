import { Loader2, Sparkles } from 'lucide-react'
import type { ExampleScenario } from '../../data/examples'
import type { PatientFormState } from '../../api/types'
import { ExampleCards } from './ExampleCards'
import { PatientPanel } from './PatientPanel'
import { PrescriptionEditor } from './PrescriptionEditor'

interface Props {
  rx: string
  patient: PatientFormState
  activeExample: string | null
  loading: boolean
  offline: boolean
  onRxChange: (v: string) => void
  onPatientChange: (p: PatientFormState) => void
  onExample: (ex: ExampleScenario) => void
  onAnalyze: () => void
}

export function CheckerPanel({
  rx,
  patient,
  activeExample,
  loading,
  offline,
  onRxChange,
  onPatientChange,
  onExample,
  onAnalyze,
}: Props) {
  return (
    <div className="glass relative space-y-6 rounded-[1.5rem] p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-bold tracking-tight">Prescription</h2>
        {offline && (
          <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-sky-300">
            offline demo data
          </span>
        )}
      </div>

      <PrescriptionEditor value={rx} onChange={onRxChange} />
      <PatientPanel patient={patient} onChange={onPatientChange} />

      <button
        type="button"
        onClick={onAnalyze}
        disabled={loading || !rx.trim()}
        className="btn-glow flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-teal-500 via-teal-400 to-indigo-500 px-5 py-3.5 text-sm font-bold text-white transition disabled:cursor-not-allowed disabled:opacity-50"
        aria-busy={loading}
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Analyzing…
          </>
        ) : (
          <>
            <Sparkles className="h-4 w-4" aria-hidden />
            Analyze prescription
          </>
        )}
      </button>

      <ExampleCards activeId={activeExample} onSelect={onExample} />
    </div>
  )
}
