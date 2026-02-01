const { chromium } = require('@playwright/test');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();

  console.log('=== VERIFICACIÓN DEL ESTADO DEL USUARIO Y ÓRDENES ===\n');

  try {
    // 1. Ir al panel de mesero
    await page.goto('http://localhost:6081/waiter');
    await page.waitForLoadState('networkidle');

    // 2. Verificar información del usuario
    const usuario = await page.evaluate(() => {
      return {
        employee_role: window.APP_DATA?.employee_role,
        employee_id: window.APP_DATA?.employee_id,
        employee_name: window.APP_DATA?.employee_name,
        role_capabilities: window.APP_DATA?.role_capabilities,
      };
    });

    console.log('--- INFORMACIÓN DEL USUARIO ---');
    console.log(`Rol: ${usuario.employee_role || 'NO DEFINIDO'}`);
    console.log(`ID: ${usuario.employee_id || 'NO DEFINIDO'}`);
    console.log(`Nombre: ${usuario.employee_name || 'NO DEFINIDO'}`);
    console.log(`Capabilities: ${JSON.stringify(usuario.role_capabilities, null, 2)}`);

    // 3. Verificar cookies
    const cookies = await context.cookies();
    console.log('\n--- COOKIES DE AUTENTICACIÓN ---');
    const authCookies = cookies.filter(
      (c) =>
        c.name.toLowerCase().includes('access') ||
        c.name.toLowerCase().includes('refresh') ||
        c.name.toLowerCase().includes('session')
    );
    authCookies.forEach((c) => {
      console.log(`${c.name}: ${c.value.substring(0, 50)}...`);
    });
    if (authCookies.length === 0) {
      console.log('NO HAY COOKIES DE AUTENTICACIÓN');
    }

    // 4. Verificar órdenes
    const ordenes = await page.evaluate(() => {
      return (window.WAITER_ORDERS_DATA || []).map((o) => ({
        id: o.id,
        workflow_status: o.workflow_status,
        status_display: o.status_display,
        waiter_id: o.waiter_id,
        customer_email: o.customer?.email,
        requires_kitchen: o.requires_kitchen,
      }));
    });

    console.log('\n--- ÓRDENES ---');
    ordenes.forEach((o) => {
      console.log(
        `Orden ${o.id}: Estado=${o.workflow_status}, Display="${o.status_display}", Waiter=${o.waiter_id || 'Sin asignar'}, Email=${o.customer_email || 'N/A'}`
      );
    });

    // 5. Verificar si hay órdenes en estado 'new'
    const ordenesNew = ordenes.filter((o) => o.workflow_status === 'new');
    console.log(`\nÓrdenes en estado 'new': ${ordenesNew.length}`);

    // 6. Verificar si hay órdenes en estado 'queued'
    const ordenesQueued = ordenes.filter((o) => o.workflow_status === 'queued');
    console.log(`Órdenes en estado 'queued': ${ordenesQueued.length}`);

    // 7. Verificar botones disponibles
    console.log('\n--- BOTONES DISPONIBLES ---');
    const botones = await page.locator('button:has-text("Aceptar orden")').count();
    console.log(`Botones "Aceptar orden": ${botones}`);

    // 8. Verificar todos los botones de acción
    const todosBotones = await page.evaluate(() => {
      const buttons = document.querySelectorAll('button[data-order-action="workflow"]');
      return Array.from(buttons).map((b) => ({
        text: b.textContent,
        endpoint: b.dataset.endpoint,
      }));
    });
    console.log('Botones de workflow:', todosBotones);
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await browser.close();
  }
})();
