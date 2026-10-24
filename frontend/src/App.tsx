import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { analyzePrescription, checkHealth } from './api/client'
import type { AnalyzeResponse, PatientFormState } from './api/types'
import { CheckerPanel } from './components/checker/CheckerPanel'
import { Hero } from './components/hero/Hero'
import { Footer } from './components/layout/Footer'
import { Navbar } from './components/layout/Navbar'
import { ReportPanel } from './components/report/ReportPanel'
import { AlertFatigue } from './components/sections/AlertFatigue'
import { HowItWorks } from './components/sections/HowItWorks'
import { Trust } from './components/sections/Trust'
import { EXAMPLES, type ExampleScenario } from './data/examples'
import { useTheme } from './hooks/useTheme'
import { defaultActiveKeys, filterPrescriptionText } from './lib/whatIf'

export default function App() {
  const { theme, toggle } = useTheme()
  const reduce = useReducedMotion()
  const [rx, setRx] = useState(EXAMPLES[0].rx)
  const [patient, setPatient] = useState<PatientFormState>(EXAMPLES[0].patient)
  const [activeExample, setActiveExample] = useState<string | null>(EXAMPLES[0].id)
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<AnalyzeResponse | null>(null)
  const [offline, setOffline] = useState(false)
  const [apiUp, setApiUp] = useState<boolean | null>(null)
  const [activeKeys, setActiveKeys] = useState<Set<string>>(() =>
    defaultActiveKeys(EXAMPLES[0].rx),
  )
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    checkHealth().then(setApiUp)
  }, [])

  const whatIf = useMemo(() => filterPrescriptionText(rx, activeKeys), [rx, activeKeys])
  const whatIfActive = whatIf.excludedCount > 0

  const runAnalyze = useCallback(
    async (text: string, p: PatientFormState, exampleId: string | null) => {
      setLoading(true)
      try {
        await new Promise((r) => setTimeout(r, reduce ? 0 : 450))
        const { data, offline: isOff } = await analyzePrescription(text, p, exampleId)
        setReport(data)
        setOffline(isOff)
        setApiUp(!isOff)
      } finally {
        setLoading(false)
      }
    },
    [reduce],
  )

  const scheduleWhatIfAnalyze = useCallback(
    (keys: Set<string>) => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
      debounceRef.current = setTimeout(() => {
        const filtered = filterPrescriptionText(rx, keys)
        if (!filtered.text.trim()) {
          setReport({
            empty: true,
            items: [],
            daily_doses: { by_ingredient: [], strength_unclear: [] },
            alerts: [],
            counts: { critical: 0, review: 0, info: 0 },
            verdict: 'clear',
          })
          return
        }
        void runAnalyze(filtered.text, patient, null)
      }, 400)
    },
    [rx, patient, runAnalyze],
  )

  const onExample = (ex: ExampleScenario) => {
    setActiveExample(ex.id)
    setRx(ex.rx)
    setPatient(ex.patient)
    setActiveKeys(defaultActiveKeys(ex.rx))
    void runAnalyze(ex.rx, ex.patient, ex.id)
  }

  const onAnalyze = () => {
    const filtered = filterPrescriptionText(rx, activeKeys)
    void runAnalyze(filtered.text || rx, patient, activeExample)
  }

  const onPickCandidate = (line: string, brandName: string) => {
    const lines = rx.split('\n')
    const next = lines
      .map((l) => {
        if (!line) return l
        if (l.trim() === line.trim() || l.includes(line.slice(0, 12))) {
          const form = l.match(/^(Tab|Cap|Syp|Susp|Inj)\s+/i)?.[0] || 'Tab '
          return `${form}${brandName} OD`
        }
        return l
      })
      .join('\n')
    setRx(next)
    setActiveKeys(defaultActiveKeys(next))
    setActiveExample(null)
    void runAnalyze(next, patient, null)
  }

  const onToggleActive = (key: string, next: boolean) => {
    setActiveKeys((prev) => {
      const copy = new Set(prev)
      if (next) copy.add(key)
      else copy.delete(key)
      scheduleWhatIfAnalyze(copy)
      return copy
    })
  }

  const resetWhatIf = () => {
    const keys = defaultActiveKeys(rx)
    setActiveKeys(keys)
    void runAnalyze(rx, patient, activeExample)
  }

  return (
    <div className="min-h-screen">
      <Navbar theme={theme} onToggleTheme={toggle} />
      <main>
        <Hero />

        <section id="checker" className="mx-auto max-w-7xl px-4 py-16 sm:px-6">
          <div className="mb-8 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-3xl font-extrabold tracking-tight">Try the checker</h2>
              <p className="mt-2 text-[var(--muted)]">
                Paste a prescription or load a scenario. Every alert cites a rule.
              </p>
            </div>
            {apiUp === false && (
              <span className="rounded-full border border-sky-500/30 bg-sky-500/10 px-3 py-1 text-xs text-sky-300">
                API offline — using bundled demo data
              </span>
            )}
          </div>

          {whatIfActive && (
            <motion.div
              initial={reduce ? false : { opacity: 0, y: -6 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 flex flex-wrap items-center gap-2 rounded-2xl border border-violet-500/30 bg-violet-500/10 px-4 py-2 text-sm text-violet-100"
            >
              <span className="rounded-full bg-violet-500/30 px-2.5 py-0.5 text-xs font-semibold">
                What-if mode: {whatIf.excludedCount} medicine(s) excluded. This is a
                simulation, not advice.
              </span>
              <button
                type="button"
                onClick={resetWhatIf}
                className="rounded-xl border border-violet-400/40 px-3 py-1 text-xs font-semibold hover:bg-violet-500/20"
              >
                Reset
              </button>
            </motion.div>
          )}

          <div className="grid gap-6 lg:grid-cols-2">
            <CheckerPanel
              rx={rx}
              patient={patient}
              activeExample={activeExample}
              loading={loading}
              offline={offline}
              onRxChange={(v) => {
                setRx(v)
                setActiveKeys(defaultActiveKeys(v))
                setActiveExample(null)
              }}
              onPatientChange={setPatient}
              onExample={onExample}
              onAnalyze={onAnalyze}
            />
            <ReportPanel
              report={report}
              loading={loading}
              patient={patient}
              offline={offline}
              prescriptionText={rx}
              activeKeys={activeKeys}
              onToggleActive={onToggleActive}
              onPickCandidate={onPickCandidate}
            />
          </div>
        </section>

        <HowItWorks />
        <AlertFatigue />
        <Trust />
      </main>
      <Footer />
    </div>
  )
}
