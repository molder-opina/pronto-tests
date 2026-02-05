import { expect, Page } from '@playwright/test'

type ApiFailure = {
  url: string
  method: string
  status: number
}

export function installApi404405Guard(page: Page) {
  const failures: ApiFailure[] = []

  page.on('response', (response) => {
    const url = response.url()
    if (!url.includes('/api/')) return

    const request = response.request()
    const method = request.method()
    if (method === 'OPTIONS') return

    const status = response.status()
    if (status !== 404 && status !== 405) return

    failures.push({ url, method, status })
  })

  return {
    assertNoFailures() {
      expect(
        failures,
        `API 404/405 detected: ${JSON.stringify(failures, null, 2)}`
      ).toEqual([])
    },
  }
}

