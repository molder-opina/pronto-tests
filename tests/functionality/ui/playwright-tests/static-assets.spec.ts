import { test, expect } from '@playwright/test';

test.describe('Static Assets Configuration', () => {
    test('should load assets from public host and not internal host', async ({ page }) => {
        // Read expected public host from env or default
        // The default here matches the default in .env for localdev
        const expectedPublicHost = (process.env.PRONTO_STATIC_PUBLIC_HOST || 'http://localhost:9088').replace(/\/$/, '');

        let expectedHostname: string;
        let expectedPort: string;

        try {
            const url = new URL(expectedPublicHost);
            expectedHostname = url.hostname;
            expectedPort = url.port || (expectedPublicHost.startsWith('https') ? '443' : '80');
        } catch (e) {
            console.error(`Invalid PRONTO_STATIC_PUBLIC_HOST: ${expectedPublicHost}`);
            throw e;
        }

        const expectedHostString = `${expectedHostname}:${expectedPort}`;
        console.log(`Expecting assets from: ${expectedHostString}`);

        // Intercept all requests to check for forbidden hosts
        const failedRequests: string[] = [];
        await page.route('**/*', route => {
            const url = route.request().url();
            // Forbidden: internal static container alias or explicit static:80
            if (url.includes('://static/') || url.includes('static:80')) {
                failedRequests.push(url);
            }
            route.continue();
        });

        // Navigate to the client app
        await page.goto('/');

        // fail if any request was made to the internal static host
        expect(failedRequests, `Requests were made to internal static host: ${failedRequests.join(', ')}`).toHaveLength(0);

        // Check CSS links
        const cssLinks = await page.locator('link[rel="stylesheet"]').all();
        console.log(`Found ${cssLinks.length} CSS links`);
        for (const link of cssLinks) {
            const href = await link.getAttribute('href');
            if (href) {
                // FAIL if internal host is leaked
                expect(href).not.toContain('static:80');
                expect(href).not.toContain('://static/');

                // If it is a local asset (contains /assets/), it MUST use the public host
                // We assume all our assets are under /assets/ path and not starting with data:
                if (href.includes('/assets/') && !href.startsWith('data:')) {
                    expect(href).toContain(expectedHostString);
                }
            }
        }

        // Check JS scripts
        const scripts = await page.locator('script[src]').all();
        console.log(`Found ${scripts.length} Scripts`);
        for (const script of scripts) {
            const src = await script.getAttribute('src');
            if (src) {
                // FAIL if internal host is leaked
                expect(src).not.toContain('static:80');
                expect(src).not.toContain('://static/');

                // If it is a local asset
                if (src.includes('/assets/') && !src.startsWith('data:')) {
                    expect(src).toContain(expectedHostString);
                }
            }
        }

        // Check Page Content for hardcoded strings
        const content = await page.content();
        expect(content).not.toContain('://static/');
        expect(content).not.toContain('static:80/');

        // Check CSP Header logic
        // We need to reload to capture headers if not already captured
        const response = await page.reload();
        if (response) {
            const csp = response.headers()['content-security-policy'];
            if (csp) {
                // In DEBUG mode (assumed here for local test run), upgrade-insecure-requests should be absent
                if (process.env.DEBUG_MODE === 'true' || process.env.DEBUG_MODE === '1') {
                    expect(csp).not.toContain('upgrade-insecure-requests');
                }
                // Verify the public host is in the CSP (heuristic)
                // e.g. script-src ... localhost:9088 ...
                expect(csp).toContain(expectedHostname);
            }
        }
    });
});
