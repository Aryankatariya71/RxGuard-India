/**
 * Hindi / English spoken-frequency phrases → standard Rx codes.
 * Client-side only; always show the interpreted code for confirmation.
 */

export interface SpokenFreqMatch {
  phrase: string
  code: string
  label: string
  kind: 'frequency' | 'timing'
}

const RULES: { pattern: RegExp; code: string; label: string; kind: SpokenFreqMatch['kind'] }[] = [
  { pattern: /\bsubah\s*(?:aur\s*)?shaam\b/gi, code: '1-0-1', label: '1-0-1 (subah shaam)', kind: 'frequency' },
  { pattern: /\bshaam\s*(?:aur\s*)?subah\b/gi, code: '1-0-1', label: '1-0-1 (subah shaam)', kind: 'frequency' },
  { pattern: /\bmorning\s+and\s+evening\b/gi, code: '1-0-1', label: '1-0-1 (morning and evening)', kind: 'frequency' },
  { pattern: /\bteen\s+baar\b/gi, code: 'TDS', label: 'TDS (teen baar)', kind: 'frequency' },
  { pattern: /\bthree\s+times\b/gi, code: 'TDS', label: 'TDS (three times)', kind: 'frequency' },
  { pattern: /\bdo\s+baar\b/gi, code: 'BD', label: 'BD (do baar)', kind: 'frequency' },
  { pattern: /\btwice\s+(?:a\s+)?day\b/gi, code: 'BD', label: 'BD (twice a day)', kind: 'frequency' },
  { pattern: /\bek\s+baar\b/gi, code: 'OD', label: 'OD (ek baar)', kind: 'frequency' },
  { pattern: /\bonce\s+(?:a\s+)?day\b/gi, code: 'OD', label: 'OD (once a day)', kind: 'frequency' },
  { pattern: /\braat\s+ko\b/gi, code: 'HS', label: 'HS (raat ko)', kind: 'frequency' },
  { pattern: /\bat\s+night\b/gi, code: 'HS', label: 'HS (at night)', kind: 'frequency' },
  { pattern: /\bchaar\s+baar\b/gi, code: 'QID', label: 'QID (chaar baar)', kind: 'frequency' },
  { pattern: /\bfour\s+times\b/gi, code: 'QID', label: 'QID (four times)', kind: 'frequency' },
  { pattern: /\bkhali\s+pet\b/gi, code: 'AC', label: 'AC (khali pet)', kind: 'timing' },
  { pattern: /\bbefore\s+(?:food|meals?)\b/gi, code: 'AC', label: 'AC (before food)', kind: 'timing' },
  { pattern: /\bkhane\s+ke\s+baad\b/gi, code: 'PC', label: 'PC (khane ke baad)', kind: 'timing' },
  { pattern: /\bafter\s+(?:food|meals?)\b/gi, code: 'PC', label: 'PC (after food)', kind: 'timing' },
]

export function findSpokenFrequencyMatches(text: string): SpokenFreqMatch[] {
  const out: SpokenFreqMatch[] = []
  const seen = new Set<string>()
  for (const rule of RULES) {
    rule.pattern.lastIndex = 0
    const m = text.match(rule.pattern)
    if (!m) continue
    const key = `${rule.kind}:${rule.code}:${m[0].toLowerCase()}`
    if (seen.has(key)) continue
    seen.add(key)
    out.push({
      phrase: m[0],
      code: rule.code,
      label: rule.label,
      kind: rule.kind,
    })
  }
  return out
}

/** Replace spoken phrases with standard codes for clearer confirmation. */
export function normalizeSpokenFrequencies(text: string): {
  text: string
  matches: SpokenFreqMatch[]
} {
  const matches = findSpokenFrequencyMatches(text)
  let next = text
  for (const rule of RULES) {
    rule.pattern.lastIndex = 0
    next = next.replace(rule.pattern, rule.code)
  }
  return { text: next.replace(/\s+/g, ' ').trim(), matches }
}

/** Prefer the primary frequency match for a single line. */
export function interpretedFrequencyForLine(line: string): string | undefined {
  const matches = findSpokenFrequencyMatches(line)
  const freq = matches.find((m) => m.kind === 'frequency')
  if (freq) return freq.label
  const timing = matches.find((m) => m.kind === 'timing')
  return timing?.label
}
