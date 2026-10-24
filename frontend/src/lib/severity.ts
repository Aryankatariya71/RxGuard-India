import { AlertTriangle, CheckCircle2, Info, ShieldAlert } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export type Tier = 'critical' | 'review' | 'info' | 'clear'

export function tierMeta(tier: string): {
  key: Tier
  label: string
  icon: LucideIcon
  className: string
  bg: string
  border: string
} {
  switch (tier) {
    case 'critical':
      return {
        key: 'critical',
        label: 'Critical',
        icon: ShieldAlert,
        className: 'text-rose-400',
        bg: 'bg-rose-500/10',
        border: 'border-rose-500/30',
      }
    case 'review':
      return {
        key: 'review',
        label: 'Review',
        icon: AlertTriangle,
        className: 'text-amber-400',
        bg: 'bg-amber-500/10',
        border: 'border-amber-500/30',
      }
    case 'info':
      return {
        key: 'info',
        label: 'Info',
        icon: Info,
        className: 'text-sky-400',
        bg: 'bg-sky-500/10',
        border: 'border-sky-500/30',
      }
    default:
      return {
        key: 'clear',
        label: 'Clear',
        icon: CheckCircle2,
        className: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30',
      }
  }
}
