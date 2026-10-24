/**
 * Illustrative 24h dose timeline builder.
 * Clock times are illustrative mappings of written frequencies — not medical advice.
 */

import type { Alert, DailyIngredient, LineItem } from '../api/types'

export type ClockHour =
  | 8
  | 9
  | 10
  | 12
  | 14
  | 16
  | 21
  | 22

export interface TimelineDose {
  brand: string
  line?: string
  hour: number
  label: string
  colorIndex: number
}

export interface CumulativePoint {
  hour: number
  /** Cumulative mg by end of this hour (0–24) */
  cumulativeMg: number
}

export interface IngredientTimelineSeries {
  ingredient: string
  unit: string
  totalMgDay: number
  limitMgDay: number | null
  points: CumulativePoint[]
  crossesLimit: boolean
}

export interface TimelineResult {
  doses: TimelineDose[]
  series: IngredientTimelineSeries[]
  unclear: { brand: string; reason: string }[]
  caption: string
}

const CAPTION =
  'Illustrative schedule based on the written frequency. Actual timing may differ.'

/** Map frequency codes / patterns → illustrative clock hours */
export function frequencyToHours(
  frequencyCode: string | null | undefined,
  opts?: { prn?: boolean; timesPerDay?: number | null },
): number[] | 'unclear' {
  if (opts?.prn) return 'unclear'
  const raw = (frequencyCode || '').trim().toUpperCase().replace(/\./g, '')
  if (!raw) {
    if (opts?.timesPerDay != null && opts.timesPerDay > 0) {
      // Fallback only when we know times/day but not pattern — still unclear for clock
      return 'unclear'
    }
    return 'unclear'
  }

  // Pattern schedules like 1-0-1, 1-1-1, 1-1-1-1
  if (/^[\d./]+(?:-[\d./]+)+$/.test(raw) || /^\d+(?:-\d+)+$/.test(frequencyCode || '')) {
    const parts = (frequencyCode || raw).split('-').map((p) => p.trim())
    if (parts.length === 2) {
      // morning-evening style
      const hours: number[] = []
      if (parseDoseToken(parts[0]) > 0) hours.push(8)
      if (parseDoseToken(parts[1]) > 0) hours.push(21)
      return hours.length ? hours : 'unclear'
    }
    if (parts.length === 3) {
      // 1-0-1 → 8am, 9pm; 1-1-1 → 8am, 2pm, 9pm
      const hours: number[] = []
      if (parseDoseToken(parts[0]) > 0) hours.push(8)
      if (parseDoseToken(parts[1]) > 0) hours.push(14)
      if (parseDoseToken(parts[2]) > 0) hours.push(21)
      return hours.length ? hours : 'unclear'
    }
    if (parts.length === 4) {
      const hours: number[] = []
      if (parseDoseToken(parts[0]) > 0) hours.push(8)
      if (parseDoseToken(parts[1]) > 0) hours.push(12)
      if (parseDoseToken(parts[2]) > 0) hours.push(16)
      if (parseDoseToken(parts[3]) > 0) hours.push(21)
      return hours.length ? hours : 'unclear'
    }
    return 'unclear'
  }

  switch (raw) {
    case '1-0-1':
      return [8, 21]
    case '1-1-1':
    case 'TDS':
    case 'TID':
      return [8, 14, 21]
    case 'BD':
    case 'BID':
      return [8, 21]
    case 'OD':
    case 'QD':
      return [8]
    case 'QID':
    case 'QDS':
      return [8, 12, 16, 21]
    case 'HS':
      return [22]
    case 'SOS':
    case 'PRN':
    case 'STAT':
      return 'unclear'
    default:
      return 'unclear'
  }
}

function parseDoseToken(tok: string): number {
  if (!tok || tok === '0') return 0
  if (tok.includes('/')) {
    const [a, b] = tok.split('/').map(Number)
    if (b) return a / b
  }
  const n = Number(tok)
  return Number.isFinite(n) ? n : 0
}

function hourLabel(h: number): string {
  if (h === 0) return '12am'
  if (h < 12) return `${h}am`
  if (h === 12) return '12pm'
  return `${h - 12}pm`
}

const PALETTE = ['#14b8a6', '#818cf8', '#f472b6', '#fbbf24', '#38bdf8', '#a78bfa']

export function buildTimeline(
  items: LineItem[],
  daily: DailyIngredient[],
  alerts: Alert[],
): TimelineResult {
  const unclear: { brand: string; reason: string }[] = []
  const doses: TimelineDose[] = []
  let colorIndex = 0
  const brandColor = new Map<string, number>()

  for (const item of items) {
    if (!item.resolved) continue
    const brand = item.matched_brand || item.line || 'Unknown'
    const code = item.frequency_code as string | undefined
    const prn = Boolean(item.prn)
    const hours = frequencyToHours(code, {
      prn,
      timesPerDay: item.times_per_day as number | null | undefined,
    })
    if (hours === 'unclear') {
      unclear.push({
        brand,
        reason: prn || (code || '').toUpperCase() === 'SOS'
          ? 'SOS/PRN — no fixed schedule'
          : 'schedule unclear or ambiguous',
      })
      continue
    }
    if (!brandColor.has(brand)) {
      brandColor.set(brand, colorIndex++ % PALETTE.length)
    }
    const ci = brandColor.get(brand)!
    for (const hour of hours) {
      doses.push({
        brand,
        line: item.line,
        hour,
        label: hourLabel(hour),
        colorIndex: ci,
      })
    }
  }

  doses.sort((a, b) => a.hour - b.hour || a.brand.localeCompare(b.brand))

  // Ingredient series: only those in 2+ products OR with a stored rule limit
  const limitByIng = new Map<string, number>()
  for (const a of alerts || []) {
    if (a.limit_mg_day != null && a.ingredients?.[0]) {
      limitByIng.set(a.ingredients[0].toLowerCase(), Number(a.limit_mg_day))
    }
  }

  const series: IngredientTimelineSeries[] = []
  for (const d of daily || []) {
    const productCount = new Set((d.contributions || []).map((c) => c.brand)).size
    const limit = limitByIng.get(d.ingredient.toLowerCase()) ?? null
    if (productCount < 2 && limit == null) continue

    const total = Number(d.total_mg_per_day) || 0
    // Spread cumulative evenly across day hours that have any dose, else linear 0→24
    const doseHours = [...new Set(doses.map((x) => x.hour))].sort((a, b) => a - b)
    const points: CumulativePoint[] = [{ hour: 0, cumulativeMg: 0 }]
    if (doseHours.length === 0) {
      points.push({ hour: 24, cumulativeMg: total })
    } else {
      let cum = 0
      const perStep = total / doseHours.length
      for (const h of doseHours) {
        cum += perStep
        points.push({ hour: h, cumulativeMg: Math.round(cum * 10) / 10 })
      }
      if (points[points.length - 1].hour < 24) {
        points.push({ hour: 24, cumulativeMg: total })
      }
    }
    const crosses = limit != null && total > limit
    series.push({
      ingredient: d.ingredient,
      unit: d.unit || 'mg',
      totalMgDay: total,
      limitMgDay: limit,
      points,
      crossesLimit: crosses,
    })
  }

  return { doses, series, unclear, caption: CAPTION }
}

export function timelineColor(index: number): string {
  return PALETTE[index % PALETTE.length]
}
