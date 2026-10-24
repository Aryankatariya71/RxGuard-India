import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion, useReducedMotion } from 'framer-motion'
import { analyzePrescription, checkHealth } from './api/client'
import type { AnalyzeResponse, PatientFormState } from './api/types'
import { CheckerPanel } from './components/checker/CheckerPanel'
import { Hero } from './components/hero/Hero'
import { AppLayout } from './components/layout/AppLayout'
import { ReportPanel } from './components/report/ReportPanel'
import { AlertFatigue } from './components/sections/AlertFatigue'
import { Capabilities } from './components/sections/Capabilities'
import { HowItWorks } from './components/sections/HowItWorks'
import { Trust } from './components/sections/Trust'
import { WhyRxGuard } from './components/sections/WhyRxGuard'
import { EXAMPLES, type ExampleScenario } from './data/examples'
import { defaultActiveKeys, filterPrescriptionText } from './lib/whatIf'

export default function App() {
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
        await new Promise((r) => setTimeout(r, reduce ? 0 : 350))
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
    <AppLayout title="Prescription checker" subtitle="Every brand. Every ingredient. Every risk.">
      <Hero />
      <HowItWorks />
      <Capabilities />

      <section id="checker" className="border-t border-[#DCE8E4] bg-[#F1F7F5] py-12 sm:py-16">
        <div className="rx-container">
          <div className="mb-8 flex flex-wrap items-end justify-between gap-3">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
                Prescription checker
              </h2>
              <p className="mt-2 text-[#64748B]">
                Paste a prescription or load a scenario. Every alert cites a rule. This is decision
                support — not a medical clearance.
              </p>
            </div>
            {apiUp === false && (
              <span className="rounded-full border border-[#BFDBFE] bg-[#EFF6FF] px-3 py-1 text-xs text-[#1D4ED8]">
                API offline — using bundled demo data
              </span>
            )}
          </div>

          {whatIfActive && (
            <motion.div
              initial={reduce ? false : { opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-4 flex flex-wrap items-center gap-2 rounded-2xl border border-[#BFDBFE] bg-[#EFF6FF] px-4 py-2 text-sm text-[#1D4ED8]"
            >
              <span className="rounded-full bg-white px-2.5 py-0.5 text-xs font-semibold">
                What-if mode: {whatIf.excludedCount} medicine(s) excluded. This is a simulation, not
                advice.
              </span>
              <button
                type="button"
                onClick={resetWhatIf}
                className="btn-secondary px-3 py-1 text-xs"
              >
                Reset
              </button>
            </motion.div>
          )}

          <div className="grid gap-6 xl:grid-cols-2">
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
        </div>
      </section>

      <WhyRxGuard />
      <AlertFatigue />
      <Trust />
    </AppLayout>
  )
}
