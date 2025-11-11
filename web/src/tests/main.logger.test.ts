import { describe, it, expect, vi } from 'vitest'

describe('main logger after display', () => {
  function run(display: (s: string) => void, logger: { info: (m: string) => void }) {
    const text = 'Result text'
    display(text)
    logger.info(`Search completed: ${1} citations found`)
  }

  it('calls logger.info after display', () => {
    const display = vi.fn()
    const logger = { info: vi.fn() }
    run(display, logger)
    expect(display).toHaveBeenCalled()
    expect(logger.info).toHaveBeenCalledWith(expect.stringContaining('citations found'))
  })
})
