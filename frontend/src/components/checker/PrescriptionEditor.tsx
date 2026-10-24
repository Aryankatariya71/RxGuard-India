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
        <label htmlFor="rx-input" className="text-sm font-semibold text-[var(--heading)]">
          Prescription text
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
      <div className="overflow-hidden rounded-2xl border border-[var(--card-border)] bg-[var(--input-bg)]">
        <div className="flex items-center justify-between gap-2 border-b border-[var(--card-border)] bg-white px-3 py-2 text-[11px] text-[var(--muted)]">
          <span className="font-mono">rx · one medicine per line</span>
          <span className="tabular-nums">
            {lines.filter((l) => l.trim()).length} line{lines.filter((l) => l.trim()).length === 1 ? '' : 's'} ·{' '}
            {value.length} chars
          </span>
        </div>
        <div className="flex min-h-[200px]">
          <div
            className="select-none border-r border-[var(--card-border)] bg-white/70 px-2 py-3 text-right font-mono text-xs leading-6 text-[var(--muted)]"
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
            className="min-h-[200px] w-full resize-y bg-transparent px-3 py-3 font-mono text-sm leading-6 text-[var(--heading)] outline-none placeholder:text-[var(--muted)] focus:ring-0"
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
                className="flex flex-wrap items-center gap-2 rounded-xl border border-[var(--card-border)] bg-white px-3 py-2 text-sm"
              >
                <span className="font-medium text-[var(--heading)]">{p.brandText}</span>
                {p.frequency && (
                  <span className="rounded-full bg-[#EFF6FF] px-2 py-0.5 font-mono text-[11px] text-[#1D4ED8]">
                    {p.frequency}
                  </span>
                )}
                {p.timing && (
                  <span className="rounded-full bg-[#ECFDF5] px-2 py-0.5 font-mono text-[11px] text-[#087F6E]">
                    {p.timing}
                  </span>
                )}
                {p.interpretedFrequency && (
                  <span
                    className="rounded-full border border-[#FED7AA] bg-[#FFF7ED] px-2 py-0.5 text-[11px] text-[#B45309]"
                    title="Confirm this interpreted frequency before analyzing"
                  >
                    Confirm: {p.interpretedFrequency}
                  </span>
                )}
                {p.duration && (
                  <span className="rounded-full bg-[#F0FDF4] px-2 py-0.5 font-mono text-[11px] text-[#15803D]">
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
