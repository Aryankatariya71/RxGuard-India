import { Link } from 'react-router-dom'
import { BookOpen, ShieldCheck } from 'lucide-react'
import { AppLayout } from '../components/layout/AppLayout'
import { ErrorBoundary } from '../components/common/ErrorBoundary'

const DISCLAIMER =
  'RxGuard India is a prescription-review support prototype. It does not replace a doctor or pharmacist. A missing alert does not prove a prescription is safe. Verify findings with a qualified healthcare professional.'

export function AboutPage() {
  return (
    <AppLayout title="About" subtitle="What RxGuard India is — and is not">
      <ErrorBoundary label="About page">
        <div className="rx-container max-w-3xl py-10" data-testid="about-page">
          <p className="inline-flex items-center gap-2 rounded-full border border-[#DCE8E4] bg-[#DDF5EC] px-3 py-1 text-xs font-medium text-[#123C38]">
            <ShieldCheck className="h-3.5 w-3.5 text-[#0D9B78]" aria-hidden />
            Decision support prototype
          </p>
          <h1 className="mt-4 text-3xl font-bold tracking-tight text-[#123C38]">About RxGuard India</h1>
          <p className="mt-4 text-[#334155] leading-relaxed">
            RxGuard India helps review Indian brand-name prescriptions by resolving medicines to
            ingredients, summing daily doses, and running deterministic duplicate, dose, and
            interaction checks with cited draft rules.
          </p>
          <p className="mt-3 text-[#64748B] leading-relaxed">
            It is not a medical device, does not claim clinical validation, and does not replace a
            doctor or pharmacist.
          </p>

          <div className="rx-card mt-8 space-y-3 p-5">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-[#123C38]">
              <BookOpen className="h-5 w-5 text-[#0D9B78]" aria-hidden />
              Methodology
            </h2>
            <p className="text-sm text-[#64748B]">
              For judges, pharmacists, and engineers: pipeline details, live catalogue and rule
              counts, evaluation notes, limitations, and how to reproduce.
            </p>
            <Link
              to="/methodology"
              className="btn-primary inline-flex items-center px-4 py-2.5 text-sm text-white"
              data-testid="about-methodology-link"
            >
              Read the methodology
            </Link>
          </div>

          <div className="mt-8 rounded-2xl border border-[#FED7AA] bg-[#FFF7ED] px-4 py-3 text-sm text-[#B45309]">
            {DISCLAIMER}
          </div>

          <p className="mt-6 text-sm text-[#64748B]">
            <Link to="/" className="text-[#087F6E] hover:underline">
              Back to checker
            </Link>
          </p>
        </div>
      </ErrorBoundary>
    </AppLayout>
  )
}

export default AboutPage
