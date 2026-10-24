import { Loader2, ShieldCheck } from 'lucide-react'
import type { ExampleScenario } from '../../data/examples'
import type { PatientFormState } from '../../api/types'
import { ExampleCards } from './ExampleCards'
import { PatientPanel } from './PatientPanel'
import { PrescriptionEditor } from './PrescriptionEditor'
import { PublicMedicineSearch } from './PublicMedicineSearch'

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
    <div className="rx-card relative space-y-6 p-5 sm:p-6">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold tracking-tight text-[#123C38]">Prescription</h2>
        {offline && (
          <span className="rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[#1D4ED8]">
            offline demo data
          </span>
        )}
      </div>

      <PrescriptionEditor value={rx} onChange={onRxChange} />
      <PublicMedicineSearch
        onInsertBrand={(brand) => {
          const line = `Tab ${brand}`
          onRxChange(rx.trim() ? `${rx.trim()}\n${line}` : line)
        }}
      />
      <PatientPanel patient={patient} onChange={onPatientChange} />

      <button
        type="button"
        onClick={onAnalyze}
        disabled={loading || !rx.trim()}
        className="btn-primary flex w-full items-center justify-center gap-2 px-5 py-3.5 text-sm disabled:cursor-not-allowed disabled:opacity-50"
        aria-busy={loading}
      >
        {loading ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Analyzing…
          </>
        ) : (
          <>
            <ShieldCheck className="h-4 w-4" strokeWidth={2} aria-hidden />
            Analyze prescription
          </>
        )}
      </button>

      <ExampleCards activeId={activeExample} onSelect={onExample} />
    </div>
  )
}
