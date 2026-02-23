import { test, expect } from '@playwright/test';

const EMPLOYEES_URL = process.env.EMPLOYEES_URL || 'http://localhost:6081';
const API_URL = process.env.API_URL || 'http://localhost:6082';
const DEFAULT_PASSWORD = process.env.EMPLOYEE_PASSWORD || 'ChangeMe!123';

async function loginWaiter(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
): Promise<string> {
  const loginPageResponse = await request.get(`${EMPLOYEES_URL}/waiter/login`);
  expect(loginPageResponse.status()).toBe(200);
  const loginPageHtml = await loginPageResponse.text();
  const csrfMatch = loginPageHtml.match(/<meta\s+name="csrf-token"\s+content="([^"]+)"/i);
  expect(csrfMatch?.[1], '[AUTH] Missing csrf-token meta on /waiter/login').toBeTruthy();
  const csrfToken = csrfMatch![1];

  const loginResponse = await request.post(`${EMPLOYEES_URL}/waiter/login`, {
    form: {
      email: process.env.WAITER_EMAIL || 'maria@pronto.com',
      password: DEFAULT_PASSWORD,
    },
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken,
    },
  });
  expect(loginResponse.status()).toBe(200);
  const payload = await loginResponse.json();
  expect(payload.status).toBe('success');
  return csrfToken;
}

test.describe('Order Management', () => {
  test('waiter can read active orders with canonical payload', async ({ request }) => {
    await loginWaiter(request);

    const ordersResponse = await request.get(`${API_URL}/api/orders?status=active`, {
      headers: { Accept: 'application/json' },
    });
    expect(ordersResponse.status()).toBe(200);

    const payload = await ordersResponse.json();
    expect(payload.status).toBe('success');
    expect(payload.error).toBeNull();
    expect(Array.isArray(payload?.data?.orders)).toBe(true);
    expect(typeof payload?.data?.total).toBe('number');
    expect(typeof payload?.data?.page).toBe('number');
  });

  test('orders endpoint rejects invalid create payload with explicit error', async ({ request }) => {
    const csrfToken = await loginWaiter(request);

    const createResponse = await request.post(`${API_URL}/api/orders`, {
      data: { items: [] },
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    });

    expect(createResponse.status()).toBe(400);
    const payload = await createResponse.json();
    expect(payload.status).toBe('error');
    expect(String(payload.error || '').toLowerCase()).toContain('table_id');
  });
});
