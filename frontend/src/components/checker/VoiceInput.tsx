import { useCallback, useEffect, useMemo, useState } from 'react'
import { Mic, MicOff } from 'lucide-react'
import { normalizeSpokenFrequencies } from '../../lib/spokenFrequency'

type Lang = 'en-IN' | 'hi-IN'

interface SpeechRecognitionLike extends EventTarget {
  lang: string
  continuous: boolean
  interimResults: boolean
  start: () => void
  stop: () => void
  onresult: ((ev: SpeechRecognitionEventLike) => void) | null
  onerror: ((ev: { error?: string }) => void) | null
  onend: (() => void) | null
}

interface SpeechRecognitionEventLike {
  results: ArrayLike<{ 0: { transcript: string }; isFinal?: boolean }>
}

function getSpeechRecognitionCtor():
  | (new () => SpeechRecognitionLike)
  | null {
  const w = window as Window & {
    SpeechRecognition?: new () => SpeechRecognitionLike
    webkitSpeechRecognition?: new () => SpeechRecognitionLike
  }
  return w.SpeechRecognition || w.webkitSpeechRecognition || null
}

interface Props {
  onTranscript: (text: string) => void
  disabled?: boolean
}

export function VoiceInput({ onTranscript, disabled }: Props) {
  const [lang, setLang] = useState<Lang>('en-IN')
  const [listening, setListening] = useState(false)
  const [online, setOnline] = useState(
    typeof navigator !== 'undefined' ? navigator.onLine : true,
  )
  const [error, setError] = useState<string | null>(null)
  const [lastHeard, setLastHeard] = useState<string | null>(null)

  const Ctor = useMemo(() => getSpeechRecognitionCtor(), [])
  const available = Boolean(Ctor) && online

  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => {
      setOnline(false)
      setListening(false)
    }
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])

  const stop = useCallback(() => {
    setListening(false)
  }, [])

  const start = useCallback(() => {
    if (!Ctor || disabled || !online) return
    setError(null)
    const rec = new Ctor()
    rec.lang = lang
    rec.continuous = false
    rec.interimResults = true
    let committed = ''
    rec.onresult = (ev) => {
      let finalText = ''
      let interim = ''
      for (let i = 0; i < ev.results.length; i++) {
        const row = ev.results[i] as { 0: { transcript: string }; isFinal?: boolean }
        if (row.isFinal) finalText += row[0].transcript
        else interim += row[0].transcript
      }
      const raw = (finalText || interim).trim()
      if (!raw) return
      const { matches } = normalizeSpokenFrequencies(raw)
      setLastHeard(
        matches.length
          ? `${raw} → ${matches.map((m) => m.label).join(', ')}`
          : raw,
      )
      if (finalText.trim()) committed = finalText.trim()
    }
    rec.onerror = (ev) => {
      setError(ev.error || 'Speech recognition error')
      setListening(false)
    }
    rec.onend = () => {
      setListening(false)
      // Append only after recognition ends — never auto-analyze
      if (committed) {
        const { text } = normalizeSpokenFrequencies(committed)
        onTranscript(text)
      }
    }
    try {
      rec.start()
      setListening(true)
    } catch {
      setError('Could not start microphone')
      setListening(false)
    }
  }, [Ctor, disabled, online, lang, onTranscript])

  if (!Ctor) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-xl border border-[var(--card-border)] px-2 py-1.5 text-[11px] text-[var(--muted)]"
        title="Voice input needs the Web Speech API in a supported browser (Chrome/Edge)."
      >
        <MicOff className="h-3.5 w-3.5" aria-hidden />
        Voice unavailable
      </span>
    )
  }

  if (!online) {
    return (
      <span
        className="inline-flex items-center gap-1 rounded-xl border border-[var(--card-border)] px-2 py-1.5 text-[11px] text-[var(--muted)]"
        title="Voice input needs a network connection for speech recognition."
      >
        <MicOff className="h-3.5 w-3.5" aria-hidden />
        Voice offline
      </span>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="voice-input">
      <div className="inline-flex rounded-xl border border-[var(--card-border)] bg-white p-0.5 text-[11px]">
        <button
          type="button"
          className={`rounded-lg px-2 py-1 ${lang === 'en-IN' ? 'bg-[#ECFDF5] text-[#123C38]' : 'text-[var(--muted)]'}`}
          onClick={() => setLang('en-IN')}
          aria-pressed={lang === 'en-IN'}
        >
          English
        </button>
        <button
          type="button"
          className={`rounded-lg px-2 py-1 ${lang === 'hi-IN' ? 'bg-[#ECFDF5] text-[#123C38]' : 'text-[var(--muted)]'}`}
          onClick={() => setLang('hi-IN')}
          aria-pressed={lang === 'hi-IN'}
        >
          हिंदी
        </button>
      </div>
      <button
        type="button"
        disabled={disabled || !available}
        onClick={() => (listening ? stop() : start())}
        className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-medium transition ${
          listening
            ? 'border-[#FECACA] bg-[#FEF2F2] text-[#B91C1C]'
            : 'border-[#DCE8E4] bg-white text-[#123C38] hover:bg-[#F1F7F5]'
        }`}
        title="Dictate into the prescription box. Confirm the live parse before Analyze — voice never auto-analyzes."
        aria-pressed={listening}
      >
        <Mic className={`h-3.5 w-3.5 ${listening ? 'animate-pulse' : ''}`} aria-hidden />
        {listening ? 'Listening…' : 'Voice'}
      </button>
      {lastHeard && (
        <p className="w-full text-[11px] text-[var(--muted)]">
          Heard (confirm below): {lastHeard}
        </p>
      )}
      {error && <p className="w-full text-[11px] text-[#B45309]">{error}</p>}
      <p className="w-full text-[10px] text-[var(--muted)]">
        Voice fills the box only — review the interpreted frequency, then click Analyze yourself.
      </p>
    </div>
  )
}
