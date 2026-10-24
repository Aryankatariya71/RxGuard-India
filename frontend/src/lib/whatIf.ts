/** What-if helpers: filter prescription lines by active medicine keys. */

export function lineKey(line: string, index: number): string {
  return `${index}::${line.trim()}`
}

export function filterPrescriptionText(
  fullText: string,
  activeKeys: Set<string>,
): { text: string; excludedCount: number; total: number } {
  const lines = (fullText || '').split('\n')
  const kept: string[] = []
  let total = 0
  lines.forEach((line, i) => {
    const t = line.trim()
    if (!t) return
    total += 1
    const key = lineKey(line, i)
    if (activeKeys.has(key)) kept.push(line)
  })
  return {
    text: kept.join('\n'),
    excludedCount: Math.max(0, total - kept.length),
    total,
  }
}

export function defaultActiveKeys(fullText: string): Set<string> {
  const set = new Set<string>()
  ;(fullText || '').split('\n').forEach((line, i) => {
    if (line.trim()) set.add(lineKey(line, i))
  })
  return set
}
