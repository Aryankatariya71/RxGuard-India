import { Link } from 'react-router-dom'
import { ShieldCheck } from 'lucide-react'

export function Footer() {
  return (
    <footer className="no-print border-t border-[#DCE8E4] bg-[#07534D] text-[#F0FDFA]">
      <div className="rx-container grid gap-10 py-12 md:grid-cols-[1.4fr_1fr_1fr]">
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#0D9B78]">
              <ShieldCheck className="h-5 w-5 text-white" strokeWidth={2} aria-hidden />
            </span>
            <span className="text-base font-semibold text-white">RxGuard India</span>
          </div>
          <p className="mt-4 max-w-sm text-sm leading-relaxed text-[#D1FAE5]">
            Prescription safety and medicine intelligence — help understand risks, duplicate
            ingredients, and possible interactions with explainable findings.
          </p>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#D1FAE5]">Product</p>
          <ul className="mt-3 space-y-2 text-sm">
            <li>
              <a href="/#checker" className="text-[#F0FDFA] hover:text-white">
                Check prescription
              </a>
            </li>
            <li>
              <a href="/#how-it-works" className="text-[#F0FDFA] hover:text-white">
                How it works
              </a>
            </li>
            <li>
              <Link to="/ingredients" className="text-[#F0FDFA] hover:text-white">
                Medicines
              </Link>
            </li>
            <li>
              <Link to="/stress-test" className="text-[#F0FDFA] hover:text-white">
                Stress test
              </Link>
            </li>
            <li>
              <Link to="/methodology" className="text-[#F0FDFA] hover:text-white">
                Methodology
              </Link>
            </li>
            <li>
              <Link to="/about" className="text-[#F0FDFA] hover:text-white">
                About
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-[#D1FAE5]">Important</p>
          <p className="mt-3 text-sm leading-relaxed text-[#D1FAE5]">
            RxGuard India supports prescription review and decision-making. It does not replace
            professional medical advice. Always consult a qualified healthcare professional about
            medicine-related concerns.
          </p>
        </div>
      </div>

      <div className="border-t border-white/10">
        <div className="rx-container flex flex-col gap-2 py-4 text-xs text-[#A7F3D0] sm:flex-row sm:items-center sm:justify-between">
          <p>Decision support only · Rules are DRAFT · Not a medical device</p>
          <p>© {new Date().getFullYear()} RxGuard India</p>
        </div>
      </div>
    </footer>
  )
}
