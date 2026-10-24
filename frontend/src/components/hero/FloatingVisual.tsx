import { motion, useReducedMotion } from 'framer-motion'
import {
  ArrowRight,
  ChartNoAxesCombined,
  FileText,
  Layers,
  Network,
  Pill,
  Scale,
  Search,
} from 'lucide-react'

const MEDS = [
  {
    brand: 'Dolo 650',
    ingredients: 'Paracetamol 650 mg',
    rxLine: 'Tab Dolo 650',
  },
  {
    brand: 'Combiflam',
    ingredients: 'Ibuprofen + Paracetamol',
    rxLine: 'Tab Combiflam',
  },
  {
    brand: 'Augmentin 625',
    ingredients: 'Amoxicillin + Clavulanic acid',
    rxLine: 'Tab Augmentin 625',
  },
] as const

const CHECKS = [
  {
    title: 'Ingredient duplication',
    description: 'Check for repeated active ingredients.',
    icon: Layers,
    border: 'border-[#FDE68A]',
    bg: 'bg-[#FFFBEB]',
    iconBg: 'bg-[#FEF3C7]',
    iconColor: 'text-[#D97706]',
    titleColor: 'text-[#B45309]',
  },
  {
    title: 'Possible interaction',
    description: 'Evaluate available interaction rules.',
    icon: Network,
    border: 'border-[#BFDBFE]',
    bg: 'bg-[#EFF6FF]',
    iconBg: 'bg-[#DBEAFE]',
    iconColor: 'text-[#2563EB]',
    titleColor: 'text-[#1D4ED8]',
  },
  {
    title: 'Dosage information',
    description: 'Review available dose information.',
    icon: Scale,
    border: 'border-[#BBF7D0]',
    bg: 'bg-[#F0FDF4]',
    iconBg: 'bg-[#DCFCE7]',
    iconColor: 'text-[#15803D]',
    titleColor: 'text-[#15803D]',
  },
] as const

const WORKFLOW = [
  { label: 'Identify ingredients', icon: Search },
  { label: 'Check interactions', icon: Network },
  { label: 'Review dosage', icon: ChartNoAxesCombined },
  { label: 'Present clear results', icon: FileText },
] as const

/**
 * Hero right visual: Prescription → Brands → Ingredients → Safety checks.
 * Illustrative demo only — not a patient result.
 */
export function FloatingVisual() {
  const reduce = useReducedMotion()

  return (
    <div
      className="relative w-full min-w-0"
      role="img"
      aria-label="Illustrative medicine safety flow: prescription to brand cards to safety checks"
    >
      {/* Soft mint halo */}
      <div
        className="pointer-events-none absolute inset-0 -z-0 overflow-hidden rounded-3xl"
        aria-hidden
      >
        <div className="absolute left-1/2 top-1/2 h-[120%] w-[120%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle_at_center,rgba(221,245,236,0.95)_0%,rgba(234,248,243,0.55)_45%,transparent_70%)]" />
        <div className="absolute -left-6 top-10 h-16 w-8 rotate-12 rounded-full bg-[#DDF5EC]/80" />
        <div className="absolute right-4 bottom-24 h-10 w-5 -rotate-6 rounded-full bg-[#DDF5EC]/70" />
      </div>

      <div className="relative z-10 space-y-4 p-1 sm:p-2">
        {/* Desktop / tablet flow */}
        <div className="hidden md:grid md:grid-cols-[minmax(0,0.9fr)_auto_minmax(0,1.05fr)_auto_minmax(0,1fr)] md:items-center md:gap-2 lg:gap-3">
          <RxCard reduce={!!reduce} />
          <FlowConnector
            reduce={!!reduce}
            color="#0D9B78"
            pathId="hero-flow-a"
            className="hidden h-40 w-8 lg:block"
          />
          <MedCards reduce={!!reduce} />
          <FlowConnector
            reduce={!!reduce}
            color="#2563EB"
            pathId="hero-flow-b"
            className="hidden h-48 w-8 lg:block"
            multi
          />
          <CheckCards reduce={!!reduce} />
        </div>

        {/* Mobile vertical flow */}
        <div className="flex flex-col gap-3 md:hidden">
          <RxCard reduce={!!reduce} />
          <MobileArrow />
          <MedCards reduce={!!reduce} />
          <MobileArrow />
          <CheckCards reduce={!!reduce} />
        </div>

        <WorkflowBar reduce={!!reduce} />

        <p className="text-center text-[10px] font-medium uppercase tracking-wide text-[#82918F]">
          Illustrative demo flow — not a patient result
        </p>
      </div>
    </div>
  )
}

function RxCard({ reduce }: { reduce: boolean }) {
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 14, rotate: -4 }}
      animate={{ opacity: 1, y: 0, rotate: -2 }}
      transition={{ duration: 0.45, ease: 'easeOut' }}
      className="relative rounded-2xl border border-[#DCE8E4] bg-white p-4 shadow-[0_10px_28px_rgba(7,83,77,0.08)] md:origin-center"
    >
      <div className="mb-3 flex items-start justify-between gap-2">
        <span className="font-serif text-2xl font-bold leading-none text-[#07534D]">℞</span>
        <span className="rounded-md border border-[#DCE8E4] bg-[#F8FBFA] px-1.5 py-0.5 text-[9px] font-medium text-[#64748B]">
          Demo Rx
        </span>
      </div>
      <div className="mb-3 space-y-1.5" aria-hidden>
        <div className="h-1.5 w-3/4 rounded-full bg-[#EAF8F3]" />
        <div className="h-1.5 w-1/2 rounded-full bg-[#EAF8F3]" />
      </div>
      <ul className="space-y-2">
        {MEDS.map((m) => (
          <li
            key={m.rxLine}
            className="rounded-lg border border-[#DCE8E4] bg-[#F8FBFA] px-2.5 py-1.5 font-mono text-[11px] font-medium text-[#123C38]"
          >
            {m.rxLine}
          </li>
        ))}
      </ul>
      <p className="mt-3 text-[10px] text-[#82918F]">Illustrative sample lines</p>
    </motion.div>
  )
}

function MedCards({ reduce }: { reduce: boolean }) {
  return (
    <div className="flex flex-col gap-2.5">
      {MEDS.map((m, i) => (
        <motion.div
          key={m.brand}
          initial={reduce ? false : { opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: reduce ? 0 : 0.15 + i * 0.08, duration: 0.35 }}
          className="flex items-center gap-3 rounded-xl border border-[#DCE8E4] bg-white px-3 py-2.5 shadow-sm"
        >
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#DDF5EC]">
            <Pill className="h-4 w-4 text-[#0D9B78]" strokeWidth={2} aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-[#123C38]">{m.brand}</p>
            <p className="truncate text-[11px] text-[#64748B]">{m.ingredients}</p>
          </div>
        </motion.div>
      ))}
    </div>
  )
}

function CheckCards({ reduce }: { reduce: boolean }) {
  return (
    <div className="flex flex-col gap-2.5">
      {CHECKS.map((c, i) => {
        const Icon = c.icon
        return (
          <motion.div
            key={c.title}
            initial={reduce ? false : { opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: reduce ? 0 : 0.28 + i * 0.08, duration: 0.35 }}
            className={`rounded-xl border ${c.border} ${c.bg} px-3 py-2.5`}
          >
            <div className="flex items-start gap-2.5">
              <span
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${c.iconBg}`}
              >
                <Icon className={`h-4 w-4 ${c.iconColor}`} strokeWidth={2} aria-hidden />
              </span>
              <div className="min-w-0">
                <p className={`text-xs font-semibold ${c.titleColor}`}>{c.title}</p>
                <p className="mt-0.5 text-[11px] leading-snug text-[#64748B]">{c.description}</p>
              </div>
            </div>
          </motion.div>
        )
      })}
    </div>
  )
}

function FlowConnector({
  reduce,
  color,
  pathId,
  className,
  multi,
}: {
  reduce: boolean
  color: string
  pathId: string
  className?: string
  multi?: boolean
}) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 160"
      fill="none"
      aria-hidden
      preserveAspectRatio="none"
    >
      {multi ? (
        <>
          <path
            d="M2 28 C14 28, 14 28, 30 28"
            stroke={color}
            strokeWidth="1.5"
            strokeOpacity="0.45"
            id={`${pathId}-1`}
          />
          <path
            d="M2 80 C14 80, 18 80, 30 80"
            stroke="#0D9B78"
            strokeWidth="1.5"
            strokeOpacity="0.5"
            id={`${pathId}-2`}
          />
          <path
            d="M2 132 C14 132, 14 132, 30 132"
            stroke="#15803D"
            strokeWidth="1.5"
            strokeOpacity="0.45"
            id={`${pathId}-3`}
          />
          {!reduce && (
            <>
              <MovingDot pathHref={`#${pathId}-1`} color={color} dur="2.8s" />
              <MovingDot pathHref={`#${pathId}-2`} color="#0D9B78" dur="3.2s" begin="0.4s" />
              <MovingDot pathHref={`#${pathId}-3`} color="#15803D" dur="3s" begin="0.8s" />
            </>
          )}
        </>
      ) : (
        <>
          <path
            d="M2 40 C12 40, 12 80, 30 80 C12 80, 12 120, 2 120"
            stroke={color}
            strokeWidth="1.5"
            strokeOpacity="0.4"
            fill="none"
            id={pathId}
          />
          <path
            d="M4 80 H28"
            stroke={color}
            strokeWidth="1.5"
            strokeOpacity="0.55"
            id={`${pathId}-mid`}
          />
          {!reduce && (
            <>
              <MovingDot pathHref={`#${pathId}-mid`} color={color} dur="2.4s" />
            </>
          )}
        </>
      )}
    </svg>
  )
}

function MovingDot({
  pathHref,
  color,
  dur,
  begin = '0s',
}: {
  pathHref: string
  color: string
  dur: string
  begin?: string
}) {
  return (
    <circle r="2.5" fill={color}>
      <animateMotion dur={dur} begin={begin} repeatCount="indefinite" rotate="auto">
        <mpath href={pathHref} />
      </animateMotion>
    </circle>
  )
}

function MobileArrow() {
  return (
    <div className="flex justify-center text-[#0D9B78]" aria-hidden>
      <ArrowRight className="h-4 w-4 rotate-90" strokeWidth={2} />
    </div>
  )
}

function WorkflowBar({ reduce }: { reduce: boolean }) {
  return (
    <motion.div
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: reduce ? 0 : 0.45, duration: 0.35 }}
      className="flex flex-wrap items-center justify-center gap-x-2 gap-y-2 rounded-full border border-[#DCE8E4] bg-white/90 px-3 py-2.5 shadow-sm backdrop-blur-sm"
    >
      {WORKFLOW.map((step, i) => {
        const Icon = step.icon
        return (
          <div key={step.label} className="flex items-center gap-1.5">
            {i > 0 && (
              <ArrowRight
                className="mx-0.5 hidden h-3.5 w-3.5 text-[#0D9B78] sm:inline"
                strokeWidth={2}
                aria-hidden
              />
            )}
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#EAF8F3] px-2.5 py-1 text-[11px] font-medium text-[#123C38]">
              <Icon className="h-3.5 w-3.5 text-[#0D9B78]" strokeWidth={2} aria-hidden />
              {step.label}
            </span>
          </div>
        )
      })}
    </motion.div>
  )
}
