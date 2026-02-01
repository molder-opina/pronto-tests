const { chromium } = require("playwright");
const fs = require("fs");

const CLIENT_URL = "http://localhost:6080";
const EMPLOYEE_URL = "http://localhost:6081";

const errors = [];

function captureError(severity, description, location, impact, solution) {
  errors.push({ severity, description, location, impact, solution });
  console.log(`\n❌ [${severity}] ${description}`);
}

async function checkValidation(page, context) {
  // Check for required field validation
  const requiredFields = await page
    .locator('[required], .is-required, [data-required="true"]')
    .count();
  console.log(`  - Campos requeridos: ${requiredFields}`);

  // Check for validation error messages
  const validationErrors = await page
    .locator('.error, .validation-error, [class*="error"]:visible')
    .count();
  console.log(`  - Errores de validación visibles: ${validationErrors}`);

  if (validationErrors > 0) {
    const errorTexts = await page
      .locator(".error:visible, .validation-error:visible")
      .allTextContents();
    console.log(`  - Mensajes de error: ${errorTexts.join(", ")}`);
  }
}

(async () => {
  let browser;
  try {
    browser = await chromium.launch({
      headless: false,
      slowMo: 500,
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
    await clientPage.goto(CLIENT_URL, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
    await clientPage.waitForTimeout(2000);

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
    await firstProduct
      .click({ timeout: 5000 })
      .catch(() => console.log("   ⚠️ Click falló"));

    await clientPage.waitForTimeout(1500);

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
        "Verificar evento click y clase .active",
      );
    }

    // Verificar estado del botón add to cart
    const addToCartBtn = clientPage.locator("#modal-add-to-cart-btn");
    const btnDisabled = await addToCartBtn.getAttribute("disabled");
    const btnClass = await addToCartBtn.getAttribute("class");
    console.log(`   Botón disabled: ${btnDisabled}, class: ${btnClass}`);

    if (btnDisabled !== null || (btnClass && btnClass.includes("disabled"))) {
      captureError(
        "MEDIUM",
        "Botón add to cart está deshabilitado",
        "localhost:6080 - Modal",
        "Usuario no puede agregar producto sin seleccionar modifiers",
        "Verificar validación de campos requeridos antes de habilitar",
      );
    }

    // Check validation
    console.log("\n3. Verificando validación de campos...");
    await checkValidation(clientPage, "cliente");

    // Checkout
    console.log("\n4. Verificando checkout...");
    const checkoutVisible = await clientPage
      .locator("#checkout-btn")
      .isVisible();
    console.log(`   Botón checkout: ${checkoutVisible}`);

    // ========== EMPLOYEE ==========
    console.log("\n5. EMPLOYEE - Login...");
    await employeePage.goto(EMPLOYEE_URL, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
    await employeePage.waitForTimeout(2000);

    await employeePage.fill(
      'input[name="email"]',
      "juan.mesero@cafeteria.test",
    );
    await employeePage.fill('input[name="password"]', "ChangeMe!123");
    await employeePage.locator('button[type="submit"]').click();

    await employeePage.waitForTimeout(3000);
    const empUrl = employeePage.url();
    console.log(`   URL después de login: ${empUrl}`);

    if (empUrl.includes("/waiter")) {
      console.log("   ✅ Login exitoso");
    } else if (empUrl.includes("/login")) {
      captureError(
        "HIGH",
        "Login falló - redirect a login",
        "localhost:6081",
        "No se puede acceder",
        "Verificar JWT y cookies",
      );
    }

    // Dashboard elements
    console.log("\n6. Dashboard waiter...");
    const orderCards = await employeePage
      .locator("[data-order-id], .order-card")
      .count();
    console.log(`   Órdenes visibles: ${orderCards}`);

    // Debug panel
    const debugPanel = await employeePage
      .locator("#debug-panel, .debug-panel")
      .count();
    if (debugPanel > 0) console.log("   ⚠️ Debug panel visible (ignorar)");

    // Cobrar flow
    console.log("\n7. Verificando flujo cobrar...");
    const payBtn = await employeePage
      .locator('button:has-text("Cobrar")')
      .first();
    if (await payBtn.isVisible()) {
      await payBtn.click();
      await employeePage.waitForTimeout(1000);

      const cashBtn = await employeePage
        .locator('button:has-text("Efectivo")')
        .first();
      if (await cashBtn.isVisible()) {
        await cashBtn.click();
        await employeePage.waitForTimeout(2000);

        // Pagadas tab
        const paidTab = await employeePage
          .locator('a:has-text("Pagadas")')
          .first();
        if (await paidTab.isVisible()) {
          await paidTab.click();
          await employeePage.waitForTimeout(1000);
          console.log("   ✅ Navegó a Pagadas");
        }

        // PDF
        const pdfLink = await employeePage.locator('a[href*=".pdf"]').count();
        console.log(`   Links PDF: ${pdfLink}`);
        if (pdfLink === 0) {
          captureError(
            "MEDIUM",
            "No hay link de PDF",
            "localhost:6081 - Pagadas",
            "No se puede descargar ticket",
            "Agregar botón PDF",
          );
        }

        // Email confirmation
        const emailConfirm = await employeePage
          .locator(".email-sent, text=enviado")
          .count();
        console.log(`   Email enviado: ${emailConfirm}`);
        if (emailConfirm === 0) {
          captureError(
            "LOW",
            "Sin confirmación de email",
            "localhost:6081",
            "Usuario no sabe si email llegó",
            "Agregar toast confirmación",
          );
        }
      }
    }

    // ATRASADO status
    console.log("\n8. Verificando estados...");
    const atrasado = await employeePage.locator("text=ATRASADO").count();
    console.log(`   ATRASADO: ${atrasado}`);
    if (atrasado > 0) {
      captureError(
        "LOW",
        "Estado ATRASADO sin razón",
        "localhost:6081",
        "Confusión visual",
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
      console.log("✅ Sin errores críticos");
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
  } catch (error) {
    captureError(
      "CRITICAL",
      `Error fatal: ${error.message}`,
      "N/A",
      "Testing abortado",
      "Revisar logs",
    );
  } finally {
    if (browser) await browser.close();
  }
})();
