const { chromium } = require('playwright');

const CLIENT_URL = 'http://localhost:6080';

async function runTest() {
  console.log('╔══════════════════════════════════════════════════════════════╗');
  console.log('║        TEST E2E: CLIENTE CREA ORDEN                         ║');
  console.log('╚══════════════════════════════════════════════════════════════╝\n');

  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const page = await browser.newPage();

  const errors = [];
  const logs = [];

  // Capturar errores de consola
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(`JS ERROR: ${msg.text()}`);
    }
  });

  page.on('pageerror', (err) => {
    errors.push(`PAGE ERROR: ${err.message}`);
  });

  try {
    // 1. ABRIR MENÚ
    console.log('1. Abriendo menú...');
    await page.goto(CLIENT_URL, { waitUntil: 'domcontentloaded', timeout: 30000 });

    // Esperar a que el JavaScript renderice los productos
    await page.waitForTimeout(5000);

    // Verificar que el contenedor del menú existe
    const menuContainer = await page.locator('#menu-sections').count();
    if (menuContainer > 0) {
      console.log('   ✓ Contenedor de menú presente');
    } else {
      errors.push('ERROR: Contenedor #menu-sections no encontrado');
    }

    // 2. ESPERAR Y CONTAR PRODUCTOS
    console.log('\n2. Esperando productos...');

    // Método 1: Esperar a que aparezcan los productos
    try {
      await page.waitForSelector('.menu-item-card', { timeout: 10000 });
      console.log('   ✓ Selector de productos encontrado');
    } catch (e) {
      console.log('   ⚠ Timeout esperando productos, verificando HTML...');
    }

    // Método 2: Obtener productos por evaluate (más confiable)
    const productCount = await page.evaluate(() => {
      return document.querySelectorAll('.menu-item-card').length;
    });

    console.log(`   📦 Productos encontrados: ${productCount}`);

    if (productCount >= 2) {
      // Producto 1
      console.log('\n3. Agregando Producto 1...');
      await page.evaluate(() => {
        const products = document.querySelectorAll('.menu-item-card');
        if (products.length >= 1) {
          // Simular click real con eventos de mouse
          const el = products[0];
          const rect = el.getBoundingClientRect();
          const x = rect.left + rect.width / 2;
          const y = rect.top + rect.height / 2;

          el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, clientX: x, clientY: y }));
          el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true, clientX: x, clientY: y }));
          el.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: x, clientY: y }));
        }
      });
      await page.waitForTimeout(2000);

      // Verificar modal
      const modalOpen = await page.evaluate(() => {
        const modal = document.querySelector('#item-modal, .modal--item-customization');
        return modal && (modal.classList.contains('open') || modal.classList.contains('active'));
      });

      if (modalOpen) {
        console.log('   ✓ Modal abierto');

        // Verificar campos obligatorios
        const hasName = await page.evaluate(() => !!document.querySelector('#modal-item-name'));
        const hasPrice = await page.evaluate(() => !!document.querySelector('#modal-total-price'));

        if (hasName && hasPrice) {
          console.log('   ✓ Campos obligatorios visibles');
        }

        // Agregar al carrito
        await page.evaluate(() => {
          const btn = document.querySelector('#modal-add-to-cart-btn');
          if (btn) btn.click();
        });
        await page.waitForTimeout(1500);
        console.log('   ✓ Producto 1 agregado');

        // Cerrar modal
        await page.evaluate(() => {
          const close = document.querySelector('.modal-close, button[onclick*="close"]');
          if (close) close.click();
        });
        await page.waitForTimeout(1000);
      } else {
        errors.push('ERROR: Modal no se abrió');
      }

      // Producto 2
      console.log('\n4. Agregando Producto 2...');
      await page.evaluate(() => {
        const products = document.querySelectorAll('.menu-item-card');
        if (products.length >= 2) products[1].click();
      });
      await page.waitForTimeout(2000);

      await page.evaluate(() => {
        const btn = document.querySelector('#modal-add-to-cart-btn');
        if (btn) btn.click();
      });
      await page.waitForTimeout(1500);
      console.log('   ✓ Producto 2 agregado');

      await page.evaluate(() => {
        const close = document.querySelector('.modal-close');
        if (close) close.click();
      });
      await page.waitForTimeout(1000);
    } else {
      errors.push(`ERROR: No hay suficientes productos (encontrados: ${productCount})`);
      console.log(`   ✗ ERROR: Solo ${productCount} productos`);
    }

    // 5. VERIFICAR CARRITO
    console.log('\n5. Verificando carrito...');
    const cartCount = await page.evaluate(() => {
      const el = document.querySelector('#cart-items-count');
      return el ? el.textContent : '0';
    });
    console.log(`   📦 Items en carrito: ${cartCount}`);

    // 6. CHECKOUT
    console.log('\n6. Proceso de checkout...');

    // Asegurarse de que no hay modal abierto
    await page.evaluate(() => {
      const modals = document.querySelectorAll('.modal-overlay, .modal');
      modals.forEach((m) => m.classList.remove('open', 'active'));
    });
    await page.waitForTimeout(500);

    // Click en checkout usando evaluate
    await page.evaluate(() => {
      const btn = document.querySelector('#checkout-btn');
      if (btn) btn.click();
    });
    await page.waitForTimeout(3000);

    // Verificar formulario de checkout
    const checkoutForm = await page.evaluate(() => {
      return !!document.querySelector('#checkout-form');
    });

    if (checkoutForm) {
      console.log('   ✓ Formulario de checkout visible');

      // Llenar formulario
      await page.evaluate(() => {
        const name = document.querySelector('#customer-name');
        const email = document.querySelector('#customer-email');
        const phone = document.querySelector('#customer-phone');
        if (name) name.value = 'LuArtX Test';
        if (email) email.value = 'luartx@gmail.com';
        if (phone) phone.value = '5551234567';
      });
      console.log('   ✓ Formulario completado');

      // Método de pago
      await page.evaluate(() => {
        const btns = document.querySelectorAll('button');
        btns.forEach((b) => {
          if (b.textContent.includes('Pagar después')) b.click();
        });
      });
      await page.waitForTimeout(500);

      // Confirmar orden
      await page.evaluate(() => {
        const submit = document.querySelector('button[type="submit"]');
        if (submit) submit.click();
      });
      await page.waitForTimeout(5000);

      const finalUrl = page.url();
      console.log(`   📍 URL final: ${finalUrl}`);

      if (
        finalUrl.includes('thank-you') ||
        finalUrl.includes('feedback') ||
        finalUrl.includes('orders')
      ) {
        console.log('   ✅ ORDEN CREADA EXITOSAMENTE');
        logs.push('Orden creada exitosamente');
      } else {
        errors.push(`ERROR: Orden no confirmada. URL: ${finalUrl}`);
      }
    } else {
      errors.push('ERROR: Formulario de checkout no visible');
    }
  } catch (e) {
    errors.push(`ERROR: ${e.message}`);
  }

  // REPORTE
  console.log('\n' + '='.repeat(60));
  console.log('REPORTE');
  console.log('='.repeat(60));

  if (errors.length === 0) {
    console.log('✅ SIN ERRORES');
  } else {
    console.log(`❌ ${errors.length} ERRORES:`);
    errors.forEach((e, i) => console.log(`   ${i + 1}. ${e}`));
  }

  console.log('\n📝 LOGS:');
  logs.forEach((l) => console.log(`   • ${l}`));

  await browser.close();
  process.exit(errors.length === 0 ? 0 : 1);
}

runTest();
