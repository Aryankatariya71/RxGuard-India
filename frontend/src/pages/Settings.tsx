import { useEffect, useState } from 'react'
import { api } from '../api/hm02'
import { BannerDisclaimer } from '../components/common/Disclaimer'

export function Settings() {
  const [cfg, setCfg] = useState<Record<string, unknown> | null>(null)
  const [health, setHealth] = useState<Record<string, unknown> | null>(null)
  const [data, setData] = useState<Record<string, unknown> | null>(null)
  const [rules, setRules] = useState<Record<string, unknown> | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    Promise.all([api.config(), api.health(), api.dataStatus(), api.rulesStatus()])
      .then(([c, h, d, r]) => {
        setCfg(c as unknown as Record<string, unknown>)
        setHealth(h as unknown as Record<string, unknown>)
        setData(d)
        setRules(r)
      })
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Settings</h1>
      {error && (
        <div className="card border-red-200 bg-red-50 p-3 text-red-800" role="alert">
          {error}
        </div>
      )}
      <BannerDisclaimer />
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="card p-4 text-sm">
          <h2 className="font-bold">Application</h2>
          <ul className="mt-2 space-y-1 text-[var(--color-muted)]">
            <li>Name: {String(cfg?.app_name || '—')}</li>
            <li>Version: {String(cfg?.app_version || '—')}</li>
            <li>Demo mode: {String(cfg?.demo_data_mode)}</li>
            <li>Auth enabled: {String(cfg?.auth_enabled)} (explicitly off in prototype)</li>
          </ul>
        </div>
        <div className="card p-4 text-sm">
          <h2 className="font-bold">Connectivity</h2>
          <ul className="mt-2 space-y-1 text-[var(--color-muted)]">
            <li>API: {String(health?.status)}</li>
            <li>Database: {String(health?.database)}</li>
            <li>Environment: {String(health?.environment)}</li>
          </ul>
        </div>
        <div className="card p-4 text-sm">
          <h2 className="font-bold">Catalogue</h2>
          <ul className="mt-2 space-y-1 text-[var(--color-muted)]">
            <li>Version: {String(data?.catalogue_version)}</li>
            <li>Synthetic products: {String(data?.synthetic_product_count)}</li>
            <li>Source-backed: {String(data?.source_backed_product_count)}</li>
          </ul>
        </div>
        <div className="card p-4 text-sm">
          <h2 className="font-bold">Rules</h2>
          <ul className="mt-2 space-y-1 text-[var(--color-muted)]">
            <li>Version: {String(rules?.rule_set_version)}</li>
            <li>Active interactions: {String(rules?.active_interaction_rules)}</li>
            <li>Active dosage: {String(rules?.active_dosage_rules)}</li>
            <li>Synthetic rules: {String(rules?.synthetic_rule_count)}</li>
          </ul>
        </div>
      </div>
      <div className="card p-4 text-sm text-[var(--color-muted)]">
        <h2 className="font-bold text-[var(--color-ink)]">Privacy</h2>
        <p className="mt-2">
          Demo reviews are stored locally in SQLite. Avoid entering real patient identifiers.
          Delete reviews from History. No secrets are exposed in this UI.
        </p>
        <p className="mt-2">
          To reset demonstration DB: delete <code>backend/data/rxguard.db</code> and re-run{' '}
          <code>python backend/scripts/seed_demo_data.py</code>.
        </p>
      </div>
    </div>
  )
}
