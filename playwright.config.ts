export default {
  testDir: 'tests',
  timeout: 30000,
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:6080',
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
