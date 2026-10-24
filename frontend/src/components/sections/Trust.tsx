import { BookOpen, FlaskConical, ShieldAlert } from 'lucide-react'

export function Trust() {
  return (
    <section className="no-print mx-auto max-w-7xl px-4 py-16 sm:px-6">
      <h2 className="text-3xl font-extrabold tracking-tight">Trust & limitations</h2>
      <p className="mt-3 max-w-2xl text-[var(--muted)]">
        Honest about what we know — and what still needs a pharmacist.
      </p>
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {[
          {
            icon: ShieldAlert,
            title: 'Draft rules',
            body: 'Dose limits and curated interactions are DRAFT pending pharmacist verification.',
          },
          {
            icon: FlaskConical,
            title: 'Catalog gaps',
            body: '3+ ingredient brands are not fully representable in the two-composition dataset fields.',
          },
          {
            icon: BookOpen,
            title: 'Decision support only',
            body: 'Not a medical device. Does not replace a clinician or pharmacist.',
          },
        ].map(({ icon: Icon, title, body }) => (
          <div key={title} className="glass rounded-2xl p-5">
            <Icon className="h-5 w-5 text-amber-300" aria-hidden />
            <h3 className="mt-3 font-bold">{title}</h3>
            <p className="mt-2 text-sm text-[var(--muted)]">{body}</p>
          </div>
        ))}
      </div>
      <div className="glass mt-6 rounded-2xl p-5 text-sm text-[var(--muted)]">
        <strong className="text-[var(--fg)]">Data sources:</strong> A–Z Medicines Dataset of India
        (Kaggle); DDInter 2.0 (academic use).
      </div>
    </section>
  )
}
