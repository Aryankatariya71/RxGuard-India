export function HowItWorks() {
  const steps = [
    'Brand medicine identification against the catalogue (exact match; suggestions need confirmation).',
    'Ingredient resolution for single and combination products.',
    'Combination-product handling via product–ingredient links.',
    'Duplicate ingredient detection across distinct medicines.',
    'Configured interaction checking with normalized unordered pairs.',
    'Supported dosage checks only when inputs and rules exist.',
    'Evidence and uncertainty handling (DEMO_ONLY, NOT_EVALUATED, UNRESOLVED).',
    'Professional review — the tool never replaces a clinician.',
  ]
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">How it works</h1>
      <p className="text-[var(--color-muted)]">
        Deterministic rules engine. It does not cover every clinical issue.
      </p>
      <ol className="space-y-3">
        {steps.map((s, i) => (
          <li key={s} className="card flex gap-4 p-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 font-bold text-[var(--color-primary)]">
              {i + 1}
            </span>
            <p className="text-sm">{s}</p>
          </li>
        ))}
      </ol>
      <div className="card overflow-x-auto p-4">
        <pre className="text-xs leading-6 text-[var(--color-muted)]">{`Catalogue search → Exact resolve → Ingredients
        ↓
Duplicates │ Interactions │ Dosage (if rule+inputs)
        ↓
Findings + versions + disclaimer → Report / export`}</pre>
      </div>
    </div>
  )
}
