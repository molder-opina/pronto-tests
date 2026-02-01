export default {
  testDir: ['tests/functionality', 'tests/performance', 'tests/design'],
  timeout: 30000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },
  projects: [
    {
      name: 'functionality',
      testMatch: /tests\/functionality\/.*\.spec\.(ts|js)/,
    },
    {
      name: 'performance',
      testMatch: /tests\/performance\/.*\.spec\.(ts|js)/,
    },
    {
      name: 'design',
      testMatch: /tests\/design\/.*\.spec\.(ts|js)/,
    },
  ],
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
};
