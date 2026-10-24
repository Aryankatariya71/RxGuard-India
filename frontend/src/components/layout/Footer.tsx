export function Footer() {
  return (
    <footer className="no-print border-t border-[var(--card-border)] py-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 text-sm text-[var(--muted)] sm:flex-row sm:items-center sm:justify-between sm:px-6">
        <p>
          <span className="font-semibold text-[var(--fg)]">RxGuard India</span>
          {' — '}
          Every brand. Every ingredient. Every risk. Explained.
        </p>
        <p>Decision support only · Rules are DRAFT</p>
      </div>
    </footer>
  )
}
