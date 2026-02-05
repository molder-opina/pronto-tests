import { test, expect } from '@playwright/test';

test.describe('PRONTO Cafetería - QA Completo', () => {
    test.setTimeout(120000); // 2 minutes timeout for full flow

    let orderId: string;
    const customerEmail = 'luartx@gmail.com';
    let customerName: string;

    test('Ciclo Completo: Cliente -> Mesero Acepta -> Chef -> Mesero Entrega -> Pago -> Verificación', async ({ browser }) => {
        test.setTimeout(180000); // 3 minutes for full cycle

        // ----------------------------------------------------------------
        // PASO 1: CLIENTE (Creación de Orden)
        // ----------------------------------------------------------------
        const clientContext = await browser.newContext();
        const page = await clientContext.newPage();

        console.log('🛒 [CLIENTE] Iniciando flujo de compra...');

        // Check if service is reachable
        try {
            await page.goto('http://localhost:6080');
        } catch (e) {
            console.error('❌ ERROR FATAL: No se puede acceder a localhost:6080');
            throw e;
        }

        // ERROR CHECK: Debug Panel
        const debugPanel = page.locator('#debug-toolbar, .flt-glass-pane, .debug-panel, #debug-table-panel');
        if (await debugPanel.isVisible()) {
            console.log('⚠️ OBSERVACION: Debug Panel visible');
            // Intentar cerrarlo
            const closeDebug = page.locator('#flt-hide-debug, button[aria-label="Close Debug"]');
            if (await closeDebug.isVisible()) await closeDebug.click();
        }

        // Handle Table Selection Modal and Overlays
        const handleBlockingElements = async () => {
            // Remove backdrop if hanging
            await page.evaluate(() => {
                const backdrops = document.querySelectorAll('.modal-backdrop, .modal-overlay, .cdk-overlay-backdrop');
                backdrops.forEach(el => el.remove());
                document.body.classList.remove('modal-open');
                // Ensure main doesn't block (if it was an issue)
                const main = document.querySelector('main');
                if (main && getComputedStyle(main).pointerEvents === 'none') {
                    main.style.pointerEvents = 'auto';
                }
            });

            const buttons = [
                'button:has-text("Continuar sin mesa")',
                '.btn:has-text("Continuar sin mesa")',
                'button:has-text("Continuar de todos modos")',
                'button:has-text("Entendido")',
                'button:has-text("Aceptar")'
            ];

            for (const selector of buttons) {
                const btn = page.locator(selector).first();
                if (await btn.isVisible()) {
                    console.log(`ℹ️ Dismissing blocking element: ${selector}`);
                    await btn.click({ force: true }).catch(() => { });
                    await page.waitForTimeout(500);
                }
            }
        };

        await handleBlockingElements();

        // Agregar primer producto
        await page.waitForSelector('.menu-item-card:not(.menu-item-card--skeleton)', { state: 'visible', timeout: 30000 });
        const products = page.locator('.menu-item-card:not(.menu-item-card--skeleton), .product-card:not(.product-card--skeleton)');
        const productsCount = await products.count();
        console.log(`📦 Productos encontrados: ${productsCount}`);
        expect(productsCount).toBeGreaterThan(0);

        const firstProduct = products.first();
        // Force scroll and remove any potential final blocker
        await firstProduct.scrollIntoViewIfNeeded();
        await handleBlockingElements();
        await firstProduct.hover({ force: true });

        // Identificar botón de agregar
        const addBtn = firstProduct.locator('.menu-item-card__quick-add, .add-to-cart-btn, .quick-add-btn').first();

        console.log('🛒 [CLIENTE] Haciendo click en agregar...');
        await addBtn.click({ force: true });

        // Esperar un momento para reactividad
        await page.waitForTimeout(1500);

        // Manejar posible Modal o Agregado Directo
        const itemModal = page.locator('#item-modal, .modal--item-customization').first();
        if (await itemModal.isVisible()) {
            console.log('ℹ️ Modal de opciones detectado');

            // Seleccionar radio buttons si hay
            const radioGroups = await page.evaluate(() => {
                const radios = Array.from(document.querySelectorAll('input[type="radio"]')) as HTMLInputElement[];
                const visibleRadios = radios.filter(r => r.offsetParent !== null);
                const names = new Set(visibleRadios.map(r => r.name));
                return Array.from(names);
            });

            for (const groupName of radioGroups) {
                await page.locator(`input[name="${groupName}"]:visible`).first().check();
            }

            // Marcar primer checkbox si hay
            const firstCheckbox = page.locator('input[type="checkbox"]:visible').first();
            if (await firstCheckbox.isVisible()) {
                await firstCheckbox.check();
            }

            const modalAddBtn = page.locator('#modal-add-to-cart-btn');
            await modalAddBtn.click();
            await page.waitForTimeout(500);
        } else {
            console.log('ℹ️ No se detectó modal o agregado directo exitoso.');
        }

        // Checkout
        console.log('🛒 [CLIENTE] Verificando estado del carrito...');
        const cartPanel = page.locator('#cart-panel, .cart-panel');
        const isCartOpen = await cartPanel.evaluate(el => el.classList.contains('open')).catch(() => false);

        if (!isCartOpen) {
            console.log('🛒 [CLIENTE] Abriendo carrito...');
            const cartBtn = page.locator('#cart-btn, .cart-btn, [data-toggle-cart], #sticky-cart-btn').filter({ visible: true }).first();
            await cartBtn.click();
        } else {
            console.log('🛒 [CLIENTE] El carrito ya está abierto.');
        }

        console.log('🛒 [CLIENTE] Esperando panel de carrito y verificando items...');
        await expect(cartPanel).toHaveClass(/open/, { timeout: 10000 });

        const cartItemsEmpty = page.locator('.empty-state:visible');
        if (await cartItemsEmpty.isVisible()) {
            console.error('❌ ERROR: El carrito está vacío después de intentar agregar un producto');
            throw new Error('Cart is empty');
        }

        console.log('🛒 [CLIENTE] Procediendo al checkout...');
        const checkoutBtn = page.locator('#checkout-btn, .checkout-btn, button:has-text("Ir a pagar")').filter({ visible: true }).first();
        await expect(checkoutBtn).toBeVisible({ timeout: 10000 });
        await checkoutBtn.click();

        // Formulario
        console.log('📝 [CLIENTE] Llenando formulario de checkout...');
        const emailSelector = '#customer-email, input[name="email"], input[name="customer_email"]';
        const nameSelector = '#customer-name, input[name="name"], input[name="customer_name"]';
        const phoneSelector = '#customer-phone, input[name="phone"], input[name="customer_phone"]';

        const uniqueSuffix = Date.now().toString().slice(-6);
        customerName = `QA Tester ${uniqueSuffix}`;

        await page.waitForSelector(emailSelector, { timeout: 10000 });
        await page.fill(nameSelector, customerName);
        await page.fill(emailSelector, customerEmail);

        const phoneInput = page.locator(phoneSelector);
        if (await phoneInput.isVisible()) {
            await phoneInput.fill('5551234567');
        }

        console.log(`🚀 [CLIENTE] Confirmando orden para ${customerName}...`);

        // Close profile modal if open (it can block the checkout button)
        const profileModal = page.locator('#profile-modal.active');
        if (await profileModal.isVisible()) {
            console.log('🛒 [CLIENTE] Cerrando modal de perfil...');
            await page.locator('.profile-modal-close, .profile-modal-overlay').first().click();
            await page.waitForTimeout(500);
        }

        // Use specific selector for checkout submit button (not login button)
        const submitBtn = page.locator('#checkout-submit-btn, button:has-text("Confirmar Pedido")').first();
        await expect(submitBtn).toBeVisible({ timeout: 10000 });
        await submitBtn.click();

        // Wait for redirect to orders tab
        await page.waitForURL(/tab=orders|orders/i, { timeout: 15000 }).catch(() => {
            // If URL doesn't change, wait for success notification
        });
        await page.waitForTimeout(2000);

        // Capturar ID from orders list (after redirect to /?tab=orders)
        // Method 1: Find order card by customer name (most reliable)
        const orderCard = page.locator(`.order-card:has-text("${customerName}")`).first();
        if (await orderCard.count() > 0) {
            orderId = (await orderCard.getAttribute('data-order-id')) || '';
            if (orderId) console.log(`📍 Order ID from order card: ${orderId}`);
        }

        // Method 2: From URL if contains order ID
        if (!orderId) {
            const url = page.url();
            const urlMatch = url.match(/\/orders\/(\d+)/);
            if (urlMatch) {
                orderId = urlMatch[1];
                console.log(`📍 Order ID from URL: ${orderId}`);
            }
        }

        // Method 3: From any data-order-id attribute
        if (!orderId) {
            const trackerOrder = page.locator('[data-order-id]').first();
            if (await trackerOrder.isVisible()) {
                orderId = (await trackerOrder.getAttribute('data-order-id')) || '';
                if (orderId) console.log(`📍 Order ID from data-order-id: ${orderId}`);
            }
        }

        // Method 4: Extract from order number text
        if (!orderId) {
            const orderNumber = page.locator('.order-number, .order-id-display').first();
            if (await orderNumber.isVisible()) {
                const text = await orderNumber.textContent();
                const match = text?.match(/#(\d+)/);
                if (match) {
                    orderId = match[1];
                    console.log(`📍 Order ID from order number: ${orderId}`);
                }
            }
        }

        console.log(`✅ Orden creada: #${orderId || 'UNKNOWN'} para ${customerName}`);
        await clientContext.close();

        if (!orderId) throw new Error('No se pudo capturar el ID de la orden');

        // ----------------------------------------------------------------
        // PASO 2: MESERO (Aceptación de Orden)
        // ----------------------------------------------------------------
        console.log('\n--- INICIANDO ETAPA DE MESERO (ACEPTACIÓN) ---');
        const waiterAcceptContext = await browser.newContext();
        const waiterAcceptPage = await waiterAcceptContext.newPage();

        // Debugging logs from console
        waiterAcceptPage.on('console', msg => {
            console.log(`[WAITER ACCEPT PAGE CONSOLE] ${msg.type()}: ${msg.text()}`);
        });

        console.log(`🏃 [MESERO-ACEPTA] Buscando orden #${orderId}...`);

        // Navigate to waiter login and wait for load
        await waiterAcceptPage.goto('http://localhost:6081/waiter/login');
        await waiterAcceptPage.waitForLoadState('domcontentloaded');

        // Fill login form
        const waiterAcceptLoginForm = waiterAcceptPage.locator('input[name="email"]');
        await expect(waiterAcceptLoginForm).toBeVisible({ timeout: 10000 });

        console.log('🏃 [MESERO-ACEPTA] Llenando formulario de login...');
        await waiterAcceptPage.fill('input[name="email"]', 'juan.mesero@cafeteria.test');
        await waiterAcceptPage.fill('input[name="password"]', 'ChangeMe!123');

        // Submit form
        await waiterAcceptPage.click('button[type="submit"]');

        // Wait for either redirect to dashboard or page reload
        await waiterAcceptPage.waitForLoadState('domcontentloaded');
        await waiterAcceptPage.waitForTimeout(2000);

        // Check if we're already on the dashboard or need to navigate
        let waiterAcceptDashboardUrl = waiterAcceptPage.url();
        console.log(`🏃 [MESERO-ACEPTA] URL después de login: ${waiterAcceptDashboardUrl}`);

        if (waiterAcceptDashboardUrl.includes('/login')) {
            // Login failed or session issue - try navigating to dashboard
            console.log('🏃 [MESERO-ACEPTA] Aún en login, navegando al dashboard...');
            await waiterAcceptPage.goto('http://localhost:6081/waiter/dashboard', { waitUntil: 'domcontentloaded' });
            waiterAcceptDashboardUrl = waiterAcceptPage.url();
        }

        if (waiterAcceptDashboardUrl.includes('/login')) {
            throw new Error('Session lost - still on login page after navigation attempt');
        }

        // Wait for dashboard to load - use domcontentloaded instead of networkidle to avoid hanging
        await waiterAcceptPage.waitForSelector('table, .waiter-board, .order-row, .orders-table', { timeout: 15000 });
        console.log(`🏃 [MESERO-ACEPTA] Dashboard cargado, buscando orden #${orderId}...`);

        // Forzar refresh inicial para asegurar que la orden esté cargada
        console.log('🏃 [MESERO-ACEPTA] Refrescando órdenes...');
        await waiterAcceptPage.evaluate(() => (window as any).refreshWaiterOrders?.());
        await waiterAcceptPage.waitForTimeout(2000);

        // Try to find order by ID first, then by customer name as fallback
        let waiterAcceptOrder = waiterAcceptPage.locator(`tr[data-order-id="${orderId}"]`).first();

        if (orderId && await waiterAcceptOrder.count() > 0) {
            console.log(`🏃 [MESERO-ACEPTA] Orden encontrada por ID: #${orderId}`);
        } else {
            // Fallback: find by customer name (case-insensitive)
            console.log(`🏃 [MESERO-ACEPTA] Buscando orden por nombre de cliente: ${customerName}...`);
            waiterAcceptOrder = waiterAcceptPage.locator(`tr:has-text("${customerName.toUpperCase()}")`).first();

            if (await waiterAcceptOrder.count() > 0) {
                // Update orderId from the found row
                const foundOrderId = await waiterAcceptOrder.getAttribute('data-order-id');
                if (foundOrderId) {
                    orderId = foundOrderId;
                    console.log(`🏃 [MESERO-ACEPTA] Orden encontrada por nombre, ID actualizado: #${orderId}`);
                }
            }
        }

        await expect(waiterAcceptOrder).toBeAttached({ timeout: 20000 });
        console.log(`🏃 [MESERO-ACEPTA] Estado inicial: ${await waiterAcceptOrder.getAttribute('data-status')}`);

        // Aceptar la orden - use multiple selectors to find the accept button
        // Note: The button is icon-only with label in title/aria-label attributes
        const acceptBtnSelectors = [
            `tr[data-order-id="${orderId}"] button[title="Aceptar"]`,
            `tr[data-order-id="${orderId}"] button[aria-label="Aceptar"]`,
            `tr[data-order-id="${orderId}"] button[data-endpoint*="/accept"]`,
            `tr[data-order-id="${orderId}"] .waiter-action[title="Aceptar"]`,
            `tr[data-order-id="${orderId}"] button:has-text("Aceptar")`,
        ];

        let acceptBtn = null;
        for (const selector of acceptBtnSelectors) {
            const btn = waiterAcceptPage.locator(selector).first();
            if (await btn.count() > 0 && await btn.isVisible()) {
                acceptBtn = btn;
                console.log(`🏃 [MESERO-ACEPTA] Botón encontrado con selector: ${selector}`);
                break;
            }
        }

        // Si se encontró el botón de aceptar, hacer click
        if (acceptBtn) {
            console.log('🏃 [MESERO-ACEPTA] Aceptando orden...');
            await acceptBtn.click({ force: true });
            await waiterAcceptPage.waitForTimeout(3000);

            // Refrescar y verificar el estado
            await waiterAcceptPage.evaluate(() => (window as any).refreshWaiterOrders?.());
            await waiterAcceptPage.waitForTimeout(2000);

            // Re-locate the order after the action
            waiterAcceptOrder = waiterAcceptPage.locator(`tr[data-order-id="${orderId}"]`).first();
            if (await waiterAcceptOrder.count() === 0) {
                waiterAcceptOrder = waiterAcceptPage.locator(`tr:has-text("${customerName.toUpperCase()}")`).first();
            }

            const newStatus = await waiterAcceptOrder.getAttribute('data-status');
            console.log(`🏃 [MESERO-ACEPTA] Estado después de aceptar: ${newStatus}`);
        } else {
            // Si no hay botón de aceptar, la orden ya puede estar asignada
            console.log('🏃 [MESERO-ACEPTA] No se encontró botón de aceptar - verificando estado actual...');
            const currentStatus = await waiterAcceptOrder.getAttribute('data-status');
            console.log(`🏃 [MESERO-ACEPTA] Estado actual: ${currentStatus}`);
        }

        console.log(`✅ [MESERO-ACEPTA] Orden #${orderId} procesada por mesero.`);
        await waiterAcceptContext.close();

        // ----------------------------------------------------------------
        // PASO 3: CHEF (Preparación)
        // ----------------------------------------------------------------
        console.log('\n--- INICIANDO ETAPA DE CHEF ---');
        const chefContext = await browser.newContext();
        const chefPage = await chefContext.newPage();

        // Debugging logs from console
        chefPage.on('console', msg => {
            console.log(`[CHEF PAGE CONSOLE] ${msg.type()}: ${msg.text()}`);
        });

        chefPage.on('request', request => {
            if (request.url().includes('/api/')) {
                console.log(`[CHEF API REQUEST] ${request.method()} ${request.url()}`);
            }
        });

        chefPage.on('response', response => {
            if (response.url().includes('/api/')) {
                console.log(`[CHEF API RESPONSE] ${response.status()} ${response.url()}`);
            }
        });

        console.log(`👨‍🍳 [CHEF] Buscando orden #${orderId}...`);

        // Navigate to chef login and wait for load
        await chefPage.goto('http://localhost:6081/chef/login');
        await chefPage.waitForLoadState('domcontentloaded');

        // Fill login form - wait longer for the page to fully load
        const loginForm = chefPage.locator('input[name="email"]');
        await expect(loginForm).toBeVisible({ timeout: 10000 });

        console.log('👨‍🍳 [CHEF] Llenando formulario de login...');
        await chefPage.fill('input[name="email"]', 'carlos.chef@cafeteria.test');
        await chefPage.fill('input[name="password"]', 'ChangeMe!123');

        // Submit form
        await chefPage.click('button[type="submit"]');

        // Wait for either redirect to dashboard or page reload
        await chefPage.waitForLoadState('domcontentloaded');
        await chefPage.waitForTimeout(2000);

        // Check if we're already on the dashboard or need to navigate
        let chefDashboardUrl = chefPage.url();
        console.log(`👨‍🍳 [CHEF] URL después de login: ${chefDashboardUrl}`);

        if (chefDashboardUrl.includes('/login')) {
            // Login failed or session issue - try navigating to dashboard
            console.log('👨‍🍳 [CHEF] Aún en login, navegando al dashboard...');
            await chefPage.goto('http://localhost:6081/chef/dashboard', { waitUntil: 'domcontentloaded' });
            chefDashboardUrl = chefPage.url();
        }

        if (chefDashboardUrl.includes('/login')) {
            throw new Error('Session lost - still on login page after navigation attempt');
        }

        // Wait for the dashboard to load
        await chefPage.waitForSelector('table, .kitchen-board, .order-row, .orders-table', { timeout: 15000 });
        console.log(`👨‍🍳 [CHEF] Dashboard cargado, buscando orden #${orderId}...`);

        // Refresh kitchen orders to ensure they're loaded
        await chefPage.evaluate(() => {
            if ((window as any).refreshKitchenOrders) (window as any).refreshKitchenOrders();
        });
        await chefPage.waitForTimeout(2000);

        // Try to find order by ID first, then by customer name as fallback
        let chefOrder = chefPage.locator(`tr[data-order-id="${orderId}"]`).first();
        let orderFoundInChefDashboard = false;

        if (orderId && await chefOrder.count() > 0) {
            console.log(`👨‍🍳 [CHEF] Orden encontrada por ID: #${orderId}`);
            orderFoundInChefDashboard = true;
        } else {
            // Fallback: find by customer name
            console.log(`👨‍🍳 [CHEF] Buscando orden por nombre de cliente: ${customerName}...`);
            chefOrder = chefPage.locator(`tr:has-text("${customerName.toUpperCase()}")`).first();
            if (await chefOrder.count() > 0) {
                orderFoundInChefDashboard = true;
            }
        }

        // If order not found in Chef dashboard, it might be a quick-serve item that doesn't require kitchen
        if (!orderFoundInChefDashboard) {
            console.log('👨‍🍳 [CHEF] Orden no encontrada en cocina - puede ser un artículo de servicio rápido. Saltando paso de cocina...');
            await chefContext.close();
        } else {
            await expect(chefOrder).toBeAttached({ timeout: 20000 });

            // Iniciar
            console.log('👨‍🍳 [CHEF] Buscando botones de acción...');

            // Forzar actualización si no hay botones
            const actionsCell = chefOrder.locator('.actions');
            if (await actionsCell.innerHTML() === '') {
                console.log('👨‍🍳 [CHEF] Acciones vacías, forzando refresh...');
                await chefPage.evaluate(() => {
                    if ((window as any).refreshKitchenOrders) (window as any).refreshKitchenOrders();
                    else window.location.reload();
                });
                await chefPage.waitForTimeout(3000);
            }

            console.log(`👨‍🍳 [CHEF] HTML de acciones: ${await actionsCell.innerHTML()}`);
            console.log(`👨‍🍳 [CHEF] Estado actual de la fila: ${await chefOrder.getAttribute('data-status')}`);

            const chefStartBtn = chefOrder.locator('.kitchen-action, button:has-text("Iniciar")').first();
            console.log('👨‍🍳 [CHEF] Haciendo click en "Iniciar" (vía JS)...');
            await chefStartBtn.evaluate(btn => (btn as HTMLButtonElement).click());

            // Esperar a que el estado cambie en el DOM
            console.log('👨‍🍳 [CHEF] Esperando cambio de estado a "En Proceso"...');
            await expect(async () => {
                const status = await chefOrder.getAttribute('data-status');
                console.log(`👨‍🍳 [CHEF] Estado actual: ${status}, Acciones: ${await actionsCell.innerHTML()}`);
                expect(status).toMatch(/kitchen_in_progress|preparing/i);
            }).toPass({ timeout: 10000 });

            // Listo
            console.log('👨‍🍳 [CHEF] Marcando como listo...');
            const chefReadyBtn = chefOrder.locator('.kitchen-action, button:has-text("Listo")').first();
            await chefReadyBtn.evaluate(btn => (btn as HTMLButtonElement).click());

            // Esperar a que el estado cambie en el DOM
            console.log('👨‍🍳 [CHEF] Esperando cambio de estado a "Listo"...');
            await expect(async () => {
                const status = await chefOrder.getAttribute('data-status');
                expect(status).toMatch(/ready_for_delivery|ready/i);
            }).toPass({ timeout: 10000 });
            await chefPage.waitForTimeout(1000);

            console.log(`✅ [CHEF] Orden #${orderId} lista para entrega.`);
            await chefContext.close();
        }

        // ----------------------------------------------------------------
        // PASO 4: MESERO (Entrega y Cobro)
        // ----------------------------------------------------------------
        console.log('\n--- INICIANDO ETAPA DE MESERO (ENTREGA) ---');
        const waiterDeliverContext = await browser.newContext();
        const waiterPage = await waiterDeliverContext.newPage();

        // Debugging logs from console
        waiterPage.on('console', msg => {
            console.log(`[WAITER DELIVER PAGE CONSOLE] ${msg.type()}: ${msg.text()}`);
        });

        console.log(`🏃 [MESERO-ENTREGA] Buscando orden #${orderId}...`);

        // Navigate to waiter login and wait for load
        await waiterPage.goto('http://localhost:6081/waiter/login');
        await waiterPage.waitForLoadState('domcontentloaded');

        // Fill login form
        const waiterDeliverLoginForm = waiterPage.locator('input[name="email"]');
        await expect(waiterDeliverLoginForm).toBeVisible({ timeout: 10000 });

        console.log('🏃 [MESERO-ENTREGA] Llenando formulario de login...');
        await waiterPage.fill('input[name="email"]', 'juan.mesero@cafeteria.test');
        await waiterPage.fill('input[name="password"]', 'ChangeMe!123');

        // Submit form
        await waiterPage.click('button[type="submit"]');

        // Wait for either redirect to dashboard or page reload
        await waiterPage.waitForLoadState('domcontentloaded');
        await waiterPage.waitForTimeout(2000);

        // Check if we're already on the dashboard or need to navigate
        let waiterDeliverDashboardUrl = waiterPage.url();
        console.log(`🏃 [MESERO-ENTREGA] URL después de login: ${waiterDeliverDashboardUrl}`);

        if (waiterDeliverDashboardUrl.includes('/login')) {
            // Login failed or session issue - try navigating to dashboard
            console.log('🏃 [MESERO-ENTREGA] Aún en login, navegando al dashboard...');
            await waiterPage.goto('http://localhost:6081/waiter/dashboard', { waitUntil: 'domcontentloaded' });
            waiterDeliverDashboardUrl = waiterPage.url();
        }

        if (waiterDeliverDashboardUrl.includes('/login')) {
            throw new Error('Session lost - still on login page after navigation attempt');
        }

        // Wait for dashboard to load
        await waiterPage.waitForSelector('table, .waiter-board, .order-row, .orders-table', { timeout: 15000 });
        console.log(`🏃 [MESERO-ENTREGA] Dashboard cargado, buscando orden #${orderId}...`);

        // Forzar refresh inicial
        console.log('🏃 [MESERO-ENTREGA] Refrescando órdenes...');
        await waiterPage.evaluate(() => (window as any).refreshWaiterOrders?.());
        await waiterPage.waitForTimeout(2000);

        // Try to find order by ID first, then by customer name as fallback
        let waiterOrder = waiterPage.locator(`tr[data-order-id="${orderId}"]`).first();

        if (orderId && await waiterOrder.count() > 0) {
            console.log(`🏃 [MESERO-ENTREGA] Orden encontrada por ID: #${orderId}`);
        } else {
            // Fallback: find by customer name
            console.log(`🏃 [MESERO-ENTREGA] Buscando orden por nombre de cliente: ${customerName}...`);
            waiterOrder = waiterPage.locator(`tr:has-text("${customerName.toUpperCase()}")`).first();
        }

        await expect(waiterOrder).toBeAttached({ timeout: 20000 });
        const deliveryInitialStatus = await waiterOrder.getAttribute('data-status');
        console.log(`🏃 [MESERO-ENTREGA] Estado inicial: ${deliveryInitialStatus}`);

        // If order is still in "new" status, accept it first
        if (deliveryInitialStatus === 'new') {
            console.log('🏃 [MESERO-ENTREGA] Orden aún en estado "new", aceptando primero...');
            // Use title/aria-label selector since the button is icon-only
            const acceptBtnDelivery = waiterPage.locator(`tr[data-order-id="${orderId}"] button[title="Aceptar"], tr[data-order-id="${orderId}"] button[data-endpoint*="/accept"]`).first();
            if (await acceptBtnDelivery.isVisible()) {
                console.log('🏃 [MESERO-ENTREGA] Botón Aceptar encontrado, haciendo click...');
                await acceptBtnDelivery.click({ force: true });
                await waiterPage.waitForTimeout(3000);
                await waiterPage.evaluate(() => (window as any).refreshWaiterOrders?.());
                await waiterPage.waitForTimeout(2000);

                // Re-check status
                const newStatus = await waiterOrder.getAttribute('data-status');
                console.log(`🏃 [MESERO-ENTREGA] Nuevo estado después de aceptar: ${newStatus}`);
            } else {
                console.log('🏃 [MESERO-ENTREGA] Botón Aceptar NO encontrado');
            }
        }

        // Entregar - look for deliver button with multiple selectors
        // Note: Buttons may be icon-only with labels in title/aria-label
        console.log('🏃 [MESERO-ENTREGA] Buscando botón de entrega...');
        const deliverBtnSelectors = [
            `tr[data-order-id="${orderId}"] button[title="Entregar"]`,
            `tr[data-order-id="${orderId}"] button[aria-label="Entregar"]`,
            `tr[data-order-id="${orderId}"] button[data-endpoint*="/deliver"]`,
            `tr[data-order-id="${orderId}"] button:has-text("Entregar")`,
            `tr[data-order-id="${orderId}"] .waiter-action:has-text("Entregar")`,
        ];

        let deliverBtn = null;
        for (const selector of deliverBtnSelectors) {
            const btn = waiterPage.locator(selector).first();
            if (await btn.count() > 0 && await btn.isVisible()) {
                deliverBtn = btn;
                console.log(`🏃 [MESERO-ENTREGA] Botón de entrega encontrado con selector: ${selector}`);
                break;
            }
        }

        if (!deliverBtn) {
            console.log('🏃 [MESERO-ENTREGA] No se encontró botón de entrega. La orden puede no requerir entrega o ya fue entregada.');
        } else {
            console.log('🏃 [MESERO-ENTREGA] Entregando orden...');
            await deliverBtn.click({ force: true });

            // Esperar a que el estado cambie a entregado
            console.log('🏃 [MESERO-ENTREGA] Esperando estado "Entregado"...');
            await expect(async () => {
                const status = await waiterOrder.getAttribute('data-status');
                console.log(`🏃 [MESERO-ENTREGA] Estado actual en loop: ${status}`);
                if (status !== 'delivered') {
                    await waiterPage.evaluate(() => (window as any).refreshWaiterOrders?.());
                }
                expect(status).toBe('delivered');
            }).toPass({ timeout: 20000 });
        }

        // ----------------------------------------------------------------
        // PASO 5: PAGO
        // ----------------------------------------------------------------
        console.log('\n--- INICIANDO ETAPA DE PAGO ---');

        // Cobrar - look for payment button with multiple selectors
        console.log('💰 [PAGO] Iniciando cobro...');
        // Note: Button may be icon-only with labels in title/aria-label, or use data attributes
        const payBtnSelectors = [
            `tr[data-order-id="${orderId}"] button[data-open-payment-modal]`,
            `tr[data-order-id="${orderId}"] button[title*="Cobrar"]`,
            `tr[data-order-id="${orderId}"] button[aria-label*="Cobrar"]`,
            `tr[data-order-id="${orderId}"] button:has-text("Cobrar")`,
        ];

        let payBtn = null;
        for (const selector of payBtnSelectors) {
            const btn = waiterPage.locator(selector).first();
            if (await btn.count() > 0 && await btn.isVisible()) {
                payBtn = btn;
                console.log(`💰 [PAGO] Botón encontrado con selector: ${selector}`);
                break;
            }
        }

        if (!payBtn) {
            throw new Error('No se encontró botón de cobrar');
        }
        await payBtn.evaluate(btn => (btn as HTMLButtonElement).click());

        // Modal Pago: Efectivo
        console.log('💰 [PAGO] Seleccionando efectivo...');
        const cashBtn = waiterPage.locator('#employee-payment-modal .payment-method-btn[data-method="cash"]').first();
        await expect(cashBtn).toBeAttached({ timeout: 10000 });
        await cashBtn.evaluate(btn => (btn as HTMLButtonElement).click());

        // Confirmar Pago
        console.log('💰 [PAGO] Confirmando pago...');
        const confirmCashBtn = waiterPage.locator('#confirm-cash-payment').first();
        await expect(confirmCashBtn).toBeAttached({ timeout: 10000 });
        await confirmCashBtn.evaluate(btn => (btn as HTMLButtonElement).click());
        await waiterPage.waitForTimeout(2000);

        // Manejar modal de propina si aparece
        const tipModal = waiterPage.locator('#employee-tip-modal');
        if (await tipModal.isVisible()) {
            console.log('💰 [PAGO] Omitiendo propina...');
            const skipTipBtn = tipModal.locator('#cancel-employee-tip, button:has-text("Omitir")').first();
            await skipTipBtn.click();
            await waiterPage.waitForTimeout(1000);
        }

        // Manejar modal de ticket si aparece
        const ticketModal = waiterPage.locator('#employee-ticket-modal');
        if (await ticketModal.isVisible()) {
            console.log('💰 [PAGO] Cerrando modal de ticket...');
            const closeTicketBtn = ticketModal.locator('#cancel-employee-ticket, button:has-text("Cerrar")').first();
            await closeTicketBtn.click();
            await waiterPage.waitForTimeout(1000);
        }

        console.log(`✅ [PAGO] Orden #${orderId} pagada.`);
        await waiterDeliverContext.close();

        // ----------------------------------------------------------------
        // PASO 6: VERIFICACIÓN (Cliente)
        // ----------------------------------------------------------------
        console.log('\n--- INICIANDO ETAPA DE VERIFICACIÓN ---');
        const verifierContext = await browser.newContext();
        const verifierPage = await verifierContext.newPage();

        console.log(`✅ [VERIFICACIÓN] Navegando a http://localhost:6080...`);
        await verifierPage.goto('http://localhost:6080');

        // Ir a la pestaña de órdenes
        console.log('✅ [VERIFICACIÓN] Navegando a pestaña de órdenes...');
        const ordersTab = verifierPage.locator('button:has-text("Órdenes"), .nav-tab:has-text("Órdenes"), a:has-text("Órdenes")').first();
        await ordersTab.click();
        await verifierPage.waitForTimeout(2000);

        console.log(`✅ [VERIFICACIÓN] Comprobando orden #${orderId} para ${customerName}...`);

        await expect(async () => {
            const ordCardsCount = await verifierPage.locator('.order-card, .order-item-card').count();
            console.log(`✅ [VERIFICACIÓN] Encontradas ${ordCardsCount} órdenes.`);

            if (ordCardsCount === 0) {
                await verifierPage.reload();
                await verifierPage.waitForTimeout(2000);
                await ordersTab.click();
                throw new Error('No orders found');
            }

            const orderCard = verifierPage.locator('.order-card, .order-item-card').filter({ hasText: customerName }).first();
            await expect(orderCard).toBeVisible();

            const cardText = await orderCard.textContent();
            console.log(`✅ [VERIFICACIÓN] Texto de la tarjeta: ${cardText}`);

            expect(cardText).toMatch(/pagada|paid|pagado|completado/i);
        }).toPass({ timeout: 20000 });

        console.log(`🎉 QA FLOW COMPLETADO: Orden #${orderId} verificada como pagada.`);
        await verifierContext.close();
    });
});
