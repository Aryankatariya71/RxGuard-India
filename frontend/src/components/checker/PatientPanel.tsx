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
      <h3 className="text-sm font-semibold">Patient</h3>

      <div className="glass flex items-start gap-3 rounded-2xl p-4">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500/30 to-indigo-500/30">
          <UserRound className="h-5 w-5 text-teal-300" aria-hidden />
        </div>
        <div>
          <p className="text-sm font-medium leading-snug">{patientSummary(patient)}</p>
          <p className="mt-1 text-xs text-[var(--muted)]">Updates live as you edit</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="age" className="text-xs text-[var(--muted)]">
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
              className="w-full accent-teal-500"
              aria-valuetext={`${patient.age_years} years`}
            />
            <input
              type="number"
              min={0}
              max={120}
              value={patient.age_years}
              onChange={(e) => set('age_years', Number(e.target.value) || 0)}
              className="glass w-16 rounded-xl px-2 py-1.5 font-mono text-sm"
              aria-label="Age years number"
            />
          </div>
        </div>
        <div>
          <label htmlFor="weight" className="text-xs text-[var(--muted)]">
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
            className="glass mt-1 w-full rounded-xl px-3 py-2 font-mono text-sm"
          />
        </div>
      </div>

      <fieldset>
        <legend className="text-xs text-[var(--muted)]">Sex</legend>
        <div className="mt-1 grid grid-cols-3 gap-1 rounded-xl border border-[var(--card-border)] p-1">
          {(['', 'M', 'F'] as const).map((s) => (
            <button
              key={s || 'na'}
              type="button"
              onClick={() => set('sex', s)}
              className={`rounded-lg py-2 text-sm transition ${
                patient.sex === s
                  ? 'bg-teal-500/20 font-semibold text-teal-200'
                  : 'text-[var(--muted)] hover:bg-white/5'
              }`}
              aria-pressed={patient.sex === s}
            >
              {s === '' ? '—' : s === 'M' ? 'Male' : 'Female'}
            </button>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-xs text-[var(--muted)]">Kidney function</legend>
        <div className="mt-1 grid grid-cols-2 gap-1 rounded-xl border border-[var(--card-border)] p-1 sm:grid-cols-4">
          {KIDNEY.map((k) => (
            <button
              key={k.id}
              type="button"
              onClick={() => set('kidney', k.id)}
              className={`rounded-lg px-2 py-2 text-xs transition sm:text-sm ${
                patient.kidney === k.id
                  ? 'bg-indigo-500/20 font-semibold text-indigo-200'
                  : 'text-[var(--muted)] hover:bg-white/5'
              }`}
              aria-pressed={patient.kidney === k.id}
            >
              {k.label}
            </button>
          ))}
        </div>
      </fieldset>

      <label className="flex cursor-pointer items-center gap-3 text-sm">
        <input
          type="checkbox"
          checked={patient.pregnant}
          onChange={(e) => set('pregnant', e.target.checked)}
          className="h-4 w-4 accent-teal-500"
        />
        Pregnant
      </label>
    </div>
  )
}
