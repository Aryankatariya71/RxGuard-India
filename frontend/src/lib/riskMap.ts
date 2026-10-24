/** Build risk-map nodes/edges from real engine alerts + resolved items. */

import type { Alert, LineItem } from '../api/types'

export interface RiskNode {
  id: string
  label: string
  brands: string[]
}

export interface RiskEdge {
  id: string
  source: string
  target: string
  kind: 'interaction' | 'duplicate'
  tier: string
  dashed: boolean
  ruleId: string
  mechanism?: string
  sourceLabel: string
  version?: string
  status?: string
  title: string
  icon: 'alert' | 'link' | 'copy'
}

export interface RiskMapData {
  nodes: RiskNode[]
  edges: RiskEdge[]
  emptyMessage?: string
}

function norm(name: string): string {
  return name.trim().toLowerCase()
}

function pairKey(a: string, b: string): string {
  return [norm(a), norm(b)].sort().join('||')
}

function inferStatus(alert: Alert): string {
  const raw =
    (alert.status as string) ||
    (alert.rule_status as string) ||
    (alert.evidence_status as string) ||
    ''
  if (raw) return String(raw)
  const label = (alert.source_label || '').toLowerCase()
  if (label.includes('demo')) return 'DEMO_ILLUSTRATIVE'
  if (label.includes('ddinter') || label.includes('curated')) return 'REVIEW_PENDING'
  if (label.includes('clinically') || label.includes('pharmacist')) return 'CLINICALLY_REVIEWED'
  return 'REVIEW_PENDING'
}

function tierIcon(tier: string, kind: RiskEdge['kind']): RiskEdge['icon'] {
  if (kind === 'duplicate') return 'copy'
  if (tier === 'critical') return 'alert'
  return 'link'
}

/** Collect ingredient → brands from resolved line items. */
export function ingredientsFromItems(items: LineItem[]): Map<string, RiskNode> {
  const map = new Map<string, RiskNode>()
  for (const it of items) {
    if (!it.resolved) continue
    const brand = it.matched_brand || it.line || 'Unknown'
    for (const ing of it.ingredients || []) {
      const name = (ing.ingredient || '').trim()
      if (!name) continue
      const id = norm(name)
      const existing = map.get(id)
      if (existing) {
        if (!existing.brands.includes(brand)) existing.brands.push(brand)
      } else {
        map.set(id, { id, label: name, brands: [brand] })
      }
    }
  }
  return map
}

export function buildRiskMap(items: LineItem[], alerts: Alert[]): RiskMapData {
  const nodeMap = ingredientsFromItems(items)
  const edges: RiskEdge[] = []
  const seen = new Set<string>()

  for (const alert of alerts || []) {
    const type = (alert.type || '').toLowerCase()
    const ings = (alert.ingredients || []).map((x) => String(x).trim()).filter(Boolean)
    const isDup = type.includes('duplicate')
    const isInt = type.includes('interaction')
    if (!isDup && !isInt) continue

    // Prefer pairs from ingredients list; for duplicates may be 1 ingredient across brands
    if (isDup && ings.length === 1) {
      const id = norm(ings[0])
      if (!nodeMap.has(id)) {
        nodeMap.set(id, {
          id,
          label: ings[0],
          brands: alert.brands || [],
        })
      } else {
        const n = nodeMap.get(id)!
        for (const b of alert.brands || []) {
          if (!n.brands.includes(b)) n.brands.push(b)
        }
      }
      // Self-loop style: represent as dashed edge from ingredient to itself via brands
      const key = `dup-self:${id}:${alert.source_rule_id || alert.id}`
      if (!seen.has(key) && (alert.brands || []).length >= 2) {
        seen.add(key)
        edges.push({
          id: key,
          source: id,
          target: id,
          kind: 'duplicate',
          tier: alert.tier || 'review',
          dashed: true,
          ruleId: alert.source_rule_id || alert.id,
          mechanism: alert.mechanism ? String(alert.mechanism) : undefined,
          sourceLabel: alert.source_label || 'source not recorded',
          version: alert.rule_version ? String(alert.rule_version) : undefined,
          status: inferStatus(alert),
          title: alert.title || 'Duplicate ingredient',
          icon: 'copy',
        })
      }
      continue
    }

    // Pairwise edges among listed ingredients
    for (let i = 0; i < ings.length; i++) {
      for (let j = i + 1; j < ings.length; j++) {
        const a = ings[i]
        const b = ings[j]
        const na = norm(a)
        const nb = norm(b)
        if (!nodeMap.has(na)) nodeMap.set(na, { id: na, label: a, brands: alert.brands || [] })
        if (!nodeMap.has(nb)) nodeMap.set(nb, { id: nb, label: b, brands: alert.brands || [] })
        const key = `${isDup ? 'dup' : 'int'}:${pairKey(a, b)}:${alert.source_rule_id || alert.id}`
        if (seen.has(key)) continue
        seen.add(key)
        const kind: RiskEdge['kind'] = isDup ? 'duplicate' : 'interaction'
        edges.push({
          id: key,
          source: na,
          target: nb,
          kind,
          tier: alert.tier || 'review',
          dashed: kind === 'duplicate',
          ruleId: alert.source_rule_id || alert.id,
          mechanism: alert.mechanism ? String(alert.mechanism) : undefined,
          sourceLabel: alert.source_label || 'source not recorded',
          version: alert.rule_version ? String(alert.rule_version) : undefined,
          status: inferStatus(alert),
          title: alert.title || (kind === 'duplicate' ? 'Duplicate' : 'Interaction'),
          icon: tierIcon(alert.tier || 'review', kind),
        })
      }
    }
  }

  // Keep nodes that appear in edges or are from items (show all active ingredients)
  const nodes = [...nodeMap.values()].sort((a, b) => a.label.localeCompare(b.label))

  if (edges.length === 0) {
    return {
      nodes,
      edges: [],
      emptyMessage: 'No matching rule in this prototype dataset',
    }
  }

  return { nodes, edges }
}

/** Circular layout positions in a unit circle scaled to SVG size. */
export function circularLayout(
  nodes: RiskNode[],
  width: number,
  height: number,
  padding = 48,
): Map<string, { x: number; y: number }> {
  const cx = width / 2
  const cy = height / 2
  const r = Math.max(40, Math.min(width, height) / 2 - padding)
  const map = new Map<string, { x: number; y: number }>()
  const n = nodes.length
  if (n === 0) return map
  if (n === 1) {
    map.set(nodes[0].id, { x: cx, y: cy })
    return map
  }
  nodes.forEach((node, i) => {
    const angle = (2 * Math.PI * i) / n - Math.PI / 2
    map.set(node.id, {
      x: cx + r * Math.cos(angle),
      y: cy + r * Math.sin(angle),
    })
  })
  return map
}

export function tierStroke(tier: string): string {
  if (tier === 'critical') return '#f43f5e'
  if (tier === 'review') return '#f59e0b'
  return '#0ea5e9'
}
