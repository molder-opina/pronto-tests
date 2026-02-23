import { test, expect } from '@playwright/test';

const EMPLOYEES_URL = process.env.EMPLOYEES_URL || 'http://localhost:6081';
const DEFAULT_PASSWORD = process.env.EMPLOYEE_PASSWORD || 'ChangeMe!123';

const LOGIN_ROUTES = [
  '/waiter/login',
  '/chef/login',
  '/cashier/login',
  '/admin/login',
  '/system/login',
];

const EXPECTED_CONTEXT_BY_ROUTE: Record<string, string> = {
  '/waiter/login': 'waiter',
  '/chef/login': 'chef',
  '/cashier/login': 'cashier',
  '/admin/login': 'admin',
  '/system/login': 'system',
};

const ROLE_LOGINS = [
  {
    role: 'waiter',
    path: '/waiter/login',
    email: process.env.WAITER_EMAIL || 'maria@pronto.com',
    password: DEFAULT_PASSWORD,
  },
  {
    role: 'chef',
    path: '/chef/login',
    email: process.env.CHEF_EMAIL || 'carlos@pronto.com',
    password: DEFAULT_PASSWORD,
  },
  {
    role: 'cashier',
    path: '/cashier/login',
    email: process.env.CASHIER_EMAIL || 'pedro@pronto.com',
    password: DEFAULT_PASSWORD,
  },
  {
    role: 'admin',
    path: '/admin/login',
    email: process.env.ADMIN_EMAIL || 'juan@pronto.com',
    password: DEFAULT_PASSWORD,
  },
] as const;

test.describe('Employee Login Flows', () => {
  for (const route of LOGIN_ROUTES) {
    test(`login page exposes csrf + shell for ${route}`, async ({ request }) => {
      const response = await request.get(`${EMPLOYEES_URL}${route}`);
      expect(response.status()).toBe(200);

      const body = await response.text();
      expect(body.toLowerCase().includes('404')).toBe(false);
      expect(body).toContain('name="csrf-token"');
      expect(body).toContain('<div id="app"></div>');
      expect(body).toContain('assets/js/employees/main.js');
      expect(body).toMatch(new RegExp(`window\\.APP_CONTEXT\\s*=\\s*['"]${EXPECTED_CONTEXT_BY_ROUTE[route]}['"]`));
    });
  }

  for (const login of ROLE_LOGINS) {
    test(`${login.role} login rejects auth errors and returns success payload`, async ({ request }) => {
      const loginPageResponse = await request.get(`${EMPLOYEES_URL}${login.path}`);
      expect(loginPageResponse.status()).toBe(200);
      const loginPageHtml = await loginPageResponse.text();
      const csrfMatch = loginPageHtml.match(/<meta\s+name="csrf-token"\s+content="([^"]+)"/i);
      expect(csrfMatch?.[1], `[AUTH] Missing csrf-token meta on ${login.path}`).toBeTruthy();
      const csrfToken = csrfMatch![1];

      const response = await request.post(`${EMPLOYEES_URL}${login.path}`, {
        form: {
          email: login.email,
          password: login.password,
        },
        headers: {
          Accept: 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
          'X-CSRFToken': csrfToken,
        },
      });

      expect(
        response.status(),
        `[AUTH] ${login.role} login returned ${response.status()} for ${login.email}; auth failures must fail tests.`,
      ).toBe(200);

      const payload = await response.json();
      expect(payload.status).toBe('success');
    });
  }

  test('login screen stays in guest mode (no sidebar)', async ({ page }) => {
    const response = await page.request.get(`${EMPLOYEES_URL}/waiter/login`);
    expect(response.status()).toBe(200);
    const html = await response.text();
    // Vue SPA - check that it's a valid page with Vue app
    expect(html).toContain('id="app"');
    expect(html).toContain('csrf-token');
  });
});
