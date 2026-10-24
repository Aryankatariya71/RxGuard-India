import { parsePreview } from '../../lib/parsePreview'
import { ErrorBoundary } from '../common/ErrorBoundary'
import { ScanPrescription } from './ScanPrescription'
import { VoiceInput } from './VoiceInput'

interface Props {
  value: string
  onChange: (v: string) => void
}

export function PrescriptionEditor({ value, onChange }: Props) {
  const lines = value.split('\n')
  const preview = parsePreview(value)

  const appendTranscript = (spoken: string) => {
    const chunk = spoken.trim()
    if (!chunk) return
    const next = value.trim() ? `${value.trim()}\n${chunk}` : chunk
    onChange(next)
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <label htmlFor="rx-input" className="text-sm font-semibold">
          Prescription
        </label>
        <ErrorBoundary label="Voice input">
          <VoiceInput onTranscript={appendTranscript} />
        </ErrorBoundary>
      </div>
      <ErrorBoundary label="Prescription scan">
        <ScanPrescription
          onUseText={(text) => {
            onChange(value.trim() ? `${value.trim()}\n${text}` : text)
          }}
        />
      </ErrorBoundary>
      <div className="glass overflow-hidden rounded-2xl">
        <div className="flex border-b border-[var(--card-border)] bg-black/20 px-3 py-2 text-[11px] text-[var(--muted)]">
          <span className="font-mono">rx · one medicine per line</span>
        </div>
        <div className="flex min-h-[200px]">
          <div
            className="select-none border-r border-[var(--card-border)] bg-black/10 px-2 py-3 text-right font-mono text-xs leading-6 text-[var(--muted)]"
            aria-hidden
          >
            {lines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          <textarea
            id="rx-input"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            spellCheck={false}
            className="min-h-[200px] w-full resize-y bg-transparent px-3 py-3 font-mono text-sm leading-6 text-[var(--fg)] outline-none placeholder:text-[var(--muted)]"
            placeholder={'Tab Dolo 650 1-0-1 x 5 days\nTab Crocin Advance BD'}
            aria-label="Prescription text, one medicine per line"
          />
        </div>
      </div>

      {preview.length > 0 && (
        <div className="space-y-2" aria-live="polite">
          <p className="text-xs font-medium uppercase tracking-wider text-[var(--muted)]">
            Live parse preview
          </p>
          <ul className="space-y-1.5">
            {preview.map((p) => (
              <li
                key={p.raw}
                className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--card-border)] bg-black/10 px-3 py-2 text-sm"
              >
                <span className="font-medium">{p.brandText}</span>
                {p.frequency && (
                  <span className="rounded-full bg-indigo-500/15 px-2 py-0.5 font-mono text-[11px] text-indigo-300">
                    {p.frequency}
                  </span>
                )}
                {p.timing && (
                  <span className="rounded-full bg-sky-500/15 px-2 py-0.5 font-mono text-[11px] text-sky-300">
                    {p.timing}
                  </span>
                )}
                {p.interpretedFrequency && (
                  <span
                    className="rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-100"
                    title="Confirm this interpreted frequency before analyzing"
                  >
                    Confirm: {p.interpretedFrequency}
                  </span>
                )}
                {p.duration && (
                  <span className="rounded-full bg-teal-500/15 px-2 py-0.5 font-mono text-[11px] text-teal-300">
                    {p.duration}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
