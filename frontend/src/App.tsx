import { useCallback, useEffect, useState } from 'react'
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

export default function App() {
  const { theme, toggle } = useTheme()
  const [rx, setRx] = useState(EXAMPLES[0].rx)
  const [patient, setPatient] = useState<PatientFormState>(EXAMPLES[0].patient)
  const [activeExample, setActiveExample] = useState<string | null>(EXAMPLES[0].id)
  const [loading, setLoading] = useState(false)
  const [report, setReport] = useState<AnalyzeResponse | null>(null)
  const [offline, setOffline] = useState(false)
  const [apiUp, setApiUp] = useState<boolean | null>(null)

  useEffect(() => {
    checkHealth().then(setApiUp)
  }, [])

  const runAnalyze = useCallback(
    async (text: string, p: PatientFormState, exampleId: string | null) => {
      setLoading(true)
      setReport(null)
      try {
        // Brief pipeline animation window
        await new Promise((r) => setTimeout(r, 900))
        const { data, offline: isOff } = await analyzePrescription(text, p, exampleId)
        setReport(data)
        setOffline(isOff)
        setApiUp(!isOff)
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  const onExample = (ex: ExampleScenario) => {
    setActiveExample(ex.id)
    setRx(ex.rx)
    setPatient(ex.patient)
    void runAnalyze(ex.rx, ex.patient, ex.id)
  }

  const onAnalyze = () => {
    void runAnalyze(rx, patient, activeExample)
  }

  const onPickCandidate = (line: string, brandName: string) => {
    // Replace the matching prescription line with the chosen brand text and re-run
    const lines = rx.split('\n')
    const next = lines
      .map((l) => {
        if (!line) return l
        if (l.trim() === line.trim() || l.includes(line.slice(0, 12))) {
          // Keep form hint if present
          const form = l.match(/^(Tab|Cap|Syp|Susp|Inj)\s+/i)?.[0] || 'Tab '
          return `${form}${brandName} OD`
        }
        return l
      })
      .join('\n')
    setRx(next)
    setActiveExample(null)
    void runAnalyze(next, patient, null)
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

          <div className="grid gap-6 lg:grid-cols-2">
            <CheckerPanel
              rx={rx}
              patient={patient}
              activeExample={activeExample}
              loading={loading}
              offline={offline}
              onRxChange={(v) => {
                setRx(v)
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
