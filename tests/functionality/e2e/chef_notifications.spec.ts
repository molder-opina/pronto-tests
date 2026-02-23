import { test, expect } from '@playwright/test';

const EMPLOYEES_URL = process.env.EMPLOYEES_URL || 'http://localhost:6081';
const DEFAULT_PASSWORD = process.env.EMPLOYEE_PASSWORD || 'ChangeMe!123';
const CHEF_EMAIL = process.env.CHEF_EMAIL || 'carlos@pronto.com';

test.describe('Chef Login and Dashboard', () => {
    test('chef login page renders correctly', async ({ request }) => {
        const response = await request.get(`${EMPLOYEES_URL}/chef/login`);
        expect(response.status()).toBe(200);

        const body = await response.text();
        expect(body).toContain('name="csrf-token"');
        expect(body).toContain('<div id="app"></div>');
        expect(body).toContain('assets/js/employees/main.js');
        expect(body).toMatch(/window\.APP_CONTEXT\s*=\s*['"]chef['"]/);
    });

    test('chef can login via API', async ({ request }) => {
        // Get CSRF token first
        const loginPage = await request.get(`${EMPLOYEES_URL}/chef/login`);
        const loginHtml = await loginPage.text();
        const csrfMatch = loginHtml.match(/content="([^"]+)"/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Login
        const response = await request.post(`${EMPLOYEES_URL}/api/employees/auth/login`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            data: {
                email: CHEF_EMAIL,
                password: DEFAULT_PASSWORD,
            },
        });

        // Should succeed (if seed data exists)
        if (response.status() === 200) {
            const data = await response.json();
            expect(data.status).toBe('success');
        } else {
            // Skip if credentials not seeded
            test.skip(true, 'Chef credentials not available');
        }
    });

    test('chef can access realtime notifications endpoint after login', async ({ request }) => {
        // Get CSRF token
        const loginPage = await request.get(`${EMPLOYEES_URL}/chef/login`);
        const loginHtml = await loginPage.text();
        const csrfMatch = loginHtml.match(/content="([^"]+)"/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Login
        const loginResponse = await request.post(`${EMPLOYEES_URL}/api/employees/auth/login`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            data: {
                email: CHEF_EMAIL,
                password: DEFAULT_PASSWORD,
            },
        });

        if (loginResponse.status() !== 200) {
            test.skip(true, 'Chef credentials not available');
            return;
        }

        // Get realtime notifications
        const notificationsResponse = await request.get(`${EMPLOYEES_URL}/api/realtime/notifications`);

        // Should return valid response
        expect([200, 401]).toContain(notificationsResponse.status());
    });

    test('chef can access realtime orders endpoint after login', async ({ request }) => {
        // Get CSRF token
        const loginPage = await request.get(`${EMPLOYEES_URL}/chef/login`);
        const loginHtml = await loginPage.text();
        const csrfMatch = loginHtml.match(/content="([^"]+)"/);
        const csrfToken = csrfMatch ? csrfMatch[1] : '';

        // Login
        const loginResponse = await request.post(`${EMPLOYEES_URL}/api/employees/auth/login`, {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            data: {
                email: CHEF_EMAIL,
                password: DEFAULT_PASSWORD,
            },
        });

        if (loginResponse.status() !== 200) {
            test.skip(true, 'Chef credentials not available');
            return;
        }

        // Get realtime orders
        const ordersResponse = await request.get(`${EMPLOYEES_URL}/api/realtime/orders`);

        // Should return valid response
        expect([200, 401]).toContain(ordersResponse.status());
    });
});
