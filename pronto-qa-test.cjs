const { chromium } = require("playwright");
const fs = require("fs");

const CLIENT_URL = "http://localhost:6080";
const EMPLOYEE_URL = "http://localhost:6081";
const TEST_EMAIL = "luartx@gmail.com";

const errors = [];

function captureError(severity, description, location, impact, solution) {
  errors.push({ severity, description, location, impact, solution });
  console.log(`\n❌ [${severity}] ${description}`);
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch({
      headless: false,
      slowMo: 800,
    });

    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
    });

    const clientPage = await context.newPage();
    const employeePage = await context.newPage();

    console.log("\n========================================");
    console.log("  PRONTO QA - CICLO COMPLETO DE TESTING");
    console.log("========================================\n");

    // ========== FASE 1: CLIENTE - VERIFICAR MENU ==========
    console.log("FASE 1: Verificando menú del cliente...");

    await clientPage.goto(CLIENT_URL, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
    await clientPage.waitForTimeout(3000);

    // Verificar que hay productos
    const menuItems = await clientPage.locator("[data-item-id]").count();
    console.log(`  - Items de menú visibles: ${menuItems}`);

    if (menuItems === 0) {
      captureError(
        "CRITICAL",
        "No se visualizan productos en el menú del cliente",
        "localhost:6080 - Menú principal",
        "Usuario no puede ver ni ordenar productos",
        "Verificar endpoint /api/menu y que la base de datos tiene datos",
      );
    } else {
      console.log("  ✅ Menú cargado correctamente");
    }

    // Verificar estructura del DOM
    const hasMenuRoot = await clientPage.locator("[data-menu-root]").count();
    const hasCartPanel = await clientPage.locator("#cart-panel").count();
    const hasCategoryTabs = await clientPage.locator("#category-tabs").count();

    console.log(
      `  - Estructura: menu-root=${hasMenuRoot}, cart-panel=${hasCartPanel}, tabs=${hasCategoryTabs}`,
    );

    if (hasMenuRoot === 0) {
      captureError(
        "HIGH",
        "Falta contenedor [data-menu-root] en la página",
        "localhost:6080",
        "La aplicación JavaScript no puede inicializar",
        "Agregar atributo data-menu-root al contenedor principal del menú",
      );
    }

    // ========== FASE 2: CLIENTE - AGREGAR PRODUCTOS ==========
    console.log("\nFASE 2: Probando agregar productos...");

    if (menuItems > 0) {
      // Click en primer producto
      const firstProduct = clientPage.locator("[data-item-id]").first();
      await firstProduct.click();
      await clientPage.waitForTimeout(1500);

      // Verificar que modal se abrió
      const modalActive = await clientPage.evaluate(() => {
        const modal = document.getElementById("item-modal");
        return modal && modal.classList.contains("active");
      });

      console.log(`  - Modal abierto: ${modalActive}`);

      if (!modalActive) {
        captureError(
          "HIGH",
          "El modal de personalización NO se abre al hacer click en producto",
          "localhost:6080 - Tarjeta de producto",
          "Usuario no puede personalizar productos con modificadores",
          "Verificar evento click en menu.js y clase .active del modal",
        );
      }

      // Verificar botón add to cart
      const addToCartVisible = await clientPage
        .locator("#modal-add-to-cart-btn")
        .isVisible();
      console.log(`  - Botón agregar visible: ${addToCartVisible}`);

      if (addToCartVisible) {
        await clientPage.locator("#modal-add-to-cart-btn").click();
        await clientPage.waitForTimeout(1000);

        // Verificar carrito
        const cartItemCount = await clientPage
          .locator("#cart-items .cart-item")
          .count();
        console.log(`  - Items en carrito: ${cartItemCount}`);

        if (cartItemCount === 0) {
          captureError(
            "HIGH",
            "El carrito está vacío después de agregar producto",
            "localhost:6080 - Carrito",
            "Usuario no puede completar la orden",
            "Verificar función addToCart y actualización del DOM del carrito",
          );
        } else {
          console.log("  ✅ Producto agregado al carrito");
        }
      }
    }

    // ========== FASE 3: CHECKOUT ==========
    console.log("\nFASE 3: Verificando checkout...");

    const checkoutBtn = await clientPage.locator("#checkout-btn").isVisible();
    console.log(`  - Botón checkout visible: ${checkoutBtn}`);

    if (checkoutBtn) {
      await clientPage.locator("#checkout-btn").click();
      await clientPage.waitForTimeout(2000);

      // Verificar página de checkout
      const checkoutUrl = clientPage.url();
      console.log(`  - URL checkout: ${checkoutUrl}`);

      // Verificar campo de email
      const emailInput = await clientPage
        .locator('input[type="email"], input[name="email"], #email-input')
        .first();
      const emailVisible = await emailInput.isVisible();
      console.log(`  - Campo email visible: ${emailVisible}`);

      if (emailVisible) {
        await emailInput.fill(TEST_EMAIL);
        console.log(`  ✅ Email填写完成: ${TEST_EMAIL}`);
      } else {
        captureError(
          "MEDIUM",
          "Campo de email no visible en checkout",
          "localhost:6080/checkout",
          "Usuario no puede confirmar su email",
          "Verificar que el campo de email existe y está visible",
        );
      }

      // Buscar botón de confirmar orden
      const confirmBtn = await clientPage
        .locator(
          'button[type="submit"], .confirm-btn, #confirm-order-btn, button:has-text("Ord")',
        )
        .first();
      const confirmVisible = await confirmBtn.isVisible();
      console.log(`  - Botón confirmar visible: ${confirmVisible}`);

      if (!confirmVisible) {
        captureError(
          "HIGH",
          "No se encontró botón para confirmar la orden",
          "localhost:6080/checkout",
          "Usuario no puede completar la orden",
          "Agregar botón de confirmación con texto claro",
        );
      }
    }

    // ========== FASE 4: EMPLOYEE LOGIN ==========
    console.log("\nFASE 4: Verificando employee app...");

    await employeePage.goto(EMPLOYEE_URL, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
    await employeePage.waitForTimeout(2000);

    // Verificar login page
    const hasLoginForm = await employeePage
      .locator('form, input[name="email"]')
      .count();
    console.log(`  - Formulario login presente: ${hasLoginForm > 0}`);

    if (hasLoginForm > 0) {
      // Llenar credenciales
      await employeePage.fill(
        'input[name="email"], #email',
        "juan.mesero@cafeteria.test",
      );
      await employeePage.fill(
        'input[name="password"], #password',
        "ChangeMe!123",
      );

      const loginBtn = employeePage.locator('button[type="submit"]');
      await loginBtn.click();

      await employeePage.waitForTimeout(3000);

      // Verificar dashboard
      const dashboardUrl = employeePage.url();
      console.log(`  - URL después de login: ${dashboardUrl}`);

      // Verificar scoped redirect
      if (dashboardUrl.includes("/waiter")) {
        console.log("  ✅ Login exitoso, redirect a /waiter");
      } else if (dashboardUrl.includes("/login")) {
        captureError(
          "HIGH",
          "Redirect de login falló - sigue en página de login",
          "localhost:6081 - Login",
          "Usuario no puede acceder al dashboard",
          "Verificar JWT cookies y lógica de redirect en waiter/auth.py",
        );
      }
    }

    // ========== FASE 5: VERIFICAR ELEMENTOS DE UI ==========
    console.log("\nFASE 5: Verificando elementos de UI en employee...");

    // Debug panel
    const debugPanel = await employeePage
      .locator("#debug-panel, .debug-panel")
      .count();
    console.log(`  - Debug panel visible: ${debugPanel > 0}`);

    if (debugPanel > 0) {
      console.log("  ⚠️ DEBUG PANEL VISIBLE (ignorar según instrucciones)");
    }

    // Verificar navigation
    const navItems = await employeePage
      .locator('nav, .nav, [class*="nav"]')
      .count();
    console.log(`  - Elementos de navegación: ${navItems}`);

    // ========== FASE 6: CHECKOUT FLOW ==========
    console.log("\nFASE 6: Verificando flujo de checkout (efectivo)...");

    // Buscar botón de cobrar
    const payBtn = await employeePage
      .locator('button:has-text("Cobrar"), .pay-btn')
      .first();
    const payVisible = await payBtn.isVisible();
    console.log(`  - Botón cobrar visible: ${payVisible}`);

    if (payVisible) {
      await payBtn.click();
      await employeePage.waitForTimeout(1500);

      // Verificar opciones de pago
      const cashBtn = await employeePage
        .locator('button:has-text("Efectivo"), [data-method="cash"]')
        .first();
      const cashVisible = await cashBtn.isVisible();
      console.log(`  - Opción efectivo visible: ${cashVisible}`);

      if (cashVisible) {
        await cashBtn.click();
        await employeePage.waitForTimeout(2000);

        // Verificar estado de pago
        const paidTab = await employeePage
          .locator('a:has-text("Pagadas"), .tab-paid')
          .first();
        if (await paidTab.isVisible()) {
          await paidTab.click();
          await employeePage.waitForTimeout(1000);
          console.log("  ✅ Navegó a pestaña Pagadas");
        }

        // Verificar PDF
        const pdfLink = await employeePage
          .locator('a[href*=".pdf"], .download-pdf')
          .count();
        console.log(`  - Links de PDF: ${pdfLink}`);

        if (pdfLink === 0) {
          captureError(
            "MEDIUM",
            "No hay link para descargar PDF del ticket",
            "localhost:6081/waiter - Órdenes pagadas",
            "Usuario no puede descargar ticket",
            "Agregar funcionalidad de descarga de PDF",
          );
        }

        // Verificar email enviado
        const emailSent = await employeePage
          .locator(".email-sent, .notification-sent, text=enviado")
          .count();
        console.log(`  - Indicadores email enviado: ${emailSent}`);

        if (emailSent === 0) {
          captureError(
            "LOW",
            "No hay confirmación visual de email enviado",
            "localhost:6081 - Post pago",
            "Usuario no sabe si email se envió",
            "Agregar toast/notificación de confirmación",
          );
        }
      }
    }

    // ========== FASE 7: ESTADOS ==========
    console.log("\nFASE 7: Verificando estados de órdenes...");

    const atrasado = await employeePage
      .locator("text=ATRASADO, .status-atrasado")
      .count();
    console.log(`  - Órdenes con estado ATRASADO: ${atrasado}`);

    if (atrasado > 0) {
      captureError(
        "LOW",
        `Hay ${atrasado} órdenes marcadas como ATRASADO sin razón aparente`,
        "localhost:6081",
        "Confusión visual",
        "Revisar lógica de cálculo de estado ATRASADO",
      );
    }

    // ========== RESUMEN ==========
    console.log("\n\n========================================");
    console.log("  REPORTE DE ERRORES PRONTO QA");
    console.log("========================================");
    console.log(`Total de errores: ${errors.length}\n`);

    if (errors.length > 0) {
      const critical = errors.filter((e) => e.severity === "CRITICAL").length;
      const high = errors.filter((e) => e.severity === "HIGH").length;
      const medium = errors.filter((e) => e.severity === "MEDIUM").length;
      const low = errors.filter((e) => e.severity === "LOW").length;

      console.log(`Por severidad:`);
      console.log(`  CRITICAL: ${critical}`);
      console.log(`  HIGH: ${high}`);
      console.log(`  MEDIUM: ${medium}`);
      console.log(`  LOW: ${low}\n`);

      errors.forEach((err, i) => {
        console.log(`${i + 1}. [${err.severity}] ${err.description}`);
        console.log(`   📍 ${err.location}`);
        console.log(`   💥 ${err.impact}`);
        console.log(`   🔧 ${err.solution}\n`);
      });
    } else {
      console.log("✅ NO SE ENCONTRARON ERRORES CRÍTICOS");
    }

    // Guardar reporte
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
      `Error fatal: ${error.message}`,
      "N/A",
      "Testing abortado",
      "Revisar y corregir error",
    );
  } finally {
    if (browser) await browser.close();
  }
})();
