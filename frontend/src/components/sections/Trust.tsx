import { BookOpen, FlaskConical, Info, ShieldAlert } from 'lucide-react'

export function Trust() {
  return (
    <section id="trust" className="no-print bg-[#F1F7F5] py-14 sm:py-16">
      <div className="rx-container">
        <h2 className="text-3xl font-bold tracking-tight text-[#123C38] sm:text-4xl">
          Trust & limitations
        </h2>
        <p className="rx-prose mt-3 text-[#64748B]">
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
              title: 'Catalogue gaps',
              body: 'Some multi-ingredient brands are not fully representable in current dataset fields.',
            },
            {
              icon: BookOpen,
              title: 'Decision support only',
              body: 'Not a medical device. Does not replace a clinician or pharmacist.',
            },
          ].map(({ icon: Icon, title, body }) => (
            <div key={title} className="rx-card p-5">
              <Icon className="h-5 w-5 text-[#B45309]" strokeWidth={2} aria-hidden />
              <h3 className="mt-3 font-semibold text-[#123C38]">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#64748B]">{body}</p>
            </div>
          ))}
        </div>

        <div className="rx-card mt-6 flex gap-3 border-[#BFDBFE] bg-[#EFF6FF]/60 p-5">
          <Info className="mt-0.5 h-5 w-5 shrink-0 text-[#1D4ED8]" strokeWidth={2} aria-hidden />
          <div className="text-sm leading-relaxed text-[#334155]">
            <p className="font-semibold text-[#123C38]">Medical safety disclaimer</p>
            <p className="mt-1 text-[#64748B]">
              RxGuard India supports prescription review and decision-making. It does not replace
              professional medical advice. Always consult a qualified healthcare professional about
              medicine-related concerns.
            </p>
          </div>
        </div>

        <div className="rx-card mt-4 p-5 text-sm text-[#64748B]">
          <strong className="text-[#123C38]">Data sources:</strong> A–Z Medicines Dataset of India
          (Kaggle); DDInter 2.0 (academic use).
        </div>
      </div>
    </section>
  )
}
