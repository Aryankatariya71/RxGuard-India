import { motion, useReducedMotion } from 'framer-motion'
import { BookOpen, MessageCircle, Scale, ShieldCheck } from 'lucide-react'

const POINTS = [
  {
    icon: MessageCircle,
    title: 'Clear explanations',
    body: 'Findings use patient-friendly language — what we found, why it matters, and what to do next.',
  },
  {
    icon: BookOpen,
    title: 'Source and verification',
    body: 'Alerts cite rule IDs and source labels. Demo-only rules are labeled so evidence stays honest.',
  },
  {
    icon: Scale,
    title: 'Less alert noise',
    body: 'Duplicate and dose findings can merge; identical interaction pairs collapse so critical items surface first.',
  },
  {
    icon: ShieldCheck,
    title: 'Structured review workflow',
    body: 'From Rx text to resolved ingredients, daily dose totals, and tiered safety cards in one place.',
  },
]

export function WhyRxGuard() {
  const reduce = useReducedMotion()
  return (
    <section id="why" className="no-print border-t border-[#DCE8E4] bg-white py-14 sm:py-16">
      <div className="rx-container">
        <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
          Why RxGuard India
        </h2>
        <p className="rx-prose mt-3 text-[#64748B]">
          Built for clarity and accountability — not black-box scores or unsupported guarantees.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {POINTS.map((p, i) => {
            const Icon = p.icon
            return (
              <motion.div
                key={p.title}
                initial={reduce ? false : { opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.05 }}
                className="rx-card flex gap-4 p-5"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#DDF5EC] text-[#087F6E]">
                  <Icon className="h-5 w-5" strokeWidth={2} aria-hidden />
                </span>
                <div>
                  <h3 className="font-semibold text-[#123C38]">{p.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-[#64748B]">{p.body}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
