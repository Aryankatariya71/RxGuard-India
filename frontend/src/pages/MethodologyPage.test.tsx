import { describe, expect, it, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MethodologyPage } from './MethodologyPage'

vi.mock('../api/methodology', async () => {
  const actual = await vi.importActual<typeof import('../api/methodology')>(
    '../api/methodology',
  )
  return {
    ...actual,
    fetchMethodologyStats: vi.fn(async () => ({
      engine_version: 'engine-test',
      dataset_version: 'demo-test',
      products_in_db: 12,
      ingredients_in_db: 8,
      ddinter_pairs_loaded: null,
      incomplete_composition_links: 0,
      catalogue_files: {
        source_csv_rows: null,
        cleaned_parquet_rows: null,
        ddinter_pairs_loaded: null,
      },
      interaction_rules: {
        by_status: {
          DEMO_ILLUSTRATIVE: 1,
          REVIEW_PENDING: 2,
          CLINICALLY_REVIEWED: 0,
          total: 3,
        },
      },
      dose_rules: {
        by_status: {
          DEMO_ILLUSTRATIVE: 0,
          REVIEW_PENDING: 1,
          CLINICALLY_REVIEWED: 0,
          total: 1,
        },
      },
      tests: { backend_test_function_count: 10, backend_test_file_count: 2 },
      gold: {
        gold_case_count: 40,
        developer_labeled_count: 40,
        pharmacist_verified_count: 0,
      },
      evaluation: {
        brand_resolution_accuracy: null,
        false_alarm_rate_clean: null,
        precision_recall_by_type: null,
      },
      composition_examples: null,
      alert_fatigue: {
        naive_alert_count: null,
        merged_alert_count: null,
        note: 'Run the stress test to measure',
      },
      rule_status_note: 'Today most rules are REVIEW_PENDING.',
      disclaimer:
        'RxGuard India is a prescription-review support prototype. It does not replace a doctor or pharmacist.',
    })),
  }
})

const frontendSources = import.meta.glob(['../**/*.{ts,tsx,css}'], {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

describe('MethodologyPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders every major section and the disclaimer', async () => {
    render(
      <MemoryRouter>
        <MethodologyPage />
      </MemoryRouter>,
    )
    await waitFor(() => {
      expect(screen.getByTestId('methodology-page')).toBeInTheDocument()
    })
    expect(screen.getByTestId('methodology-disclaimer-top')).toHaveTextContent(
      /does not replace a doctor or pharmacist/i,
    )
    expect(screen.getByTestId('methodology-disclaimer-bottom')).toBeInTheDocument()

    const ids = [
      'glance',
      'problem',
      'principles',
      'pipeline',
      'data-sources',
      'brand-resolution',
      'ingredient-expansion',
      'dose',
      'safety-checks',
      'alert-fatigue',
      'evaluation',
      'explainability',
      'privacy',
      'limitations',
      'related',
    ]
    for (const id of ids) {
      expect(document.getElementById(id)).toBeTruthy()
    }

    const body = document.body.textContent || ''
    expect(body).not.toMatch(/100% safe/i)
    expect(body).not.toMatch(/clinically validated/i)
    expect(body).not.toMatch(/guaranteed/i)
  })

  it('does not hard-code known catalogue counts in frontend source', () => {
    const banned = ['249880', '256489', '256490', '41494']
    const offenders: string[] = []
    for (const [path, text] of Object.entries(frontendSources)) {
      if (path.includes('.test.')) continue
      for (const n of banned) {
        if (text.includes(n)) offenders.push(`${path} contains ${n}`)
      }
    }
    expect(offenders).toEqual([])
  })
})
