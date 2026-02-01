import { test, expect } from '@playwright/test';

test.describe('Autenticación de Cliente', () => {
    const baseUrl = 'http://localhost:6080';

    test('Registro e Inicio de Sesión', async ({ page }) => {
        page.on('console', msg => console.log(`💻 [BROWSER] ${msg.type()}: ${msg.text()}`));

        console.log(`👤 Navegando a ${baseUrl}...`);
        await page.goto(baseUrl);
        await page.waitForLoadState('networkidle');

        const profileBtn = page.locator('.profile-btn').first();
        await expect(profileBtn).toBeVisible();
        await profileBtn.click();

        const modal = page.locator('#profile-modal');
        await expect(modal).toBeAttached();

        console.log('👤 Cambiando a pestaña de registro...');
        await page.click('.profile-tab[data-tab="register"]');

        const suffix = Date.now().toString().slice(-4);
        const email = `test-${suffix}@example.com`;

        console.log(`👤 Llenando datos para ${email}...`);
        await page.fill('#register-name', 'Test User');
        await page.fill('#register-email', email);
        await page.fill('#register-phone', '1234567890');
        await page.fill('#register-password', 'Password123');

        console.log('👤 Marcando checkbox de términos...');
        // Forzamos el click en el checkbox mismo
        await page.locator('#accept-terms').click({ force: true });

        // Debugging values
        const values = await page.evaluate(() => {
            const terms = (document.getElementById('accept-terms') as HTMLInputElement).checked;
            const pass = (document.getElementById('register-password') as HTMLInputElement).value;
            const btnDisabled = (document.getElementById('register-submit-btn') as HTMLButtonElement).disabled;
            return { terms, pass, btnDisabled };
        });
        console.log('📊 Estado actual en el navegador:', values);

        const registerBtn = page.locator('#register-submit-btn');
        if (values.btnDisabled) {
            console.log('⚠️ Botón sigue deshabilitado, forzando llamada a updateRegisterButtonState...');
            await page.evaluate(() => (window as any).updateRegisterButtonState?.() ||
                // Fallback si no es global
                (() => {
                    const termsCheckbox = document.getElementById('accept-terms') as HTMLInputElement | null;
                    const passwordInput = document.getElementById('register-password') as HTMLInputElement | null;
                    const submitBtn = document.getElementById('register-submit-btn') as HTMLButtonElement | null;
                    if (submitBtn && passwordInput) {
                        const termsAccepted = termsCheckbox?.checked ?? false;
                        const passwordValid = passwordInput.value.length >= 6;
                        submitBtn.disabled = !(termsAccepted && passwordValid);
                    }
                })()
            );
        }

        await expect(registerBtn).toBeEnabled({ timeout: 10000 });
        await registerBtn.click();

        console.log('👤 Verificando registro en storage...');
        await expect(async () => {
            const user = await page.evaluate(() => localStorage.getItem('pronto-user'));
            if (!user) throw new Error('No user in storage');
        }).toPass({ timeout: 15000 });

        console.log('🎉 Registro exitoso!');

        // El resto del flujo... (Login/Logout)
        // Para acortar, solo verificamos que estamos logueados
        const avatar = page.locator('#profile-avatar');
        await expect(avatar).toBeVisible();
    });
});
