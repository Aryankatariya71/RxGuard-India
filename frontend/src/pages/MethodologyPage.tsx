import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion, useReducedMotion } from 'framer-motion'
import {
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  Download,
  Info,
  Link2,
  Printer,
  Search,
  ShieldAlert,
} from 'lucide-react'
import {
  analyzeLiveExample,
  fetchMethodologyStats,
  formatStat,
  searchMedicineLive,
  type MethodologyStats,
} from '../api/methodology'
import { AppLayout } from '../components/layout/AppLayout'
import { ErrorBoundary } from '../components/common/ErrorBoundary'

const DISCLAIMER =
  'RxGuard India is a prescription-review support prototype. It does not replace a doctor or pharmacist. A missing alert does not prove a prescription is safe. Verify findings with a qualified healthcare professional.'

const PIPELINE = [
  'Prescription text',
  'Parser',
  'Brand resolver',
  'Ingredient expansion',
  'Daily dose',
  'Duplicate / Interaction / Dose checks',
  'Alert manager',
  'Report',
] as const

const TOC = [
  { id: 'glance', label: 'At a glance' },
  { id: 'problem', label: '1. The problem' },
  { id: 'principles', label: '2. Design principles' },
  { id: 'pipeline', label: '3. Pipeline' },
  { id: 'data-sources', label: '4. Data sources' },
  { id: 'brand-resolution', label: '5. Brand resolution' },
  { id: 'ingredient-expansion', label: '6. Ingredient expansion' },
  { id: 'dose', label: '7. Parsing & dose' },
  { id: 'safety-checks', label: '8. Safety checks' },
  { id: 'alert-fatigue', label: '9. Alert fatigue' },
  { id: 'evaluation', label: '10. Evaluation' },
  { id: 'explainability', label: '11. Explainability' },
  { id: 'privacy', label: '12. Privacy & security' },
  { id: 'limitations', label: '13. Limitations' },
  { id: 'related', label: '14. Related work' },
] as const

const WORKED_RX = 'Tab Dolo 650 1-0-1 x 5 days\nTab Combiflam 1-0-1'

function Section({
  id,
  title,
  children,
}: {
  id: string
  title: string
  children: React.ReactNode
}) {
  const copy = async () => {
    const url = `${window.location.origin}/methodology#${id}`
    await navigator.clipboard.writeText(url)
  }
  return (
    <section id={id} className="scroll-mt-28 print-report">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-2">
        <h2 className="text-2xl font-bold tracking-tight text-[#123C38] sm:text-3xl">{title}</h2>
        <button
          type="button"
          onClick={() => void copy()}
          className="no-print btn-secondary inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs"
          aria-label={`Copy link to ${title}`}
        >
          <Link2 className="h-3.5 w-3.5" aria-hidden />
          Copy link
        </button>
      </div>
      <div className="space-y-4 text-sm leading-relaxed text-[#334155]">{children}</div>
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rx-card p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-[#82918F]">{label}</p>
      <p className="mt-1 font-mono text-xl font-semibold tabular-nums text-[#123C38]">{value}</p>
    </div>
  )
}

export function MethodologyPage() {
  const reduce = useReducedMotion()
  const [stats, setStats] = useState<MethodologyStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [active, setActive] = useState('glance')
  const [tocOpen, setTocOpen] = useState(false)
  const [pipeStep, setPipeStep] = useState(0)
  const [exampleOut, setExampleOut] = useState<unknown>(null)
  const [exampleErr, setExampleErr] = useState<string | null>(null)
  const [exampleBusy, setExampleBusy] = useState(false)
  const [searchQ, setSearchQ] = useState('dolo650')
  const [searchOut, setSearchOut] = useState<unknown>(null)
  const [searchErr, setSearchErr] = useState<string | null>(null)
  const [searchBusy, setSearchBusy] = useState(false)

  useEffect(() => {
    setLoading(true)
    void fetchMethodologyStats().then((d) => {
      setStats(d)
      setLoading(false)
    })
  }, [])

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return
    const ids = TOC.map((t) => t.id)
    const obs = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0]
        if (visible?.target?.id) setActive(visible.target.id)
      },
      { rootMargin: '-20% 0px -60% 0px', threshold: [0.1, 0.25, 0.5] },
    )
    ids.forEach((id) => {
      const el = document.getElementById(id)
      if (el) obs.observe(el)
    })
    return () => obs.disconnect()
  }, [loading])

  const runExample = useCallback(async () => {
    setExampleBusy(true)
    setExampleErr(null)
    try {
      const data = await analyzeLiveExample(WORKED_RX)
      setExampleOut(data)
    } catch (e) {
      setExampleErr(e instanceof Error ? e.message : 'Analyze unavailable')
      setExampleOut(null)
    } finally {
      setExampleBusy(false)
    }
  }, [])

  const runSearch = useCallback(async () => {
    setSearchBusy(true)
    setSearchErr(null)
    try {
      const data = await searchMedicineLive(searchQ.trim() || 'dolo')
      setSearchOut(data)
    } catch (e) {
      setSearchErr(e instanceof Error ? e.message : 'Search unavailable')
      setSearchOut(null)
    } finally {
      setSearchBusy(false)
    }
  }, [searchQ])

  const exportMarkdown = () => {
    const md = buildMarkdown(stats)
    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'METHODOLOGY.md'
    a.click()
    URL.revokeObjectURL(url)
  }

  const intStatus = stats?.interaction_rules?.by_status
  const doseStatus = stats?.dose_rules?.by_status
  const files = stats?.catalogue_files

  const glanceBullets = useMemo(
    () => [
      `Deterministic rules engine (engine ${formatStat(stats?.engine_version)}) — not an LLM judge.`,
      `Local catalogue: ${formatStat(stats?.products_in_db)} products · ${formatStat(stats?.ingredients_in_db)} ingredients.`,
      `Interaction rules: ${formatStat(intStatus?.total)} · Dose rules: ${formatStat(doseStatus?.total)}.`,
      `DDInter pairs loaded: ${formatStat(stats?.ddinter_pairs_loaded)}.`,
      `Gold evaluation cases: ${formatStat(stats?.gold?.gold_case_count)} (developer-labeled).`,
      `Automated backend tests: ${formatStat(stats?.tests?.backend_test_function_count)}.`,
    ],
    [stats, intStatus, doseStatus],
  )

  return (
    <AppLayout title="Methodology" subtitle="How RxGuard India works">
      <ErrorBoundary label="Methodology page">
        <div className="methodology-page bg-[#F1F7F5] pb-16" data-testid="methodology-page">
          <div className="border-b border-[#DCE8E4] bg-white">
            <div className="rx-container py-8 sm:py-10">
              <p className="inline-flex items-center gap-2 rounded-full border border-[#DCE8E4] bg-[#DDF5EC] px-3 py-1 text-xs font-medium text-[#123C38]">
                <BookOpen className="h-3.5 w-3.5 text-[#0D9B78]" aria-hidden />
                For judges, pharmacists, and engineers
              </p>
              <h1 className="mt-4 text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
                Methodology
              </h1>
              <p className="rx-prose mt-3 text-[#64748B]">
                How RxGuard India parses Indian brand prescriptions, expands combination products,
                runs deterministic safety checks, and surfaces uncertainty without claiming clinical
                validation.
              </p>
              <div className="no-print mt-6 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="btn-secondary inline-flex items-center gap-2 px-3 py-2 text-sm"
                >
                  <Printer className="h-4 w-4" aria-hidden />
                  Print / Save as PDF
                </button>
                <button
                  type="button"
                  onClick={exportMarkdown}
                  className="btn-secondary inline-flex items-center gap-2 px-3 py-2 text-sm"
                >
                  <Download className="h-4 w-4" aria-hidden />
                  Export as Markdown
                </button>
                <Link to="/about" className="btn-secondary inline-flex items-center gap-2 px-3 py-2 text-sm">
                  About
                </Link>
              </div>
            </div>
          </div>

          <div
            className="disclaimer-banner border-b border-[#FED7AA] bg-[#FFF7ED] px-4 py-3 text-sm text-[#B45309]"
            role="note"
            data-testid="methodology-disclaimer-top"
          >
            <div className="rx-container flex gap-2">
              <Info className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
              <p>{DISCLAIMER}</p>
            </div>
          </div>

          <div className="rx-container mt-8 grid gap-8 lg:grid-cols-[240px_minmax(0,1fr)]">
            <aside className="no-print lg:sticky lg:top-24 lg:self-start">
              <div className="lg:hidden">
                <button
                  type="button"
                  className="btn-secondary flex w-full items-center justify-between px-3 py-2 text-sm"
                  aria-expanded={tocOpen}
                  onClick={() => setTocOpen((v) => !v)}
                >
                  On this page
                  <ChevronDown className={`h-4 w-4 transition ${tocOpen ? 'rotate-180' : ''}`} />
                </button>
                {tocOpen && (
                  <nav className="mt-2 rx-card p-2" aria-label="Table of contents">
                    {TOC.map((t) => (
                      <a
                        key={t.id}
                        href={`#${t.id}`}
                        onClick={() => setTocOpen(false)}
                        className={`block rounded-lg px-3 py-2 text-sm ${
                          active === t.id ? 'bg-[#DDF5EC] text-[#123C38]' : 'text-[#64748B]'
                        }`}
                      >
                        {t.label}
                      </a>
                    ))}
                  </nav>
                )}
              </div>
              <nav className="hidden rx-card p-3 lg:block" aria-label="Table of contents">
                <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-wide text-[#82918F]">
                  On this page
                </p>
                {TOC.map((t) => (
                  <a
                    key={t.id}
                    href={`#${t.id}`}
                    className={`block rounded-lg px-2 py-1.5 text-sm transition ${
                      active === t.id
                        ? 'bg-[#DDF5EC] font-medium text-[#123C38]'
                        : 'text-[#64748B] hover:bg-[#F1F7F5] hover:text-[#123C38]'
                    }`}
                    aria-current={active === t.id ? 'true' : undefined}
                  >
                    {t.label}
                  </a>
                ))}
              </nav>
            </aside>

            <div className="min-w-0 space-y-14">
              {loading && (
                <p className="text-sm text-[#64748B]" role="status">
                  Loading live methodology stats…
                </p>
              )}

              <Section id="glance" title="Methodology at a glance">
                <ul className="rx-card space-y-2 p-5">
                  {glanceBullets.map((b) => (
                    <li key={b} className="flex gap-2 text-[#334155]">
                      <CheckCircle2
                        className="mt-0.5 h-4 w-4 shrink-0 text-[#0D9B78]"
                        aria-hidden
                      />
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Stat label="Products in DB" value={formatStat(stats?.products_in_db)} />
                  <Stat label="Ingredients" value={formatStat(stats?.ingredients_in_db)} />
                  <Stat
                    label="Dataset version"
                    value={formatStat(stats?.dataset_version)}
                  />
                  <Stat label="Engine version" value={formatStat(stats?.engine_version)} />
                  <Stat
                    label="Interaction rules"
                    value={formatStat(intStatus?.total)}
                  />
                  <Stat label="Dose rules" value={formatStat(doseStatus?.total)} />
                </div>
              </Section>

              <Section id="problem" title="1. The problem">
                <p>
                  Indian prescriptions commonly use <strong>brand names</strong>,{' '}
                  <strong>combination products</strong>, and abbreviations such as OD, BD, TDS, and
                  SOS. Those habits can hide duplicate ingredients, interactions, and excessive daily
                  doses when checking brands by eye.
                </p>
                <div className="grid gap-3 sm:grid-cols-2">
                  {[
                    {
                      title: 'Misspelled brands',
                      how: 'Normalisation + exact / prefix / fuzzy resolution with confirmation.',
                      href: '#brand-resolution',
                    },
                    {
                      title: 'Combination ingredients',
                      how: 'Expand each brand into APIs + strengths before safety checks.',
                      href: '#ingredient-expansion',
                    },
                    {
                      title: 'Patient-specific dose limits',
                      how: 'Sum mg/day and apply draft adult / paediatric / renal rules when data exists.',
                      href: '#dose',
                    },
                    {
                      title: 'Alert fatigue',
                      how: 'Merge duplicate+dose, dedupe pairs, tier critical / review / info.',
                      href: '#alert-fatigue',
                    },
                  ].map((c) => (
                    <article key={c.title} className="rx-card p-4">
                      <h3 className="font-semibold text-[#123C38]">{c.title}</h3>
                      <p className="mt-1 text-[#64748B]">
                        <span className="font-medium text-[#087F6E]">How we address it: </span>
                        {c.how}
                      </p>
                      <a href={c.href} className="mt-2 inline-block text-[#087F6E] underline-offset-2 hover:underline">
                        Jump to section
                      </a>
                    </article>
                  ))}
                </div>
              </Section>

              <Section id="principles" title="2. Design principles">
                <ul className="list-disc space-y-2 pl-5">
                  <li>
                    <strong>Deterministic rules engine</strong>, not an LLM judge.
                  </li>
                  <li>
                    Every finding traces to a <strong>stored rule</strong> (id, source, version,
                    status).
                  </li>
                  <li>
                    <strong>Uncertainty is shown</strong>, not hidden — unresolved items and
                    checks-not-run stay visible.
                  </li>
                  <li>
                    Unresolved brands <strong>block dependent checks</strong> that need identity.
                  </li>
                  <li>
                    Identity confidence and clinical severity are <strong>separate axes</strong>.
                  </li>
                  <li>
                    <strong>“No match” never means a prescription needs no review</strong> — absence
                    of an alert is not clearance.
                  </li>
                </ul>
              </Section>

              <Section id="pipeline" title="3. Pipeline">
                <p>
                  Click a step for a short description. Run the worked example through the live{' '}
                  <code className="font-mono text-xs">POST /api/analyze</code> endpoint.
                </p>
                <div className="flex flex-wrap gap-2" role="list">
                  {PIPELINE.map((step, i) => (
                    <button
                      key={step}
                      type="button"
                      role="listitem"
                      onClick={() => setPipeStep(i)}
                      className={`rounded-xl border px-3 py-2 text-left text-xs font-medium transition ${
                        pipeStep === i
                          ? 'border-[#0D9B78] bg-[#DDF5EC] text-[#123C38]'
                          : 'border-[#DCE8E4] bg-white text-[#64748B] hover:border-[#0D9B78]/40'
                      }`}
                      aria-pressed={pipeStep === i}
                    >
                      <span className="mr-1 text-[#0D9B78]">{i + 1}.</span>
                      {step}
                    </button>
                  ))}
                </div>
                <motion.div
                  key={pipeStep}
                  initial={reduce ? false : { opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rx-card p-5"
                >
                  <PipelinePanel step={pipeStep} />
                </motion.div>
                <div className="rx-card space-y-3 p-5">
                  <h3 className="font-semibold text-[#123C38]">Worked example (live engine)</h3>
                  <pre className="overflow-x-auto rounded-xl bg-[#F8FBFA] p-3 font-mono text-xs text-[#123C38]">
                    {WORKED_RX}
                  </pre>
                  <button
                    type="button"
                    className="btn-primary px-4 py-2 text-sm text-white disabled:opacity-50"
                    disabled={exampleBusy}
                    onClick={() => void runExample()}
                  >
                    {exampleBusy ? 'Running…' : 'Run through live engine'}
                  </button>
                  {exampleErr && (
                    <p className="text-[#B45309]" role="alert">
                      {exampleErr} — start the API to see live output.
                    </p>
                  )}
                  {exampleOut != null && (
                    <pre className="max-h-80 overflow-auto rounded-xl border border-[#DCE8E4] bg-white p-3 font-mono text-[11px] text-[#334155]">
                      {JSON.stringify(exampleOut, null, 2)}
                    </pre>
                  )}
                </div>
              </Section>

              <Section id="data-sources" title="4. Data sources">
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[640px] border-collapse text-left text-sm">
                    <thead>
                      <tr className="border-b border-[#DCE8E4] text-[#123C38]">
                        <th className="py-2 pr-3 font-semibold">Source</th>
                        <th className="py-2 pr-3 font-semibold">Licence / terms</th>
                        <th className="py-2 pr-3 font-semibold">What we use</th>
                        <th className="py-2 font-semibold">What we do not trust it for</th>
                      </tr>
                    </thead>
                    <tbody className="text-[#334155]">
                      <tr className="border-b border-[#DCE8E4]">
                        <td className="py-3 pr-3 align-top">
                          A–Z Medicines Dataset of India (Kaggle)
                          <p className="mt-1 font-mono text-xs text-[#64748B]">
                            rows before cleaning: {formatStat(files?.source_csv_rows)}
                            <br />
                            after clean/dedupe: {formatStat(files?.cleaned_parquet_rows)}
                            <br />
                            in local DB now: {formatStat(stats?.products_in_db)}
                          </p>
                        </td>
                        <td className="py-3 pr-3 align-top">Respect upstream Kaggle licence</td>
                        <td className="py-3 pr-3 align-top">
                          Brand ↔ composition catalogue (≤2 composition fields)
                        </td>
                        <td className="py-3 align-top">
                          Dataset “use” / “side effect” text is <em>not</em> used for safety logic;
                          prices are 2022 snapshots and unverified; not CDSCO-verified.
                        </td>
                      </tr>
                      <tr className="border-b border-[#DCE8E4]">
                        <td className="py-3 pr-3 align-top">
                          DDInter 2.0
                          <p className="mt-1 font-mono text-xs text-[#64748B]">
                            pairs loaded: {formatStat(stats?.ddinter_pairs_loaded)}
                          </p>
                        </td>
                        <td className="py-3 pr-3 align-top">Academic / non-commercial research use</td>
                        <td className="py-3 pr-3 align-top">
                          Pair levels after normalisation; Unknown dropped; dedupe across files
                          keeping highest level; filtered toward catalogue ingredients where
                          configured.
                        </td>
                        <td className="py-3 align-top">
                          Not a complete clinical interaction knowledge base; curated draft rules
                          override when present.
                        </td>
                      </tr>
                      <tr className="border-b border-[#DCE8E4]">
                        <td className="py-3 pr-3 align-top">Curated draft rules</td>
                        <td className="py-3 pr-3 align-top">Project-authored, status-labeled</td>
                        <td className="py-3 pr-3 align-top">
                          High-priority pairs and dose limits with explicit DRAFT / REVIEW_PENDING
                          status
                        </td>
                        <td className="py-3 align-top">
                          Not pharmacist-verified unless status is CLINICALLY_REVIEWED
                        </td>
                      </tr>
                      <tr>
                        <td className="py-3 pr-3 align-top">Synthetic demo seed</td>
                        <td className="py-3 pr-3 align-top">Bundled DEMO_ONLY</td>
                        <td className="py-3 pr-3 align-top">Offline demos when catalogue is empty</td>
                        <td className="py-3 align-top">Never treat as real formulary data</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </Section>

              <Section id="brand-resolution" title="5. Brand resolution">
                <p>
                  Normalisation: case-fold, strip punctuation, split letters/digits (e.g.{' '}
                  <code className="font-mono text-xs">dolo650</code>). Match order: exact →
                  token-prefix → fuzzy. Number-aware matching keeps pantop 40 from matching pantop
                  20. Fuzzy hits are <strong>suggestions</strong> that need user confirmation —
                  never auto-selected as verified identity.
                </p>
                <div className="rx-card space-y-3 p-5">
                  <h3 className="font-semibold text-[#123C38]">Try it (live search)</h3>
                  <div className="flex flex-wrap gap-2">
                    <input
                      className="rx-input min-w-[12rem] flex-1 px-3 py-2 text-sm"
                      value={searchQ}
                      onChange={(e) => setSearchQ(e.target.value)}
                      aria-label="Brand search query"
                    />
                    <button
                      type="button"
                      className="btn-primary inline-flex items-center gap-2 px-4 py-2 text-sm text-white disabled:opacity-50"
                      disabled={searchBusy}
                      onClick={() => void runSearch()}
                    >
                      <Search className="h-4 w-4" aria-hidden />
                      {searchBusy ? 'Searching…' : 'Search'}
                    </button>
                  </div>
                  {searchErr && <p className="text-[#B45309]">{searchErr}</p>}
                  {searchOut != null && (
                    <pre className="max-h-64 overflow-auto rounded-xl border border-[#DCE8E4] bg-[#F8FBFA] p-3 font-mono text-[11px]">
                      {JSON.stringify(searchOut, null, 2)}
                    </pre>
                  )}
                </div>
              </Section>

              <Section id="ingredient-expansion" title="6. Ingredient expansion">
                <p>
                  Compositions parse into (ingredient, strength, unit, per-unit). Salt stripping and
                  synonyms (amoxycillin → amoxicillin, acetylsalicylic acid → aspirin) apply with
                  protected names. Syrup per-5-ml handling is supported when the basis is known. The
                  source holds at most <strong>two compositions</strong> per product — 3+ ingredient
                  products may be flagged “composition may be incomplete” (
                  incomplete links in DB: {formatStat(stats?.incomplete_composition_links)}).
                </p>
                <div className="space-y-3">
                  {(stats?.composition_examples || []).length > 0 ? (
                    stats!.composition_examples!.map((ex) => (
                      <div key={ex.brand_name + ex.before} className="rx-card p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-[#82918F]">
                          Before → after
                        </p>
                        <p className="mt-1 font-mono text-sm text-[#123C38]">{ex.before}</p>
                        <p className="mt-2 font-mono text-xs text-[#087F6E]">
                          → {ex.after.join(' · ')}
                        </p>
                        {ex.incomplete_flag && (
                          <p className="mt-2 text-xs text-[#B45309]">
                            Composition may be incomplete
                          </p>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-[#64748B]">
                      Composition examples: not available (seed the catalogue or start the API).
                    </p>
                  )}
                </div>
              </Section>

              <Section id="dose" title="7. Prescription parsing and dose calculation">
                <p>
                  Frequency table covers OD, BD, TDS, QID, HS, digit patterns like 1-0-1, and SOS.
                  Daily dose per ingredient is summed across brands. SOS uses an assumed maximum and
                  is labeled. Ambiguous schedules produce CHECK_NOT_RUN rather than a silent guess.
                </p>
                <div className="rx-card p-5 font-mono text-xs leading-relaxed text-[#123C38]">
                  daily_mg(ingredient) = Σ (strength_mg_per_unit × units_per_day) across resolved
                  brands
                  <br />
                  Example pattern: 1-0-1 → 2 units/day; BD → 2; TDS → 3; OD → 1
                </div>
                <p>
                  Worked illustration: for Dolo 650 at 1-0-1, if resolved as 650 mg paracetamol × 2
                  units/day → 1300 mg/day from that brand alone, before adding other paracetamol
                  brands. Run the pipeline example above for live numbers from the engine.
                </p>
              </Section>

              <Section id="safety-checks" title="8. Safety checks">
                <ul className="list-disc space-y-2 pl-5">
                  <li>
                    <strong>Duplicate ingredient</strong> — same ingredient (and same class where
                    configured) across brands.
                  </li>
                  <li>
                    <strong>Interaction</strong> — unordered pairs; curated rules override DDInter;
                    class-level rules; Major/Moderate/Minor map to critical/review/info.
                  </li>
                  <li>
                    <strong>Dose</strong> — adult limit, paediatric mg/kg with shown formula, renal
                    band, elderly note, required-fields declaration; “unable to assess” when data is
                    missing.
                  </li>
                </ul>
                <h3 className="pt-2 font-semibold text-[#123C38]">Rule status lifecycle</h3>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  {['DEMO_ILLUSTRATIVE', 'REVIEW_PENDING', 'CLINICALLY_REVIEWED'].map((s, i) => (
                    <span key={s} className="inline-flex items-center gap-2">
                      <span className="rounded-lg border border-[#DCE8E4] bg-white px-3 py-1.5 font-mono text-xs text-[#123C38]">
                        {s}
                      </span>
                      {i < 2 && <span className="text-[#82918F]">→</span>}
                    </span>
                  ))}
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rx-card p-4">
                    <p className="text-xs font-semibold uppercase text-[#82918F]">
                      Interaction rules by status
                    </p>
                    <ul className="mt-2 space-y-1 font-mono text-sm">
                      <li>DEMO_ILLUSTRATIVE: {formatStat(intStatus?.DEMO_ILLUSTRATIVE)}</li>
                      <li>REVIEW_PENDING: {formatStat(intStatus?.REVIEW_PENDING)}</li>
                      <li>CLINICALLY_REVIEWED: {formatStat(intStatus?.CLINICALLY_REVIEWED)}</li>
                      <li>total: {formatStat(intStatus?.total)}</li>
                    </ul>
                  </div>
                  <div className="rx-card p-4">
                    <p className="text-xs font-semibold uppercase text-[#82918F]">
                      Dose rules by status
                    </p>
                    <ul className="mt-2 space-y-1 font-mono text-sm">
                      <li>DEMO_ILLUSTRATIVE: {formatStat(doseStatus?.DEMO_ILLUSTRATIVE)}</li>
                      <li>REVIEW_PENDING: {formatStat(doseStatus?.REVIEW_PENDING)}</li>
                      <li>CLINICALLY_REVIEWED: {formatStat(doseStatus?.CLINICALLY_REVIEWED)}</li>
                      <li>total: {formatStat(doseStatus?.total)}</li>
                    </ul>
                  </div>
                </div>
                <p className="rounded-xl border border-[#FED7AA] bg-[#FFF7ED] px-4 py-3 text-[#B45309]">
                  {stats?.rule_status_note ||
                    'Today most rules are REVIEW_PENDING. CLINICALLY_REVIEWED requires pharmacist verification.'}
                </p>
              </Section>

              <Section id="alert-fatigue" title="9. Alert-fatigue design">
                <p>
                  Duplicate + dose findings for the same ingredient can merge; identical interaction
                  pairs dedupe; three tiers surface critical first; info can collapse.
                </p>
                {stats?.alert_fatigue?.naive_alert_count != null &&
                stats?.alert_fatigue?.merged_alert_count != null ? (
                  <div className="grid gap-3 sm:grid-cols-2">
                    <Stat
                      label="Naive alert count"
                      value={formatStat(stats.alert_fatigue.naive_alert_count)}
                    />
                    <Stat
                      label="Merged alert count"
                      value={formatStat(stats.alert_fatigue.merged_alert_count)}
                    />
                  </div>
                ) : (
                  <p className="rx-card p-4 text-[#64748B]">
                    {stats?.alert_fatigue?.note ||
                      'Run the stress test to measure naive vs merged alert counts.'}{' '}
                    <Link to="/stress-test" className="text-[#087F6E] underline-offset-2 hover:underline">
                      Open stress test
                    </Link>
                  </p>
                )}
              </Section>

              <Section id="evaluation" title="10. Evaluation">
                <div
                  className="rounded-xl border border-[#BFDBFE] bg-[#EFF6FF] px-4 py-3 text-[#1D4ED8]"
                  role="note"
                >
                  Labels were written by the development team from the same rule set, so these
                  figures show <strong>internal consistency, not clinical accuracy</strong>.
                  Pharmacist verification is the next step.
                </div>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  <Stat
                    label="Gold cases"
                    value={formatStat(stats?.gold?.gold_case_count)}
                  />
                  <Stat
                    label="Developer-labeled"
                    value={formatStat(stats?.gold?.developer_labeled_count)}
                  />
                  <Stat
                    label="Pharmacist-verified"
                    value={formatStat(stats?.gold?.pharmacist_verified_count)}
                  />
                  <Stat
                    label="Brand-resolution accuracy"
                    value={
                      stats?.evaluation?.brand_resolution_accuracy != null
                        ? `${stats.evaluation.brand_resolution_accuracy} (${formatStat(stats.evaluation.brand_resolution_hits)}/${formatStat(stats.evaluation.brand_resolution_total)})`
                        : 'not available'
                    }
                  />
                  <Stat
                    label="False-alarm rate (clean)"
                    value={
                      stats?.evaluation?.false_alarm_rate_clean != null
                        ? `${stats.evaluation.false_alarm_rate_clean} (${formatStat(stats.evaluation.false_alarm_count)}/${formatStat(stats.evaluation.clean_case_count)})`
                        : 'not available'
                    }
                  />
                  <Stat
                    label="Backend tests"
                    value={formatStat(stats?.tests?.backend_test_function_count)}
                  />
                </div>
                {stats?.evaluation?.precision_recall_by_type && (
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[480px] border-collapse text-left text-sm">
                      <thead>
                        <tr className="border-b border-[#DCE8E4]">
                          <th className="py-2">type</th>
                          <th className="py-2">precision</th>
                          <th className="py-2">recall</th>
                          <th className="py-2">tp</th>
                          <th className="py-2">fp</th>
                          <th className="py-2">fn</th>
                        </tr>
                      </thead>
                      <tbody>
                        {stats.evaluation.precision_recall_by_type.map((r) => (
                          <tr key={r.type} className="border-b border-[#DCE8E4] font-mono text-xs">
                            <td className="py-2">{r.type}</td>
                            <td className="py-2">{r.precision}</td>
                            <td className="py-2">{r.recall}</td>
                            <td className="py-2">{r.tp}</td>
                            <td className="py-2">{r.fp}</td>
                            <td className="py-2">{r.fn}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </Section>

              <Section id="explainability" title="11. Explainability and uncertainty">
                <p>
                  Each finding can answer “Why am I seeing this?” with rule id, exact numbers used,
                  source, version, and status. The report also shows a <strong>Checks not run</strong>{' '}
                  panel when identity or schedule data is insufficient.
                </p>
                <div className="rx-card p-4">
                  <p className="text-xs font-semibold uppercase text-[#82918F]">Identity statuses</p>
                  <ul className="mt-2 grid gap-1 font-mono text-xs sm:grid-cols-2">
                    {[
                      'VERIFIED_CATALOGUE_MATCH',
                      'USER_CONFIRMED_MATCH',
                      'SUGGESTED_MATCH',
                      'AMBIGUOUS',
                      'UNRESOLVED',
                    ].map((s) => (
                      <li key={s}>{s}</li>
                    ))}
                  </ul>
                </div>
                <p>
                  Open any safety report finding and use <strong>Why?</strong> to inspect the live
                  trace after running the checker.
                </p>
              </Section>

              <Section id="privacy" title="12. Privacy and security">
                <ul className="list-disc space-y-2 pl-5">
                  <li>Synthetic data by default in demo mode.</li>
                  <li>No names, phone numbers, or Aadhaar collection in the product UI.</li>
                  <li>No prescription logging to third-party analytics by default.</li>
                  <li>Runs offline against the local API and catalogue when seeded.</li>
                  <li>
                    No external LLM or server OCR by default. Voice input uses the browser speech
                    service (needs network). Photo scan OCR runs locally in the browser.
                  </li>
                  <li>No secrets committed in source.</li>
                </ul>
              </Section>

              <Section id="limitations" title="13. Limitations and what we would do next">
                <ul className="list-disc space-y-2 pl-5">
                  <li>Rules pending pharmacist review.</li>
                  <li>3+ ingredient products not fully representable in two-composition fields.</li>
                  <li>Syrup strength basis sometimes unknown.</li>
                  <li>Dataset prices/entries are from 2022 and unverified.</li>
                  <li>
                    Interactions are pairwise only — no food, disease, or genotype effects modeled.
                  </li>
                  <li>No allergy or pregnancy rules unless present in the rule set.</li>
                  <li>Not a medical device.</li>
                </ul>
                <p className="font-semibold text-[#123C38]">Next steps (no timelines promised)</p>
                <ul className="list-disc space-y-1 pl-5">
                  <li>Pharmacist review workflow for rules.</li>
                  <li>Verified formulary data.</li>
                  <li>More curated rules with explicit status.</li>
                  <li>Hospital pilot with clinical oversight.</li>
                </ul>
              </Section>

              <Section id="related" title="14. Related work and references">
                <p>
                  Related open-source directions include RxCheck-style checkers and PillChecker-style
                  single-product tools. This project differs by brand-level ingredient splitting,
                  patient-aware draft dose limits, alert tiers with merge logic, explicit
                  checks-not-run, and a developer-labeled evaluation set pending pharmacist
                  verification.
                </p>
                <p>
                  Credits: DDInter authors; A–Z Medicines Dataset of India (Kaggle) contributors.
                </p>
                <div className="rx-card space-y-2 p-5">
                  <h3 className="flex items-center gap-2 font-semibold text-[#123C38]">
                    <ClipboardList className="h-4 w-4 text-[#0D9B78]" aria-hidden />
                    How to reproduce
                  </h3>
                  <pre className="overflow-x-auto rounded-xl bg-[#F8FBFA] p-3 font-mono text-[11px] text-[#123C38]">{`python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
python evaluate.py
# API (FastAPI)
uvicorn backend.app.main:app --reload --port 8000
# Frontend
cd frontend && npm install && npm run dev`}</pre>
                </div>
              </Section>

              <div
                className="disclaimer-banner rounded-2xl border border-[#FED7AA] bg-[#FFF7ED] px-4 py-3 text-sm text-[#B45309]"
                role="note"
                data-testid="methodology-disclaimer-bottom"
              >
                <div className="flex gap-2">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
                  <p>{DISCLAIMER}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ErrorBoundary>
    </AppLayout>
  )
}

function PipelinePanel({ step }: { step: number }) {
  const panels = [
    {
      does: 'Accept free-text Rx lines from the user or demo scenarios.',
      io: 'In: text. Out: raw lines for parsing.',
      fail: 'Empty input; non-text paste noise.',
    },
    {
      does: 'Parse brand tokens, frequency, duration, and timing abbreviations.',
      io: 'In: lines. Out: structured fields + ambiguity flags.',
      fail: 'Illegible OCR; novel abbreviations → CHECK_NOT_RUN.',
    },
    {
      does: 'Resolve brands against the local catalogue with exact/prefix/fuzzy stages.',
      io: 'In: brand string. Out: match type, score, candidates.',
      fail: 'Misspellings below threshold; strength-number collisions.',
    },
    {
      does: 'Expand combination products into ingredients + strengths.',
      io: 'In: product. Out: ingredient list; incomplete flag when needed.',
      fail: '3+ ingredient products; missing strength units.',
    },
    {
      does: 'Sum daily dose per ingredient across brands.',
      io: 'In: strengths × frequency. Out: mg/day totals.',
      fail: 'SOS / PRN without assumed max; unclear schedules.',
    },
    {
      does: 'Run duplicate, interaction, and dose rule checks.',
      io: 'In: ingredient set + patient fields. Out: findings with rule ids.',
      fail: 'Missing age/weight/renal → unable to assess dose rules.',
    },
    {
      does: 'Merge, dedupe, and tier alerts.',
      io: 'In: raw findings. Out: critical / review / info cards.',
      fail: 'Over-merging if rule ids collide incorrectly (covered by tests).',
    },
    {
      does: 'Render the safety report with evidence and checks-not-run.',
      io: 'In: alerts + identity statuses. Out: UI report / export text.',
      fail: 'Offline mock path when API is down — labeled as demo data.',
    },
  ]
  const p = panels[step] || panels[0]
  return (
    <div className="space-y-2 text-sm">
      <p>
        <span className="font-semibold text-[#123C38]">What it does: </span>
        {p.does}
      </p>
      <p>
        <span className="font-semibold text-[#123C38]">Inputs / outputs: </span>
        {p.io}
      </p>
      <p>
        <span className="font-semibold text-[#123C38]">Known failure modes: </span>
        {p.fail}
      </p>
    </div>
  )
}

function buildMarkdown(stats: MethodologyStats | null): string {
  const f = formatStat
  return `# RxGuard India — Methodology

> ${DISCLAIMER}

## At a glance
- Engine: ${f(stats?.engine_version)}
- Products in DB: ${f(stats?.products_in_db)}
- Ingredients: ${f(stats?.ingredients_in_db)}
- Interaction rules: ${f(stats?.interaction_rules?.by_status?.total)}
- Dose rules: ${f(stats?.dose_rules?.by_status?.total)}
- DDInter pairs: ${f(stats?.ddinter_pairs_loaded)}
- Gold cases: ${f(stats?.gold?.gold_case_count)}
- Backend tests: ${f(stats?.tests?.backend_test_function_count)}
- Dataset version: ${f(stats?.dataset_version)}

## Catalogue files
- Source CSV rows: ${f(stats?.catalogue_files?.source_csv_rows)}
- Cleaned parquet rows: ${f(stats?.catalogue_files?.cleaned_parquet_rows)}

## Evaluation note
Labels were written by the development team from the same rule set, so these figures show internal consistency, not clinical accuracy. Pharmacist verification is the next step.

Brand-resolution accuracy: ${f(stats?.evaluation?.brand_resolution_accuracy)}
False-alarm rate (clean): ${f(stats?.evaluation?.false_alarm_rate_clean)}

## Reproduce
\`\`\`
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pytest
python evaluate.py
uvicorn backend.app.main:app --reload --port 8000
cd frontend && npm install && npm run dev
\`\`\`

${DISCLAIMER}
`
}

export default MethodologyPage
