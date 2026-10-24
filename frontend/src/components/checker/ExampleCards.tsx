import {
  AlertTriangle,
  Baby,
  CheckCircle2,
  Droplets,
  Layers,
  ScanSearch,
  Activity,
} from 'lucide-react'
import type { ExampleScenario } from '../../data/examples'
import { EXAMPLES } from '../../data/examples'

const ICONS = {
  layers: Layers,
  alert: AlertTriangle,
  baby: Baby,
  droplets: Droplets,
  search: ScanSearch,
  kidney: Activity,
  check: CheckCircle2,
}

interface Props {
  activeId: string | null
  onSelect: (ex: ExampleScenario) => void
}

export function ExampleCards({ activeId, onSelect }: Props) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-semibold">Example scenarios</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {EXAMPLES.map((ex) => {
          const Icon = ICONS[ex.icon]
          const active = activeId === ex.id
          return (
            <button
              key={ex.id}
              type="button"
              onClick={() => onSelect(ex)}
              className={`glass glass-hover flex gap-3 rounded-2xl p-3 text-left transition ${
                active ? 'border-teal-500/40 ring-1 ring-teal-500/30' : ''
              }`}
              aria-pressed={active}
            >
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500/20 to-indigo-500/20">
                <Icon className="h-4 w-4 text-teal-300" aria-hidden />
              </span>
              <span>
                <span className="block text-sm font-semibold leading-snug">{ex.title}</span>
                <span className="mt-0.5 block text-xs text-[var(--muted)]">{ex.subtitle}</span>
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
