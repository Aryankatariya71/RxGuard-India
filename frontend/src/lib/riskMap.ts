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
  /** Same-ingredient duplicate across brands (drawn as a ring, not a line). */
  selfLoop?: boolean
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

function alertKind(alert: Alert): 'interaction' | 'duplicate' | null {
  const type = (alert.type || '').toLowerCase()
  const title = (alert.title || '').toLowerCase()
  // duplicate_dose / duplicate / class duplicate
  if (type.includes('duplicate') || title.includes('duplicate')) return 'duplicate'
  if (type.includes('interaction') || title.includes('interaction')) return 'interaction'
  return null
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

function ensureNode(
  map: Map<string, RiskNode>,
  name: string,
  brands: string[] = [],
): string {
  const id = norm(name)
  const existing = map.get(id)
  if (!existing) {
    map.set(id, { id, label: name, brands: [...brands] })
  } else {
    for (const b of brands) {
      if (!existing.brands.includes(b)) existing.brands.push(b)
    }
  }
  return id
}

function pushEdge(edges: RiskEdge[], seen: Set<string>, edge: RiskEdge): void {
  if (seen.has(edge.id)) return
  seen.add(edge.id)
  edges.push(edge)
}

export function buildRiskMap(items: LineItem[], alerts: Alert[]): RiskMapData {
  const nodeMap = ingredientsFromItems(items)
  const edges: RiskEdge[] = []
  const seen = new Set<string>()

  for (const alert of alerts || []) {
    const kind = alertKind(alert)
    if (!kind) continue

    const ings = (alert.ingredients || [])
      .map((x) => String(x).trim())
      .filter(Boolean)
    const brands = (alert.brands || []).map(String)

    // Same ingredient in 2+ brands → dashed self / ring edge
    if (kind === 'duplicate' && ings.length === 1) {
      const id = ensureNode(nodeMap, ings[0], brands)
      const brandCount = Math.max(
        brands.length,
        nodeMap.get(id)?.brands.length || 0,
      )
      if (brandCount < 2 && brands.length < 2) {
        // Still surface the alert in the list with a self marker if engine fired
        pushEdge(edges, seen, {
          id: `dup-self:${id}:${alert.source_rule_id || alert.id}`,
          source: id,
          target: id,
          kind: 'duplicate',
          tier: alert.tier || 'review',
          dashed: true,
          selfLoop: true,
          ruleId: alert.source_rule_id || alert.id,
          mechanism: alert.mechanism ? String(alert.mechanism) : undefined,
          sourceLabel: alert.source_label || 'source not recorded',
          version: alert.rule_version ? String(alert.rule_version) : undefined,
          status: inferStatus(alert),
          title: alert.title || 'Duplicate ingredient',
          icon: 'copy',
        })
        continue
      }
      pushEdge(edges, seen, {
        id: `dup-self:${id}:${alert.source_rule_id || alert.id}`,
        source: id,
        target: id,
        kind: 'duplicate',
        tier: alert.tier || 'review',
        dashed: true,
        selfLoop: true,
        ruleId: alert.source_rule_id || alert.id,
        mechanism: alert.mechanism ? String(alert.mechanism) : undefined,
        sourceLabel: alert.source_label || 'source not recorded',
        version: alert.rule_version ? String(alert.rule_version) : undefined,
        status: inferStatus(alert),
        title: alert.title || 'Duplicate ingredient',
        icon: 'copy',
      })
      continue
    }

    // Pairwise among listed ingredients (interactions + multi-ingredient class dup)
    if (ings.length >= 2) {
      for (let i = 0; i < ings.length; i++) {
        for (let j = i + 1; j < ings.length; j++) {
          const a = ings[i]
          const b = ings[j]
          const na = ensureNode(nodeMap, a, brands)
          const nb = ensureNode(nodeMap, b, brands)
          pushEdge(edges, seen, {
            id: `${kind}:${pairKey(a, b)}:${alert.source_rule_id || alert.id}`,
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
            title:
              alert.title || (kind === 'duplicate' ? 'Duplicate' : 'Interaction'),
            icon: tierIcon(alert.tier || 'review', kind),
          })
        }
      }
      continue
    }
  }

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
  padding = 56,
): Map<string, { x: number; y: number }> {
  const cx = width / 2
  const cy = height / 2
  const r = Math.max(60, Math.min(width, height) / 2 - padding)
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

/** Slight curve so overlapping edges stay readable. */
export function edgePath(
  x1: number,
  y1: number,
  x2: number,
  y2: number,
  bend = 0.18,
): string {
  const mx = (x1 + x2) / 2
  const my = (y1 + y2) / 2
  const dx = x2 - x1
  const dy = y2 - y1
  const cx = mx - dy * bend
  const cy = my + dx * bend
  return `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`
}
