import { describe, it, expect } from 'vitest'

type Result = {
  productType: string
  brand: string
  model: string
  issueSummary: string
  observations: string[]
  hypothesis: string
  actionPlan: string[]
  escalationCriteria: string[]
  suggestedKeywords: string[]
}

function parseLLM(raw: string, context: Pick<Result, 'productType'|'brand'|'model'|'issueSummary'>): Result {
  let txt = raw.trim()
  if (txt.startsWith('```')) {
    txt = txt.replace(/^```(json)?/i, '').replace(/```\s*$/, '').trim()
  }
  try {
    const data = JSON.parse(txt)
    // Minimal check to force fallback when required arrays missing
    if (!Array.isArray(data.observations) || !Array.isArray(data.actionPlan) || !Array.isArray(data.escalationCriteria)) {
      throw new Error('missing arrays')
    }
    return data as Result
  } catch {
    return {
      productType: context.productType,
      brand: context.brand,
      model: context.model,
      issueSummary: context.issueSummary,
      observations: ['Record exact symptoms and any error codes/messages.'],
      hypothesis: 'Insufficient details: gather more observations to isolate root cause.',
      actionPlan: ['Reproduce the issue and note exact conditions.'],
      escalationCriteria: ['Battery swelling or burning smell.'],
      suggestedKeywords: [context.issueSummary, context.brand, context.model, context.productType],
    }
  }
}

describe('troubleshooter fallback', () => {
  it('returns fallback for fenced malformed JSON with minimal fields', () => {
    const fenced = '```json\n{"productType":"Router","brand":"X","model":"Y","issueSummary":"Erratic"}\n```'
    const r = parseLLM(fenced, { productType: 'Router', brand: 'X', model: 'Y', issueSummary: 'Erratic' })
    expect(r.hypothesis.toLowerCase()).toContain('insufficient details')
    expect(r.observations.length).toBeGreaterThan(0)
  })
})
