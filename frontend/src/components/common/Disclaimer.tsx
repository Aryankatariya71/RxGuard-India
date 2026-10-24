import { SHORT, FULL } from '../../lib/copy'

export function BannerDisclaimer({ short = false }: { short?: boolean }) {
  return (
    <aside className="disclaimer" role="note">
      {short ? SHORT : FULL}
    </aside>
  )
}
