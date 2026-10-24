import { motion, useReducedMotion } from 'framer-motion'
import {
  AlertTriangle,
  ClipboardList,
  FileSearch,
  Layers,
  Pill,
  Search,
} from 'lucide-react'

const CAPS = [
  {
    icon: ClipboardList,
    title: 'Prescription review',
    body: 'Parse free-text Indian Rx lines into structured brand, frequency, and duration fields.',
  },
  {
    icon: Layers,
    title: 'Ingredient duplication checks',
    body: 'Detect the same active ingredient appearing across multiple brands on one prescription.',
  },
  {
    icon: AlertTriangle,
    title: 'Possible interaction checks',
    body: 'Flag curated and class-based interaction pairs with rule IDs and source labels.',
  },
  {
    icon: Pill,
    title: 'Dosage information review',
    body: 'Sum daily dose per ingredient and compare against draft limits where configured.',
  },
  {
    icon: Search,
    title: 'Medicine information lookup',
    body: 'Search the local catalogue and explore brands that share an ingredient.',
  },
  {
    icon: FileSearch,
    title: 'Explainable safety findings',
    body: 'Every alert shows what was found, suggested next steps, and evidence details.',
  },
]

export function Capabilities() {
  const reduce = useReducedMotion()
  return (
    <section id="capabilities" className="no-print bg-[#F1F7F5] py-14 sm:py-16">
      <div className="rx-container">
        <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
          Key capabilities
        </h2>
        <p className="rx-prose mt-3 text-[#64748B]">
          Features implemented in this product. Coverage depends on catalogue data and draft rules —
          not every medicine or interaction is guaranteed.
        </p>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CAPS.map((c, i) => {
            const Icon = c.icon
            return (
              <motion.article
                key={c.title}
                initial={reduce ? false : { opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-30px' }}
                transition={{ delay: i * 0.04 }}
                className="rx-card rx-card-hover p-5"
              >
                <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#DDF5EC] text-[#087F6E]">
                  <Icon className="h-5 w-5" strokeWidth={2} aria-hidden />
                </span>
                <h3 className="mt-4 font-semibold text-[#123C38]">{c.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#64748B]">{c.body}</p>
              </motion.article>
            )
          })}
        </div>
      </div>
    </section>
  )
}
