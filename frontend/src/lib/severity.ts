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
        label: 'Urgent Attention',
        icon: ShieldAlert,
        className: 'text-[#B91C1C]',
        bg: 'bg-[#FEF2F2]',
        border: 'border-[#FECACA]',
      }
    case 'review':
      return {
        key: 'review',
        label: 'Please Check',
        icon: AlertTriangle,
        className: 'text-[#B45309]',
        bg: 'bg-[#FFF7ED]',
        border: 'border-[#FED7AA]',
      }
    case 'info':
      return {
        key: 'info',
        label: 'General Information',
        icon: Info,
        className: 'text-[#1D4ED8]',
        bg: 'bg-[#EFF6FF]',
        border: 'border-[#BFDBFE]',
      }
    default:
      return {
        key: 'clear',
        label: 'Confirmed',
        icon: CheckCircle2,
        className: 'text-[#15803D]',
        bg: 'bg-[#F0FDF4]',
        border: 'border-[#BBF7D0]',
      }
  }
}
