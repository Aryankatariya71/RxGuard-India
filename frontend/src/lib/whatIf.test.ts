import { describe, expect, it } from 'vitest'
import { defaultActiveKeys, filterPrescriptionText, lineKey } from './whatIf'

describe('what-if filter', () => {
  const rx = 'Tab A OD\nTab B BD\nTab C TDS'

  it('defaults all lines active', () => {
    const keys = defaultActiveKeys(rx)
    expect(keys.size).toBe(3)
  })

  it('recomputes text with excluded medicines', () => {
    const keys = defaultActiveKeys(rx)
    keys.delete(lineKey('Tab B BD', 1))
    const { text, excludedCount, total } = filterPrescriptionText(rx, keys)
    expect(total).toBe(3)
    expect(excludedCount).toBe(1)
    expect(text).toBe('Tab A OD\nTab C TDS')
    expect(text.includes('Tab B')).toBe(false)
  })
})
