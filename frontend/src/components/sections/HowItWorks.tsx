import { motion, useReducedMotion } from 'framer-motion'
import { ClipboardList, FileText, Stethoscope } from 'lucide-react'

const STEPS = [
  {
    icon: ClipboardList,
    title: 'Enter a prescription',
    body: 'Paste free-text Rx lines, load a sample, or use voice and scan tools where available.',
  },
  {
    icon: FileText,
    title: 'Review possible safety concerns',
    body: 'The rules engine checks duplicates, dose totals, and curated interaction pairs with cited sources.',
  },
  {
    icon: Stethoscope,
    title: 'Discuss findings with a professional',
    body: 'Use patient-friendly explanations and evidence details to inform a conversation with a clinician or pharmacist.',
  },
]

export function HowItWorks() {
  const reduce = useReducedMotion()
  return (
    <section id="how-it-works" className="no-print border-t border-[#DCE8E4] bg-white py-14 sm:py-16">
      <div className="rx-container">
        <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
          How RxGuard India works
        </h2>
        <p className="rx-prose mt-3 text-[#64748B]">
          A structured review workflow — not unexplained warning labels.
        </p>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {STEPS.map((s, i) => {
            const Icon = s.icon
            return (
              <motion.div
                key={s.title}
                initial={reduce ? false : { opacity: 0, y: 14 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ delay: i * 0.06 }}
                className="rx-card rx-card-hover p-6"
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#DDF5EC] text-[#087F6E]">
                    <Icon className="h-5 w-5" strokeWidth={2} aria-hidden />
                  </span>
                  <span className="text-xs font-semibold uppercase tracking-wider text-[#0D9B78]">
                    Step {i + 1}
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-semibold text-[#123C38]">{s.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#64748B]">{s.body}</p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
