import { test, expect } from '@playwright/test';

const EMPLOYEES_URL = process.env.EMPLOYEES_URL || 'http://localhost:6081';
const API_URL = process.env.API_URL || 'http://localhost:6082';
const DEFAULT_PASSWORD = process.env.EMPLOYEE_PASSWORD || 'ChangeMe!123';

async function loginByRole(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
  role: 'admin' | 'waiter',
  email: string,
) {
  const loginPath = `/${role}/login`;
  const loginPageResponse = await request.get(`${EMPLOYEES_URL}${loginPath}`);
  expect(loginPageResponse.status()).toBe(200);

  const loginPageHtml = await loginPageResponse.text();
  const csrfMatch = loginPageHtml.match(/<meta\s+name="csrf-token"\s+content="([^"]+)"/i);
  expect(csrfMatch?.[1], `[AUTH] Missing csrf-token meta on ${loginPath}`).toBeTruthy();
  const csrfToken = csrfMatch![1];

  const loginResponse = await request.post(`${EMPLOYEES_URL}${loginPath}`, {
    form: { email, password: DEFAULT_PASSWORD },
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken,
    },
  });

  expect(
    loginResponse.status(),
    `[AUTH] ${role} login failed with ${loginResponse.status()} for ${email}`,
  ).toBe(200);

  const payload = await loginResponse.json();
  expect(payload.status).toBe('success');
}

test.describe('Menu Management', () => {
  test('admin sees real menu payload from API', async ({ request }) => {
    await loginByRole(request, 'admin', process.env.ADMIN_EMAIL || 'juan@pronto.com');

    const menuResponse = await request.get(`${API_URL}/api/menu`, {
      headers: { Accept: 'application/json' },
    });
    expect(menuResponse.status()).toBe(200);
    const payload = await menuResponse.json();

    expect(payload.status).toBe('success');
    const categories = payload?.data?.categories || [];
    expect(Array.isArray(categories)).toBe(true);
    expect(categories.length).toBeGreaterThan(0);
    expect(Array.isArray(categories[0]?.items)).toBe(true);
    expect(categories[0].items.length).toBeGreaterThan(0);
  });

  test('waiter UI does not expose admin modules', async ({ request }) => {
    // Login as waiter
    const loginPath = '/waiter/login';
    const loginPageResponse = await request.get(`${EMPLOYEES_URL}${loginPath}`);
    expect(loginPageResponse.status()).toBe(200);
    const loginPageHtml = await loginPageResponse.text();
    const csrfMatch = loginPageHtml.match(/<meta\s+name="csrf-token"\s+content="([^"]+)"/i);
    const csrfToken = csrfMatch?.[1];
    
    const loginResponse = await request.post(`${EMPLOYEES_URL}${loginPath}`, {
      form: { email: process.env.WAITER_EMAIL || 'maria@pronto.com', password: DEFAULT_PASSWORD },
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken || '',
      },
    });
    expect(loginResponse.status()).toBe(200);
    
    // Get the dashboard as waiter - check we don't get admin content
    const dashboardResponse = await request.get(`${EMPLOYEES_URL}/waiter/dashboard`);
    expect(dashboardResponse.status()).toBe(200);
    const dashboardHtml = await dashboardResponse.text();
    
    // Verify waiter has waiter-specific modules but not admin modules
    expect(dashboardHtml).toContain('waiter');
    expect(dashboardHtml).not.toContain('Empleados');
    expect(dashboardHtml).not.toContain('Roles y Permisos');
  });
});
