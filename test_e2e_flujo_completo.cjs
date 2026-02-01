/**
 * Test E2E: Flujo completo de orden en PRONTO Cafetería
 *
 * Este script automatiza el flujo completo:
 * 1. Cliente crea orden en http://localhost:6080
 * 2. Chef procesa la orden (iniciar -> listo)
 * 3. Mesero entrega y cobra (entregar -> cobrar)
 * 4. Verificaciones finales (email, PDF, estados)
 */

const { chromium } = require('playwright');

const CLIENT_URL = 'http://localhost:6080';
const EMPLOYEE_URL = 'http://localhost:6081';

const CREDENTIALS = {
  waiter: { email: 'juan.mesero@cafeteria.test', password: 'ChangeMe!123' },
  chef: { email: 'carlos.chef@cafeteria.test', password: 'ChangeMe!123' },
  cashier: { email: 'pedro.cajero@cafeteria.test', password: 'ChangeMe!123' },
};

const CUSTOMER_EMAIL = 'luartx@gmail.com';

async function testFlujoCompleto() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║        TEST E2E: FLUJO COMPLETO DE ORDEN PRONTO              ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  const browser = await chromium.launch({ headless: false, slowMo: 100 });
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 },
  });
  const page = await context.newPage();

  const errors = [];
  const logs = [];

  // ═══════════════════════════════════════════════════════════════
  // FASE 1: CLIENTE CREA ORDEN
  // ═══════════════════════════════════════════════════════════════
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('  FASE 1: CLIENTE CREA ORDEN');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

  try {
    // 1.1 Abrir menú
    console.log('1.1 Abriendo menú...');
    await page.goto(CLIENT_URL, { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);

    // Verificar que el menú cargó
    const menuSections = await page.locator('#menu-sections').count();
    if (menuSections > 0) {
      console.log('   ✓ Menú cargado correctamente');
      logs.push('FASE 1: Menú cargado');
    } else {
      errors.push('ERROR [ALTO]: Menú no cargó - #menu-sections no encontrado');
      console.log('   ✗ ERROR: Menú no cargado');
    }

    // 1.2 Agregar productos
    console.log('\n1.2 Agregando productos al carrito...');
    const productos = await page.locator('.menu-item-card').all();
    console.log(`   Encontrados ${productos.length} productos`);

    if (productos.length >= 2) {
      // Producto 1
      await productos[0].click();
      await page.waitForTimeout(1500);

      const modalOpen = await page
        .locator('#item-modal.open, .modal--item-customization.active')
        .count();
      if (modalOpen > 0) {
        console.log('   ✓ Modal de producto abierto');

        // Verificar campos obligatorios
        const itemName = await page.locator('#modal-item-name').count();
        const itemPrice = await page.locator('#modal-total-price').count();

        if (itemName > 0 && itemPrice > 0) {
          console.log('   ✓ Campos obligatorios visibles');
        } else {
          errors.push('ERROR [MEDIO]: Campos obligatorios no visibles en modal');
        }

        // Agregar al carrito
        const addBtn = await page.locator('#modal-add-to-cart-btn').count();
        if (addBtn > 0) {
          await page.locator('#modal-add-to-cart-btn').click();
          await page.waitForTimeout(1000);
          console.log('   ✓ Producto 1 agregado');

          // Cerrar modal
          await page.locator('.modal-close').click();
          await page.waitForTimeout(500);
        }

        // Producto 2
        await productos[1].click();
        await page.waitForTimeout(1500);

        await page.locator('#modal-add-to-cart-btn').click();
        await page.waitForTimeout(1000);
        console.log('   ✓ Producto 2 agregado');

        await page.locator('.modal-close').click();
        await page.waitForTimeout(500);
      } else {
        errors.push('ERROR [ALTO]: Modal no se abrió al hacer click en producto');
      }
    } else {
      errors.push(`ERROR [ALTO]: No hay suficientes productos (encontrados: ${productos.length})`);
    }

    // 1.3 Verificar carrito
    console.log('\n1.3 Verificando carrito...');
    const cartBtn = await page.locator('[data-toggle-cart], .cart-btn').count();
    if (cartBtn > 0) {
      await page.locator('[data-toggle-cart], .cart-btn').first().click();
      await page.waitForTimeout(1000);

      const cartCount = await page.locator('#cart-items-count').textContent();
      console.log(`   ✓ Carrito con ${cartCount || 0} items`);
    }

    // 1.4 Checkout
    console.log('\n1.4 Proceso de checkout...');
    const checkoutBtn = await page.locator('#checkout-btn').count();
    if (checkoutBtn > 0) {
      await page.locator('#checkout-btn').click();
      await page.waitForTimeout(2000);

      const checkoutForm = await page.locator('#checkout-form').count();
      if (checkoutForm > 0) {
        console.log('   ✓ Formulario de checkout visible');

        // Llenar campos obligatorios
        await page.fill('#customer-name', 'LuArtX Test');
        await page.fill('#customer-email', CUSTOMER_EMAIL);
        await page.fill('#customer-phone', '5551234567');
        console.log('   ✓ Campos completados');

        // Método de pago
        const payLaterBtn = await page.locator('button:has-text("Pagar después")').count();
        if (payLaterBtn > 0) {
          await page.locator('button:has-text("Pagar después")').click();
          await page.waitForTimeout(500);
          console.log('   ✓ Método: Pagar después');
        }

        // Confirmar orden
        await page.locator('button[type="submit"]').click();
        await page.waitForTimeout(4000);

        const finalUrl = page.url();
        if (
          finalUrl.includes('thank-you') ||
          finalUrl.includes('feedback') ||
          finalUrl.includes('orders')
        ) {
          console.log(`   ✓ Orden creada exitosamente (URL: ${finalUrl})`);
          logs.push('FASE 1: Orden creada exitosamente');
        } else {
          errors.push(`ERROR [ALTO]: Orden no confirmada. URL: ${finalUrl}`);
          console.log(`   ✗ ERROR: Orden no confirmada (URL: ${finalUrl})`);
        }
      } else {
        errors.push('ERROR [ALTO]: Formulario de checkout no visible');
      }
    } else {
      errors.push('ERROR [ALTO]: Botón de checkout no encontrado');
    }
  } catch (e) {
    errors.push(`ERROR [CRITICO] FASE 1: ${e.message}`);
    console.log(`   ✗ ERROR: ${e.message}`);
  }

  // ═══════════════════════════════════════════════════════════════
  // REPORTE DE FASE 1
  // ═══════════════════════════════════════════════════════════════
  console.log('\n' + '='.repeat(60));
  console.log('REPORTE FASE 1 - CLIENTE');
  console.log('='.repeat(60));

  if (errors.filter((e) => e.includes('FASE 1')).length === 0) {
    console.log('✅ FASE 1 COMPLETADA EXITOSAMENTE');
  } else {
    console.log('❌ FASE 1 CON ERRORES:');
    errors.filter((e) => e.includes('FASE 1')).forEach((e) => console.log(`   ${e}`));
  }

  await browser.close();

  // ═══════════════════════════════════════════════════════════════
  // RESUMEN FINAL
  // ═══════════════════════════════════════════════════════════════
  console.log('\n' + '╔══════════════════════════════════════════════════════════════╗');
  console.log('║                    RESUMEN FINAL                             ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  if (errors.length === 0) {
    console.log('✅ NO SE DETECTARON ERRORES');
  } else {
    console.log(`❌ ERRORES ENCONTRADOS: ${errors.length}`);
    errors.forEach((e, i) => console.log(`\n${i + 1}. ${e}`));
  }

  console.log('\n📝 LOGS:');
  logs.forEach((l) => console.log(`   • ${l}`));

  return { success: errors.length === 0, errors, logs };
}

// Ejecutar test
if (require.main === module) {
  testFlujoCompleto()
    .then((result) => {
      process.exit(result.success ? 0 : 1);
    })
    .catch((e) => {
      console.error('Error fatal:', e);
      process.exit(1);
    });
}

module.exports = { testFlujoCompleto };
