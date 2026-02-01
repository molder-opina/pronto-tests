const { chromium } = require("playwright");

const CLIENT_URL = "http://localhost:6080";
const EMPLOYEE_URL = "http://localhost:6081";
const TEST_EMAIL = "luartx@gmail.com";

const errors = [];
const steps = [];

async function logStep(step, message) {
  const timestamp = new Date().toISOString();
  steps.push(`[${timestamp}] ${step}: ${message}`);
  console.log(`\n=== ${step} ===`);
  console.log(message);
}

async function captureError(severity, description, location, impact, solution) {
  const error = {
    severity,
    description,
    location,
    impact,
    solution,
  };
  errors.push(error);
  console.log(`\n❌ ERROR [${severity}]: ${description}`);
  console.log(`   Location: ${location}`);
  console.log(`   Impact: ${impact}`);
  console.log(`   Solution: ${solution}`);
}

async function takeScreenshot(page, name) {
  const filename = `/tmp/pronto-test-${name}-${Date.now()}.png`;
  await page.screenshot({ path: filename, fullPage: true });
  console.log(`📸 Screenshot: ${filename}`);
  return filename;
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch({
      headless: false,
      slowMo: 500,
      args: ["--no-sandbox", "--disable-setuid-sandbox"],
    });

    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
      userAgent:
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    });

    const clientPage = await context.newPage();
    const employeePage = await context.newPage();

    // Capture console errors from client page
    clientPage.on("console", (msg) => {
      if (msg.type() === "error") {
        captureError(
          "MEDIUM",
          `Console error en cliente: ${msg.text()}`,
          "localhost:6080",
          "Puede indicar problemas en la UI",
          "Revisar logs del navegador y corregir JavaScript",
        );
      }
    });

    // Capture console errors from employee page
    employeePage.on("console", (msg) => {
      if (msg.type() === "error") {
        captureError(
          "MEDIUM",
          `Console error en employee: ${msg.text()}`,
          "localhost:6081",
          "Puede indicar problemas en la UI",
          "Revisar logs del navegador y corregir JavaScript",
        );
      }
    });

    // ========== FASE 1: Crear orden en cliente ==========
    await logStep("FASE 1", "Iniciando creación de orden en cliente");

    await clientPage.goto(CLIENT_URL, {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await takeScreenshot(clientPage, "01-cliente-home");

    // Wait for menu to load
    await clientPage.waitForTimeout(3000);

    // Check if menu items are visible
    const menuItems = await clientPage.locator("[data-item-id]").count();
    console.log(`Items de menú visibles: ${menuItems}`);

    if (menuItems === 0) {
      captureError(
        "CRITICAL",
        "No se visualizan productos en el menú del cliente",
        "localhost:6080 - Menú principal",
        "Usuario no puede ver ni ordenar productos",
        "Verificar que los datos de menú están cargados en la base de datos y el endpoint /api/menu responde correctamente",
      );
    }

    // Select first available product
    const firstProduct = clientPage.locator("[data-item-id]").first();
    if (await firstProduct.isVisible()) {
      await firstProduct.click();
      await clientPage.waitForTimeout(1000);
      await takeScreenshot(clientPage, "02-producto-seleccionado");

      // Check if modal opened
      const modal = clientPage.locator("#item-modal");
      if (await modal.evaluate((el) => !el.classList.contains("active"))) {
        captureError(
          "HIGH",
          "El modal de personalización de producto no se abre al hacer click",
          "localhost:6080 - Tarjeta de producto",
          "Usuario no puede personalizar productos con modificadores",
          "Verificar el evento click y la lógica de apertura del modal en menu.js",
        );
      }

      // Add to cart
      const addToCartBtn = clientPage.locator("#modal-add-to-cart-btn");
      if (await addToCartBtn.isVisible()) {
        await addToCartBtn.click();
        await clientPage.waitForTimeout(500);
      }
    }

    // Add more products
    const allProducts = clientPage.locator("[data-item-id]");
    const totalProducts = await allProducts.count();
    console.log(`Total de productos disponibles: ${totalProducts}`);

    if (totalProducts > 1) {
      // Add second product
      await allProducts.nth(1).click();
      await clientPage.waitForTimeout(1000);
      const addBtn2 = clientPage.locator("#modal-add-to-cart-btn");
      if (await addBtn2.isVisible()) {
        await addBtn2.click();
      }
    }

    await clientPage.waitForTimeout(1000);
    await takeScreenshot(clientPage, "03-carrito-con-productos");

    // Check cart
    const cartItems = await clientPage
      .locator("#cart-items .cart-item")
      .count();
    console.log(`Items en carrito: ${cartItems}`);

    if (cartItems === 0) {
      captureError(
        "HIGH",
        "El carrito está vacío después de agregar productos",
        "localhost:6080 - Carrito",
        "Usuario no puede completar la orden",
        "Verificar que el addToCart funciona correctamente y actualiza el estado del carrito",
      );
    }

    // Go to checkout
    const checkoutBtn = clientPage.locator("#checkout-btn");
    if (await checkoutBtn.isVisible()) {
      await checkoutBtn.click();
      await clientPage.waitForTimeout(2000);
      await takeScreenshot(clientPage, "04-checkout");
    }

    // ========== FASE 2: Confirmar orden con email ==========
    await logStep("FASE 2", "Confirmando orden con email");

    // Wait for checkout page to load
    await clientPage.waitForTimeout(2000);

    // Fill email
    const emailInput = clientPage.locator(
      'input[type="email"], input[name="email"]',
    );
    if (await emailInput.isVisible()) {
      await emailInput.fill(TEST_EMAIL);
      await takeScreenshot(clientPage, "05-email-ingresado");
    } else {
      captureError(
        "MEDIUM",
        "Campo de email no visible en checkout",
        "localhost:6080/checkout",
        "Usuario no puede confirmar su email",
        "Verificar que el campo de email existe y está visible",
      );
    }

    // Confirm order
    const confirmBtn = clientPage.locator(
      'button[type="submit"], .confirm-btn, #confirm-order-btn',
    );
    if (await confirmBtn.isVisible()) {
      await confirmBtn.click();
      await clientPage.waitForTimeout(3000);
      await takeScreenshot(clientPage, "06-orden-confirmada");
    } else {
      // Look for any submit button
      const allButtons = await clientPage.locator("button").all();
      console.log(`Botones encontrados: ${allButtons.length}`);

      // Find button with "confirm" or "ordenar" text
      const confirmButtons = await clientPage
        .locator(
          'button:has-text("Ord"), button:has-text("Confir"), button:has-text("Pagar")',
        )
        .all();
      if (confirmButtons.length > 0) {
        await confirmButtons[0].click();
        await clientPage.waitForTimeout(3000);
      } else {
        captureError(
          "HIGH",
          "No se encontró botón para confirmar la orden",
          "localhost:6080/checkout",
          "Usuario no puede completar la orden",
          "Agregar botón de confirmación visible con texto claro",
        );
      }
    }

    // Check for validation errors before submission
    const validationErrors = await clientPage
      .locator('.error, .validation-error, [class*="error"]')
      .count();
    if (validationErrors > 0) {
      captureError(
        "MEDIUM",
        `Hay ${validationErrors} errores de validación visibles`,
        "localhost:6080/checkout",
        "El formulario tiene errores de validación",
        "Revisar validación de campos obligatorios",
      );
    }

    await clientPage.waitForTimeout(2000);

    // ========== FASE 3: Verificar orden en employee ==========
    await logStep("FASE 3", "Verificando orden en employee app");

    await employeePage.goto(EMPLOYEE_URL, {
      waitUntil: "networkidle",
      timeout: 30000,
    });
    await takeScreenshot(employeePage, "07-employee-login");

    // Login as waiter
    const emailField = employeePage.locator('input[name="email"], input#email');
    const passwordField = employeePage.locator(
      'input[name="password"], input#password',
    );

    if (await emailField.isVisible()) {
      await emailField.fill("juan.mesero@cafeteria.test");
      await passwordField.fill("ChangeMe!123");
      await takeScreenshot(employeePage, "08-credenciales-llenadas");

      const loginBtn = employeePage.locator('button[type="submit"]');
      await loginBtn.click();

      await employeePage.waitForTimeout(3000);
      await takeScreenshot(employeePage, "09-dashboard-mesero");
    } else {
      // Already logged in?
      await employeePage.waitForTimeout(2000);
    }

    // Look for the new order
    await employeePage.waitForTimeout(2000);
    const orderCards = await employeePage
      .locator("[data-order-id], .order-card, .order-item")
      .count();
    console.log(`Órdenes visibles en dashboard: ${orderCards}`);

    if (orderCards === 0) {
      captureError(
        "MEDIUM",
        "No se visualizan órdenes en el dashboard del mesero",
        "localhost:6081/waiter/dashboard",
        "Mesero no puede ver órdenes nuevas",
        "Verificar endpoint de órdenes y polling en tiempo real",
      );
    }

    // ========== FASE 4: Chef - Iniciar y Listo ==========
    await logStep("FASE 4", "Chef procesando orden");

    // Navigate to chef view
    const chefNav = employeePage
      .locator('a[href*="chef"], .nav-chef, text=Cocina')
      .first();
    if (await chefNav.isVisible()) {
      await chefNav.click();
      await employeePage.waitForTimeout(2000);
      await takeScreenshot(employeePage, "10-chef-dashboard");
    }

    // Find and start order
    const startBtn = employeePage.locator(
      'button:has-text("Iniciar"), .start-order-btn',
    );
    if (await startBtn.first().isVisible()) {
      await startBtn.first().click();
      await employeePage.waitForTimeout(1000);
    }

    // Mark as ready
    const readyBtn = employeePage.locator(
      'button:has-text("Listo"), .ready-btn',
    );
    if (await readyBtn.first().isVisible()) {
      await readyBtn.first().click();
      await employeePage.waitForTimeout(1000);
      await takeScreenshot(employeePage, "11-orden-lista");
    }

    // ========== FASE 5: Mesero - Entregar y Cobrar ==========
    await logStep("FASE 5", "Mesero entregando y cobrando");

    // Navigate back to waiter
    const waiterNav = employeePage
      .locator('a[href*="waiter"], .nav-waiter, text=Mesero')
      .first();
    if (await waiterNav.isVisible()) {
      await waiterNav.click();
      await employeePage.waitForTimeout(2000);
    }

    // Find order and deliver
    const deliverBtn = employeePage.locator(
      'button:has-text("Entregar"), .deliver-btn',
    );
    if (await deliverBtn.first().isVisible()) {
      await deliverBtn.first().click();
      await employeePage.waitForTimeout(1000);
      await takeScreenshot(employeePage, "12-orden-entregada");
    }

    // Pay with cash
    const payBtn = employeePage.locator(
      'button:has-text("Cobrar"), .pay-btn, .checkout-btn',
    );
    if (await payBtn.first().isVisible()) {
      await payBtn.first().click();
      await employeePage.waitForTimeout(1000);
      await takeScreenshot(employeePage, "13-opciones-pago");

      // Select cash payment
      const cashBtn = employeePage.locator(
        'button:has-text("Efectivo"), [data-method="cash"]',
      );
      if (await cashBtn.first().isVisible()) {
        await cashBtn.first().click();
        await employeePage.waitForTimeout(2000);
        await takeScreenshot(employeePage, "14-pago-efectivo");
      }
    }

    // Check for orders in paid tab
    const paidTab = employeePage.locator('a:has-text("Pagadas"), .tab-paid');
    if (await paidTab.first().isVisible()) {
      await paidTab.first().click();
      await employeePage.waitForTimeout(2000);
      await takeScreenshot(employeePage, "15-orden-pagada");
    }

    // Check for email sent indicator
    const emailSent = await employeePage
      .locator('.email-sent, .notification-sent, [class*="email"]')
      .count();
    console.log(`Indicadores de email enviado: ${emailSent}`);

    // Check for PDF download link
    const pdfLink = await employeePage
      .locator('a[href*=".pdf"], .download-pdf, [class*="pdf"]')
      .count();
    console.log(`Links de PDF disponibles: ${pdfLink}`);

    if (pdfLink === 0) {
      captureError(
        "MEDIUM",
        "No se encontró link para descargar PDF de ticket",
        "localhost:6081/waiter - Panel de órdenes pagadas",
        "Usuario no puede descargar ticket en PDF",
        "Agregar botón de descarga de PDF visible después del pago",
      );
    }

    // Check for "ATRASADO" status without reason
    const atrasadoStatus = await employeePage
      .locator('text=ATRASADO, .status-atrasado, [class*="atrasado"]')
      .count();
    if (atrasadoStatus > 0) {
      captureError(
        "LOW",
        `Se encontraron ${atrasadoStatus} órdenes con estado "ATRASADO" sin razón aparente`,
        "localhost:6081",
        "Confusión visual para usuarios",
        "Revisar lógica de cálculo de estado ATRASADO o agregar tooltip explicativo",
      );
    }

    // Check for DEBUG PANEL in production
    const debugPanel = await employeePage
      .locator('#debug-panel, .debug-panel, [id*="debug"], [class*="debug"]')
      .count();
    if (debugPanel > 0) {
      console.log(
        `⚠️ DEBUG PANEL VISIBLE (ignorar según instrucciones): ${debugPanel}`,
      );
    }

    // Check for email sent notification
    const emailNotification = await employeePage
      .locator(".email-confirmation, .email-sent-notification, text=enviado")
      .count();
    if (emailNotification === 0) {
      captureError(
        "LOW",
        "No hay confirmación visual de que el email fue enviado",
        "localhost:6081/waiter - Post pago",
        "Usuario no sabe si el email se envió correctamente",
        "Agregar toast o notificación confirmando envío de email",
      );
    }

    // ========== RESUMEN ==========
    console.log("\n\n========================================");
    console.log("  RESUMEN DE ERRORES ENCONTRADOS");
    console.log("========================================");
    console.log(`Total de errores: ${errors.length}`);

    if (errors.length === 0) {
      console.log("\n✅ NO SE ENCONTRARON ERRORES");
    } else {
      const critical = errors.filter((e) => e.severity === "CRITICAL").length;
      const high = errors.filter((e) => e.severity === "HIGH").length;
      const medium = errors.filter((e) => e.severity === "MEDIUM").length;
      const low = errors.filter((e) => e.severity === "LOW").length;

      console.log(`\nPor severidad:`);
      console.log(`  CRITICAL: ${critical}`);
      console.log(`  HIGH: ${high}`);
      console.log(`  MEDIUM: ${medium}`);
      console.log(`  LOW: ${low}`);

      console.log("\n\n========================================");
      console.log("  REPORTE DETALLADO DE ERRORES");
      console.log("========================================\n");

      errors.forEach((err, i) => {
        console.log(`${i + 1}. ERROR [${err.severity}]: ${err.description}`);
        console.log(`   Ubicación: ${err.location}`);
        console.log(`   Impacto: ${err.impact}`);
        console.log(`   Solución: ${err.solution}`);
        console.log("");
      });
    }

    // Guardar reporte a archivo
    const fs = require("fs");
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        total: errors.length,
        critical: errors.filter((e) => e.severity === "CRITICAL").length,
        high: errors.filter((e) => e.severity === "HIGH").length,
        medium: errors.filter((e) => e.severity === "MEDIUM").length,
        low: errors.filter((e) => e.severity === "LOW").length,
      },
      errors: errors,
    };
    fs.writeFileSync(
      "/tmp/pronto-qa-report.json",
      JSON.stringify(report, null, 2),
    );
    console.log("\n📄 Reporte guardado en /tmp/pronto-qa-report.json");
  } catch (error) {
    console.error("\n❌ ERROR FATAL:", error.message);
    captureError(
      "CRITICAL",
      `Error fatal durante ejecución: ${error.message}`,
      "N/A",
      "Testing completo abortado",
      "Revisar logs y corregir error antes de reintentar",
    );
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();
