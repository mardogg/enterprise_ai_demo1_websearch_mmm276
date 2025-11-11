import { describe, it, expect } from 'vitest'

describe('diagnostics summarize no-match', () => {
  // Mimic Python summarize logic heuristics: if patterns absent, arrays remain empty
  function summarize(results: Record<string, string>) {
    const summary: Record<string, string[]> = { Network: [], Storage: [], Performance: [], Connectivity: [] }
    const netCfg = results['Network config'] || ''
    if (netCfg.includes('<IP>')) summary.Network.push('IP addresses detected (redacted)')
    if ('Disks' in results) {
      const disks = results['Disks'] || ''
      if (disks.includes('FreePhysicalMemory') || disks.includes('Bytes')) summary.Storage.push('Disk stats collected')
    }
    if ('Top snapshot' in results) summary.Performance.push('Top snapshot available')
    if (Object.keys(results).some(k => k.startsWith('Ping'))) summary.Connectivity.push('Ping tests executed')
    return summary
  }

  it('returns all empty arrays when no patterns match', () => {
    const res = summarize({ Foo: 'bar', Baz: 'qux' })
    expect(res.Network.length).toBe(0)
    expect(res.Storage.length).toBe(0)
    expect(res.Performance.length).toBe(0)
    expect(res.Connectivity.length).toBe(0)
  })
})
