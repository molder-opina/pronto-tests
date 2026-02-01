import { chromium } from '@playwright/test';

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('=== VERIFICACIÓN DETALLADA DE AUTENTICACIÓN ===\n');

  try {
    // 1. Ir al panel de mesero
    await page.goto('http://localhost:6081/waiter');
    await page.waitForLoadState('networkidle');

    // 2. Verificar TODAS las cookies
    const cookies = await context.cookies();
    console.log('--- TODAS LAS COOKIES ---');
    cookies.forEach((c) => {
      console.log(`${c.name}: ${c.value.substring(0, 80)}...`);
    });

    // 3. Verificar información del usuario desde la sesión de Flask
    const sessionInfo = await page.evaluate(() => {
      // Verificar si existe la sesión de Flask
      const flaskSession = document.cookie.includes('session');

      // Verificar localStorage
      const localStorageKeys = Object.keys(localStorage || {});

      return {
        flaskSessionExists: flaskSession,
        localStorageKeys: localStorageKeys,
      };
    });
    console.log('\n--- INFORMACIÓN DE SESIÓN ---');
    console.log(`Flask Session existe: ${sessionInfo.flaskSessionExists}`);
    console.log(`LocalStorage keys: ${sessionInfo.localStorageKeys.join(', ')}`);

    // 4. Verificar si hay un JWT token en algún lugar
    const jwtInfo = await page.evaluate(() => {
      // Buscar en cookies
      const cookies = document.cookie.split(';').reduce((acc, cookie) => {
        const [key, value] = cookie.trim().split('=');
        acc[key] = value;
        return acc;
      }, {});

      return {
        hasAccessToken: 'access_token' in cookies,
        hasRefreshToken: 'refresh_token' in cookies,
        hasSession: 'session' in cookies,
        sessionValue: cookies['session']?.substring(0, 100) || 'N/A',
      };
    });
    console.log('\n--- JWT TOKEN INFO ---');
    console.log(`Has Access Token: ${jwtInfo.hasAccessToken}`);
    console.log(`Has Refresh Token: ${jwtInfo.hasRefreshToken}`);
    console.log(`Has Session Cookie: ${jwtInfo.hasSession}`);
    console.log(`Session Value: ${jwtInfo.sessionValue}...`);

    // 5. Verificar si hay un elemento de login visible
    const loginVisible = await page
      .locator('input[name="email"], input[name="username"]')
      .first()
      .isVisible()
      .catch(() => false);
    console.log(`\n¿Login visible?: ${loginVisible}`);

    // 6. Verificar si estamos en la página de login
    const currentUrl = page.url();
    console.log(`URL actual: ${currentUrl}`);

    // 7. Verificar contenido de la página
    const pageContent = await page.evaluate(() => {
      return {
        title: document.title,
        bodyText: document.body?.innerText?.substring(0, 500) || 'N/A',
      };
    });
    console.log(`\nTítulo: ${pageContent.title}`);
    console.log(`Preview del body: ${pageContent.bodyText}...`);
  } catch (error) {
    console.error('Error:', error.message);
    console.error(error.stack);
  } finally {
    await browser.close();
  }
})();
