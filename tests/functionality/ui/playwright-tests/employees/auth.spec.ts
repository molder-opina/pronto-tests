import { test, expect } from '@playwright/test';

const EMPLOYEES_URL = process.env.EMPLOYEES_URL || 'http://localhost:6081';
const API_URL = process.env.API_URL || 'http://localhost:6081';
const DEFAULT_PASSWORD = process.env.EMPLOYEE_PASSWORD || 'ChangeMe!123';

const ROLE_CREDENTIALS = {
  waiter: {
    email: process.env.WAITER_EMAIL || 'maria@pronto.com',
    password: DEFAULT_PASSWORD,
    loginPath: '/waiter/login',
  },
  admin: {
    email: process.env.ADMIN_EMAIL || 'juan@pronto.com',
    password: DEFAULT_PASSWORD,
    loginPath: '/admin/login',
  },
} as const;

async function expectSuccessfulRoleLogin(
  request: Parameters<Parameters<typeof test>[1]>[0]['request'],
  role: keyof typeof ROLE_CREDENTIALS,
) {
  const { email, password, loginPath } = ROLE_CREDENTIALS[role];
  const loginPageResponse = await request.get(`${EMPLOYEES_URL}${loginPath}`);
  expect(loginPageResponse.status()).toBe(200);
  const loginPageHtml = await loginPageResponse.text();
  const csrfMatch = loginPageHtml.match(/<meta\s+name="csrf-token"\s+content="([^"]+)"/i);
  expect(csrfMatch?.[1], `[AUTH] Missing csrf-token meta on ${loginPath}`).toBeTruthy();
  const csrfToken = csrfMatch![1];

  const response = await request.post(`${EMPLOYEES_URL}${loginPath}`, {
    form: { email, password },
    headers: {
      Accept: 'application/json',
      'X-Requested-With': 'XMLHttpRequest',
      'X-CSRFToken': csrfToken,
    },
  });

  expect(
    response.status(),
    `[AUTH] ${role} login failed (${response.status()}) for ${email}. This must fail tests when auth breaks.`,
  ).toBe(200);

  const payload = await response.json();
  expect(payload.status).toBe('success');

  const meResponse = await request.get(`${API_URL}/api/employees/auth/me`, {
    headers: { Accept: 'application/json' },
  });
  expect(meResponse.status(), `[AUTH] ${role} /auth/me is unauthorized after login`).toBe(200);
}

test.describe('Employee Authentication', () => {
  test('admin credentials authenticate successfully', async ({ request }) => {
    await expectSuccessfulRoleLogin(request, 'admin');
  });

  test('waiter credentials authenticate successfully', async ({ request }) => {
    await expectSuccessfulRoleLogin(request, 'waiter');
  });
});
