import { test, expect } from '@playwright/test';

test.describe('Autenticación de Cliente', () => {
    const baseUrl = 'http://localhost:6080';

    test('Registro de nuevo usuario', async ({ page }) => {
        const uniqueSuffix = Date.now().toString().slice(-4);
        const name = `Nuevo Cliente ${uniqueSuffix}`;
        const email = `test-${uniqueSuffix}@example.com`;

        await page.goto(baseUrl);
        await page.waitForLoadState('networkidle');

        // Click on profile button using text or id if possible
        const profileBtn = page.locator('.profile-btn');
        await profileBtn.first().click();

        // Wait for modal by class instead of ID
        const modal = page.locator('.profile-modal');
        await expect(modal).toBeVisible({ timeout: 10000 });

        // Check if we can find the register tab
        const registerTab = page.locator('.profile-tab[data-tab="register"]');
        await registerTab.click();

        await page.fill('#register-name', name);
        await page.fill('#register-email', email);
        await page.fill('#register-phone', '1234567890');
        await page.fill('#register-password', 'Password123');
        await page.check('#accept-terms');

        await page.click('#register-submit-btn');

        await expect(async () => {
            const userInStorage = await page.evaluate(() => localStorage.getItem('pronto-user'));
            if (!userInStorage) throw new Error('Storage empty');
        }).toPass({ timeout: 15000 });

        console.log(`🎉 Success for ${email}`);
    });
});
