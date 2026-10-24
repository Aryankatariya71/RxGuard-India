import type { PatientFormState } from '../../api/types'
import { patientSummary } from '../../lib/parsePreview'
import { UserRound } from 'lucide-react'

interface Props {
  patient: PatientFormState
  onChange: (p: PatientFormState) => void
}

const KIDNEY = [
  { id: 'normal' as const, label: 'Normal' },
  { id: 'mild_moderate' as const, label: 'Mild–moderate' },
  { id: 'severe' as const, label: 'Severe' },
  { id: 'unknown' as const, label: 'Unknown' },
]

export function PatientPanel({ patient, onChange }: Props) {
  const set = <K extends keyof PatientFormState>(key: K, value: PatientFormState[K]) =>
    onChange({ ...patient, [key]: value })

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-[var(--heading)]">Patient</h3>

      <div className="flex items-start gap-3 rounded-2xl border border-[var(--card-border)] bg-[var(--input-bg)] p-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#ECFDF5] text-[#087F6E]">
          <UserRound className="h-5 w-5" aria-hidden />
        </div>
        <div>
          <p className="text-sm font-medium leading-snug text-[var(--heading)]">
            {patientSummary(patient)}
          </p>
          <p className="mt-1 text-xs text-[var(--muted)]">Updates live as you edit</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="age" className="text-xs font-medium text-[var(--muted)]">
            Age (years)
          </label>
          <div className="mt-1 flex items-center gap-2">
            <input
              id="age"
              type="range"
              min={0}
              max={100}
              value={patient.age_years}
              onChange={(e) => set('age_years', Number(e.target.value))}
              className="w-full accent-[#0D9B78]"
              aria-valuetext={`${patient.age_years} years`}
            />
            <input
              type="number"
              min={0}
              max={120}
              value={patient.age_years}
              onChange={(e) => set('age_years', Number(e.target.value) || 0)}
              className="rx-input w-16 px-2 py-1.5 font-mono text-sm"
              aria-label="Age years number"
            />
          </div>
        </div>
        <div>
          <label htmlFor="weight" className="text-xs font-medium text-[var(--muted)]">
            Weight (kg)
          </label>
          <input
            id="weight"
            type="number"
            min={0}
            max={300}
            step={0.5}
            value={patient.weight_kg ?? ''}
            onChange={(e) =>
              set('weight_kg', e.target.value === '' ? null : Number(e.target.value))
            }
            className="rx-input mt-1 w-full px-3 py-2 font-mono text-sm"
          />
        </div>
      </div>

      <fieldset>
        <legend className="text-xs font-medium text-[var(--muted)]">Sex</legend>
        <div className="mt-1 grid grid-cols-3 gap-1 rounded-xl border border-[var(--card-border)] bg-white p-1">
          {(['', 'M', 'F'] as const).map((s) => (
            <button
              key={s || 'na'}
              type="button"
              onClick={() => set('sex', s)}
              className={`rounded-lg py-2 text-sm transition ${
                patient.sex === s
                  ? 'bg-[#ECFDF5] font-semibold text-[#123C38]'
                  : 'text-[var(--muted)] hover:bg-[var(--input-bg)]'
              }`}
              aria-pressed={patient.sex === s}
            >
              {s === '' ? '—' : s === 'M' ? 'Male' : 'Female'}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-xs font-medium text-[var(--muted)]">Kidney function</legend>
        <div className="mt-1 grid grid-cols-2 gap-1 rounded-xl border border-[var(--card-border)] bg-white p-1 sm:grid-cols-4">
          {KIDNEY.map((k) => (
            <button
              key={k.id}
              type="button"
              onClick={() => set('kidney', k.id)}
              className={`rounded-lg px-2 py-2 text-xs transition sm:text-sm ${
                patient.kidney === k.id
                  ? 'bg-[#ECFDF5] font-semibold text-[#123C38]'
                  : 'text-[var(--muted)] hover:bg-[var(--input-bg)]'
              }`}
              aria-pressed={patient.kidney === k.id}
            >
              {k.label}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="flex cursor-pointer items-center gap-3 text-sm text-[var(--body)]">
        <input
          type="checkbox"
          checked={patient.pregnant}
          onChange={(e) => set('pregnant', e.target.checked)}
          className="h-4 w-4 accent-[#0D9B78]"
        />
        Pregnant
      </label>
    </div>
  )
}
