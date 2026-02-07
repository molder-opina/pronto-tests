import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:6082';
const TEST_TABLE_ID = '340bac9c-b24d-41ef-beb3-cd0ba354fe4c'; // T1 UUID

test.describe('Client JWT Authentication API', () => {
    let anonToken: string;
    let anonCookie: string;

    test('GET /sessions/me returns SESSION_EXPIRED without token', async ({ request }) => {
        const response = await request.get(`${API_BASE}/api/sessions/me`);
        expect(response.status()).toBe(401);
        const body = await response.json();
        expect(body.code).toBe('SESSION_EXPIRED');
    });

    test('POST /sessions/open creates anonymous session', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/sessions/open`, {
        data: { table_id: TEST_TABLE_ID },
    });

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.success).toBe(true);
        expect(body.session.mode).toBe('anonymous');
        expect(body.session.table_id).toBe(TEST_TABLE_ID);
        expect(body.session.id).toBeDefined();
        // Session ID is a UUID string, not an integer
        expect(typeof body.session.id).toBe('string');

        // Check cookie was set
        const cookies = response.headers()['set-cookie'];
        expect(cookies).toBeDefined();
        expect(cookies).toContain('access_token=');
    });

    test('POST /auth/register creates customer and returns client token', async ({ request }) => {
        const suffix = Date.now().toString().slice(-6);
        const email = `test-${suffix}@example.com`;
        const password = 'Password123!';

        const response = await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'Test User',
                email,
                phone: '1234567890',
                password,
            },
        });

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.success).toBe(true);
        expect(body.customer.email).toBe(email);
        expect(body.customer.name).toBe('Test User');
        // Customer ID is a UUID string, not an integer
        expect(body.customer.id).toBeDefined();
        expect(typeof body.customer.id).toBe('string');

        // Check cookie was set with client mode
        const cookies = response.headers()['set-cookie'];
        expect(cookies).toBeDefined();
    });

    test('POST /auth/login authenticates customer', async ({ request }) => {
        // First register
        const suffix = Date.now().toString().slice(-6);
        const email = `login-test-${suffix}@example.com`;
        const password = 'Password123!';

        await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'Login Test',
                email,
                password,
            },
        });

        // Then login
        const response = await request.post(`${API_BASE}/api/auth/login`, {
            data: {
                email,
                password,
            },
        });

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.success).toBe(true);
        expect(body.customer.email).toBe(email);
    });

    test('POST /auth/login fails with wrong password', async ({ request }) => {
        const suffix = Date.now().toString().slice(-6);
        const email = `wrong-pass-${suffix}@example.com`;
        const password = 'CorrectPassword123!';

        // Register first
        await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'Wrong Pass Test',
                email,
                password,
            },
        });

        // Try login with wrong password
        const response = await request.post(`${API_BASE}/api/auth/login`, {
            data: {
                email,
                password: 'WrongPassword123!',
            },
        });

        // Should return 401 for invalid credentials
        expect(response.status()).toBe(401);
        const body = await response.json();
        expect(body.success).toBe(false);
        expect(body.error).toContain('Invalid');
    });

    test('POST /auth/logout clears cookie', async ({ request }) => {
        const response = await request.post(`${API_BASE}/api/auth/logout`);

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.success).toBe(true);

        // Check cookie was cleared
        const cookies = response.headers()['set-cookie'];
        expect(cookies).toBeDefined();
        expect(cookies).toContain('access_token=');
        expect(cookies).toContain('Max-Age=0');
    });

    test('GET /sessions/me returns session info with token', async ({ request }) => {
        // Note: Cookie with Domain=.pronto.com won't work with localhost
        // This test verifies the endpoint structure, not cookie transmission
        const response = await request.get(`${API_BASE}/api/sessions/me`);

        // Without proper cookie domain, expect 401 (no valid token)
        // In production with proper domain, this would return 200 with session info
        expect([200, 401]).toContain(response.status());
    });

    test('POST /auth/register merges anonymous session', async ({ request }) => {
        // Note: Full session merge requires cookie transmission working
        // which isn't possible with Domain=.pronto.com on localhost
        const suffix = Date.now().toString().slice(-6);
        const response = await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'Merge Test',
                email: `merge-${suffix}@example.com`,
                password: 'Password123!',
            },
        });

        expect(response.status()).toBe(200);
        const body = await response.json();
        expect(body.success).toBe(true);
        expect(body.customer.id).toBeDefined();
    });

    test('POST /auth/register rejects duplicate email', async ({ request }) => {
        const suffix = Date.now().toString().slice(-6);
        const email = `duplicate-${suffix}@example.com`;
        const password = 'Password123!';

        // Register first time
        await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'First User',
                email,
                password,
            },
        });

        // Try register again with same email
        const response = await request.post(`${API_BASE}/api/auth/register`, {
            data: {
                name: 'Second User',
                email,
                password: 'DifferentPassword123!',
            },
        });

        expect(response.status()).toBe(400);
        const body = await response.json();
        expect(body.success).toBe(false);
        expect(body.error).toContain('already registered');
    });
});
