import { useRef, useState } from 'react'
import { Camera, FileImage, Loader2 } from 'lucide-react'
import { recognizeImageLocal } from '../../lib/ocrLocal'
import { normalizeSpokenFrequencies } from '../../lib/spokenFrequency'

const SAMPLE_URL = '/samples/sample_prescription.png'

interface Props {
  onUseText: (text: string) => void
}

export function ScanPrescription({ onUseText }: Props) {
  const fileRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const [extracted, setExtracted] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)

  const runOcr = async (source: File | string, preview?: string) => {
    setBusy(true)
    setError(null)
    setPreviewUrl(preview || (typeof source === 'string' ? source : null))
    try {
      const raw = await recognizeImageLocal(source)
      const { text } = normalizeSpokenFrequencies(raw)
      setExtracted(text)
      setOpen(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OCR failed locally')
    } finally {
      setBusy(false)
    }
  }

  const onFile = async (file: File | null) => {
    if (!file) return
    // Never send images anywhere — stay in the browser
    const url = URL.createObjectURL(file)
    await runOcr(file, url)
  }

  const useText = () => {
    const t = extracted.trim()
    if (!t) return
    onUseText(t)
    setOpen(false)
  }

  return (
    <div className="space-y-3" data-testid="scan-prescription">
      <div className="flex flex-wrap items-center gap-2">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={busy}
          className="btn-secondary inline-flex items-center gap-1.5 px-3 py-1.5 text-xs disabled:opacity-50"
        >
          {busy ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" aria-hidden />
          ) : (
            <Camera className="h-3.5 w-3.5" aria-hidden />
          )}
          Scan prescription
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => runOcr(SAMPLE_URL, SAMPLE_URL)}
          className="inline-flex items-center gap-1.5 rounded-xl border border-[#A7F3D0] bg-[#ECFDF5] px-3 py-1.5 text-xs font-medium text-[#123C38] hover:bg-[#D1FAE5] disabled:opacity-50"
        >
          <FileImage className="h-3.5 w-3.5" aria-hidden />
          Try printed sample
        </button>
        <input
          ref={fileRef}
          type="file"
          accept="image/*"
          capture="environment"
          className="hidden"
          onChange={(e) => onFile(e.target.files?.[0] || null)}
        />
      </div>
      <p className="text-[10px] text-[var(--muted)]">
        OCR runs entirely in your browser. Images are never uploaded.
      </p>
      {error && <p className="text-xs text-[#B45309]">{error}</p>}

      {(open || busy) && (
        <div className="space-y-3 rounded-2xl border border-[#FED7AA] bg-[#FFF7ED] p-4">
          <p className="text-xs font-semibold text-[#B45309]">
            Check carefully: handwriting is often misread
          </p>
          {previewUrl && (
            <img
              src={previewUrl}
              alt="Prescription preview (stays on device)"
              className="max-h-40 rounded-lg border border-[var(--card-border)] object-contain"
            />
          )}
          {busy ? (
            <p className="flex items-center gap-2 text-sm text-[var(--muted)]">
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
              Reading text locally…
            </p>
          ) : (
            <>
              <label htmlFor="ocr-text" className="text-xs font-medium text-[var(--muted)]">
                Extracted text (editable)
              </label>
              <textarea
                id="ocr-text"
                value={extracted}
                onChange={(e) => setExtracted(e.target.value)}
                rows={6}
                className="rx-input w-full px-3 py-2 font-mono text-sm"
              />
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={useText}
                  disabled={!extracted.trim()}
                  className="btn-primary px-4 py-2 text-xs disabled:opacity-40"
                >
                  Use this text
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setOpen(false)
                    setExtracted('')
                  }}
                  className="btn-secondary px-4 py-2 text-xs"
                >
                  Discard
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
