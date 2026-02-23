import { test, expect } from '@playwright/test';

const API_BASE = 'http://localhost:6082';
const TEST_TABLE_ID = '340bac9c-b24d-41ef-beb3-cd0ba354fe4c';

test.describe('Client Session/Auth API (current contracts)', () => {
  test('GET /api/sessions/me returns SESSION_EXPIRED without token', async ({ request }) => {
    const response = await request.get(`${API_BASE}/api/sessions/me`);
    expect(response.status()).toBe(401);

    const body = await response.json();
    expect(body.code).toBe('SESSION_EXPIRED');
  });

  test('POST /api/sessions/open works without CSRF (uses JWT auth)', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/sessions/open`, {
      data: { table_id: TEST_TABLE_ID },
    });

    expect([200, 201]).toContain(response.status());
  });

  test('POST /api/client-auth/register returns 404 (endpoint not implemented)', async ({ request }) => {
    const suffix = Date.now().toString().slice(-6);
    const response = await request.post(`${API_BASE}/api/client-auth/register`, {
      data: {
        name: 'Contract User',
        email: `contract-${suffix}@example.com`,
        password: 'Password123!'
      },
    });

    expect(response.status()).toBe(404);
  });

  test('Legacy /api/auth/register endpoint is not available', async ({ request }) => {
    const response = await request.post(`${API_BASE}/api/auth/register`, {
      data: { email: 'legacy@example.com', password: 'Password123!' },
    });

    expect(response.status()).toBe(404);
  });
});
