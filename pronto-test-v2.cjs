const { chromium } = require("playwright");
const fs = require("fs");

const CLIENT_URL = "http://localhost:6080";
const EMPLOYEE_URL = "http://localhost:6081";

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
      slowMo: 300,
    });

    const context = await browser.newContext({
      viewport: { width: 1920, height: 1080 },
    });
    const clientPage = await context.newPage();
    const employeePage = await context.newPage();

    console.log("\n========================================");
    console.log("  PRONTO QA - CICLO COMPLETO");
    console.log("========================================\n");

    // ========== CLIENTE ==========
    console.log("1. CLIENTE - Verificando menú...");
    await clientPage.goto(CLIENT_URL, { waitUntil: "load", timeout: 30000 });
    await clientPage.waitForTimeout(3000);

    const menuItems = await clientPage.locator("[data-item-id]").count();
    console.log(`   Items: ${menuItems}`);

    if (menuItems === 0) {
      captureError(
        "CRITICAL",
        "No hay productos visibles",
        "localhost:6080",
        "No se pueden hacer órdenes",
        "Verificar /api/menu y base de datos",
      );
    }

    // Click en producto
    console.log("\n2. Click en producto...");
    const firstProduct = clientPage.locator("[data-item-id]").first();
    await firstProduct.click({ timeout: 5000 });

    await clientPage.waitForTimeout(2000);

    const modalActive = await clientPage.evaluate(() => {
      const modal = document.getElementById("item-modal");
      return modal && modal.classList.contains("active");
    });
    console.log(`   Modal activo: ${modalActive}`);

    if (!modalActive) {
      captureError(
        "HIGH",
        "Modal no abre al click en producto",
        "localhost:6080",
        "No se pueden agregar productos",
        "Verificar evento click y clase .active en menu.js",
      );
    }

    // Verificar botón add to cart
    const addToCartBtn = clientPage.locator("#modal-add-to-cart-btn");
    const btnDisabled = await addToCartBtn.getAttribute("disabled");
    const btnClass = await addToCartBtn.getAttribute("class");
    console.log(`   Botón disabled: ${btnDisabled}, class: ${btnClass}`);

    if (btnDisabled !== null || (btnClass && btnClass.includes("disabled"))) {
      captureError(
        "MEDIUM",
        "Botón add to cart deshabilitado - faltan modifiers requeridos",
        "localhost:6080 - Modal",
        "Usuario no puede agregar producto",
        "Verificar lógica de validación de modifiers requeridos",
      );
    }

    // Checkout
    console.log("\n3. Checkout...");
    const checkoutVisible = await clientPage
      .locator("#checkout-btn")
      .isVisible();
    console.log(`   Botón checkout: ${checkoutVisible}`);

    // ========== EMPLOYEE ==========
    console.log("\n4. EMPLOYEE - Login...");
    await employeePage.goto(EMPLOYEE_URL, {
      waitUntil: "load",
      timeout: 30000,
    });
    await employeePage.waitForTimeout(3000);

    await employeePage.fill(
      'input[name="email"]',
      "juan.mesero@cafeteria.test",
    );
    await employeePage.fill('input[name="password"]', "ChangeMe!123");
    await employeePage.locator('button[type="submit"]').click();

    await employeePage.waitForTimeout(4000);
    const empUrl = employeePage.url();
    console.log(`   URL: ${empUrl}`);

    if (empUrl.includes("/waiter")) {
      console.log("   ✅ Login exitoso");
    } else if (empUrl.includes("/login")) {
      captureError(
        "HIGH",
        "Login falló - redirect a login",
        "localhost:6081",
        "No se puede acceder",
        "Verificar JWT y cookies en ScopeGuard",
      );
    }

    // Dashboard
    console.log("\n5. Dashboard...");
    const orderCards = await employeePage
      .locator("[data-order-id], .order-card")
      .count();
    console.log(`   Órdenes: ${orderCards}`);

    // Debug panel
    const debugPanel = await employeePage.locator("#debug-panel").count();
    if (debugPanel > 0) console.log("   ⚠️ Debug panel visible (ignorar)");

    // Cobrar flow
    console.log("\n6. Cobrar efectivo...");
    const payBtn = await employeePage
      .locator('button:has-text("Cobrar")')
      .first();
    if (await payBtn.isVisible()) {
      await payBtn.click();
      await employeePage.waitForTimeout(2000);

      const cashBtn = await employeePage
        .locator('button:has-text("Efectivo")')
        .first();
      if (await cashBtn.isVisible()) {
        await cashBtn.click();
        await employeePage.waitForTimeout(3000);

        // Pagadas
        const paidTab = await employeePage
          .locator('a:has-text("Pagadas")')
          .first();
        if (await paidTab.isVisible()) {
          await paidTab.click();
          await employeePage.waitForTimeout(2000);
          console.log("   ✅ Pagadas");
        }

        // PDF
        const pdfLink = await employeePage.locator('a[href*=".pdf"]').count();
        console.log(`   PDF: ${pdfLink}`);
        if (pdfLink === 0) {
          captureError(
            "MEDIUM",
            "Sin link PDF",
            "localhost:6081 - Pagadas",
            "No se puede descargar ticket",
            "Agregar funcionalidad PDF",
          );
        }

        // Email
        const emailConfirm = await employeePage
          .locator(".email-sent, .notification")
          .count();
        console.log(`   Email: ${emailConfirm}`);
        if (emailConfirm === 0) {
          captureError(
            "LOW",
            "Sin confirmación email",
            "localhost:6081",
            "Usuario sin feedback",
            "Agregar toast confirmación",
          );
        }
      }
    }

    // ATRASADO
    console.log("\n7. Estados...");
    const atrasado = await employeePage.locator("text=ATRASADO").count();
    console.log(`   ATRASADO: ${atrasado}`);
    if (atrasado > 0) {
      captureError(
        "LOW",
        "Estado ATRASADO visible",
        "localhost:6081",
        "Confusión",
        "Revisar lógica de estado",
      );
    }

    // ========== REPORTE ==========
    console.log("\n\n========================================");
    console.log("  REPORTE DE ERRORES");
    console.log("========================================");
    console.log(`Total: ${errors.length} errores\n`);

    const bySev = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0 };
    errors.forEach((e) => bySev[e.severity]++);
    console.log(`CRITICAL: ${bySev.CRITICAL}`);
    console.log(`HIGH: ${bySev.HIGH}`);
    console.log(`MEDIUM: ${bySev.MEDIUM}`);
    console.log(`LOW: ${bySev.LOW}\n`);

    if (errors.length === 0) {
      console.log("✅ Sin errores");
    } else {
      errors.forEach((e, i) => {
        console.log(`${i + 1}. [${e.severity}] ${e.description}`);
        console.log(`   📍 ${e.location}`);
        console.log(`   💥 ${e.impact}`);
        console.log(`   🔧 ${e.solution}\n`);
      });
    }

    fs.writeFileSync(
      "/tmp/pronto-qa-report.json",
      JSON.stringify(
        {
          timestamp: new Date().toISOString(),
          summary: bySev,
          errors: errors,
        },
        null,
        2,
      ),
    );
    console.log("\n📄 /tmp/pronto-qa-report.json");
  } catch (error) {
    captureError(
      "CRITICAL",
      `Error: ${error.message}`,
      "N/A",
      "Abortado",
      "Verificar",
    );
    console.error(error);
  } finally {
    if (browser) await browser.close();
  }
})();
