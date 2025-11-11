import { describe, it, expect, vi } from 'vitest'

type Options = { allowed_domains?: string[] }

type RequestPayload = { tools?: Array<any> }

// Minimal function exercising retry-without-filters logic
async function clientSearch(doRequest: (payload: RequestPayload) => Promise<any>, options: Options) {
  const payload: RequestPayload = {
    tools: [{ type: 'web_search', filters: options.allowed_domains ? { allowed_domains: options.allowed_domains } : undefined }],
  }
  try {
    return await doRequest(payload)
  } catch (e: any) {
    const msg = String(e?.message || e)
    if (options.allowed_domains && (msg.includes('filters') || msg.includes("Parameter 'filters' not supported"))) {
      // Remove filters and retry once
      if (payload.tools && payload.tools[0]) delete payload.tools[0].filters
      return await doRequest(payload)
    }
    throw e
  }
}

describe('client retry logic', () => {
  it('gives up after second failure when filters are removed', async () => {
    const doRequest = vi.fn()
      .mockRejectedValueOnce(new Error("Parameter 'filters' not supported"))
      .mockRejectedValueOnce(new Error('still failing'))

    await expect(clientSearch(doRequest, { allowed_domains: ['example.com'] })).rejects.toThrow('still failing')
    // two calls attempted
    expect(doRequest).toHaveBeenCalledTimes(2)
    // second call should have filters removed
    const second = doRequest.mock.calls[1][0]
    expect(second.tools[0].filters).toBeUndefined()
  })
})
