/** Lightweight client-side preview — not the Python parser. */

import {
  findSpokenFrequencyMatches,
  interpretedFrequencyForLine,
} from './spokenFrequency'

const FREQ: Record<string, { label: string; perDay: number }> = {
  od: { label: 'OD = 1/day', perDay: 1 },
  bd: { label: 'BD = 2/day', perDay: 2 },
  bid: { label: 'BID = 2/day', perDay: 2 },
  tds: { label: 'TDS = 3/day', perDay: 3 },
  tid: { label: 'TID = 3/day', perDay: 3 },
  qid: { label: 'QID = 4/day', perDay: 4 },
  hs: { label: 'HS = 1/day', perDay: 1 },
  sos: { label: 'SOS (PRN)', perDay: 0 },
  prn: { label: 'PRN', perDay: 0 },
  ac: { label: 'AC (before food)', perDay: -1 },
  pc: { label: 'PC (after food)', perDay: -1 },
}

export interface PreviewLine {
  raw: string
  brandText: string
  frequency?: string
  duration?: string
  /** Spoken / Hindi phrase interpretation for confirmation. */
  interpretedFrequency?: string
  timing?: string
}

export function parsePreview(text: string): PreviewLine[] {
  return text
    .split(/\n/)
    .map((l) => l.trim())
    .filter(Boolean)
    .map((raw) => {
      const lower = raw.toLowerCase()
      let frequency: string | undefined
      let timing: string | undefined
      const patternHit = lower.match(/\b(\d(?:-\d){1,3})\b/)
      if (patternHit) {
        const parts = patternHit[1].split('-').map(Number)
        const sum = parts.reduce((a, b) => a + b, 0)
        frequency = `${patternHit[1]} = ${sum}/day`
      } else {
        for (const [k, v] of Object.entries(FREQ)) {
          if (v.perDay < 0) continue
          if (new RegExp(`\\b${k}\\b`, 'i').test(lower)) {
            frequency = v.label
            break
          }
        }
      }
      for (const [k, v] of Object.entries(FREQ)) {
        if (v.perDay >= 0) continue
        if (new RegExp(`\\b${k}\\b`, 'i').test(lower)) {
          timing = v.label
          break
        }
      }

      const spoken = findSpokenFrequencyMatches(raw)
      const spokenFreq = spoken.find((m) => m.kind === 'frequency')
      const spokenTiming = spoken.find((m) => m.kind === 'timing')
      if (!frequency && spokenFreq) frequency = spokenFreq.label
      if (!timing && spokenTiming) timing = spokenTiming.label

      const interpretedFrequency =
        interpretedFrequencyForLine(raw) ||
        (frequency ? `Interpreted: ${frequency}` : undefined)

      const dur = lower.match(/\bx\s*(\d+)\s*(day|days|d)\b/)
      const duration = dur ? `${dur[1]} days` : undefined

      let brandText = raw
        .replace(/^(tab|tablet|cap|capsule|syp|syrup|susp|inj)\s+/i, '')
        .replace(/\b(od|bd|bid|tds|tid|qid|hs|sos|prn|ac|pc)\b/gi, '')
        .replace(/\b\d(?:-\d){1,3}\b/, '')
        .replace(/\bx\s*\d+\s*(day|days|d)\b/gi, '')
        .replace(/\s+/g, ' ')
        .trim()

      // Strip known spoken phrases from brand preview
      for (const m of spoken) {
        brandText = brandText.replace(new RegExp(m.phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'ig'), '')
      }
      brandText = brandText.replace(/\s+/g, ' ').trim()

      if (!brandText) brandText = raw

      return { raw, brandText, frequency, duration, interpretedFrequency, timing }
    })
}

export function patientSummary(p: {
  age_years: number
  weight_kg: number | null
  sex: string
  kidney: string
  pregnant: boolean
}): string {
  const age = Math.round(p.age_years)
  const sexWord =
    p.sex === 'M' ? 'man' : p.sex === 'F' ? 'woman' : 'patient'
  const ageLabel =
    age < 1
      ? 'infant'
      : age < 12
        ? `${age}-year-old child`
        : age < 18
          ? `${age}-year-old adolescent`
          : `${age}-year-old ${sexWord}`
  const wt = p.weight_kg != null && p.weight_kg > 0 ? `, ${p.weight_kg} kg` : ''
  const kidneyMap: Record<string, string> = {
    normal: 'normal kidney function',
    mild_moderate: 'mild–moderate kidney impairment',
    severe: 'severe kidney impairment',
    unknown: 'unknown kidney function',
  }
  const kid = kidneyMap[p.kidney] || 'unknown kidney function'
  const preg = p.pregnant ? ', pregnant' : ''
  return `${ageLabel}${wt}, ${kid}${preg}`
}
