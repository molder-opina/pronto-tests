"""
Test completo del flujo PRONTO cafetería usando Playwright.
Valida el ciclo completo desde cliente hasta cobro.

Flujo a probar:
1. Crea una orden en localhost:6080 (cliente) con múltiples productos
2. Confirma con email luartx@gmail.com
3. Chef en localhost:6081: Iniciar → Listo
4. Mesero: Entregar → Cobrar (Efectivo)
5. Verifica: email enviado, PDF descargable, orden en "Pagadas"
"""

import asyncio
import json
import time
from typing import Any

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright


class ProntoTester:
    """QA Tester para PRONTO cafetería."""

    def __init__(self):
        self.errors: list[dict[str, Any]] = []
        self.browsers = {}
        self.contexts = {}
        self.pages = {}

    def report_error(
        self, severity: str, description: str, location: str, impact: str, suggested_solution: str
    ):
        """Reporta un error en formato estandarizado."""
        error = {
            "severity": severity,
            "description": description,
            "location": location,
            "impact": impact,
            "suggested_solution": suggested_solution,
        }
        self.errors.append(error)
        print(f"❌ ERROR [{severity}]: {description}")
        print(f"   Ubicación: {location}")
        print(f"   Impacto: {impact}")
        print(f"   Solución sugerida: {suggested_solution}\n")

    def report_success(self, message: str):
        """Reporta un éxito."""
        print(f"✅ {message}\n")

    def report_warning(self, message: str):
        """Reporta una advertencia."""
        print(f"⚠️  {message}\n")

    async def setup(self):
        """Configura Playwright y abre navegadores."""
        print("🚀 Configurando Playwright...")
        playwright = await async_playwright().start()

        # Browser para cliente
        self.browsers["client"] = await playwright.chromium.launch(headless=False, slow_mo=500)
        self.contexts["client"] = await self.browsers["client"].new_context(
            viewport={"width": 375, "height": 812},  # Mobile
            locale="es-MX",
        )

        # Browser para chef
        self.browsers["chef"] = await playwright.chromium.launch(headless=False, slow_mo=500)
        self.contexts["chef"] = await self.browsers["chef"].new_context(
            viewport={"width": 1366, "height": 768},  # Desktop
            locale="es-MX",
        )

        # Browser para mesero/cashier
        self.browsers["waiter"] = await playwright.chromium.launch(headless=False, slow_mo=500)
        self.contexts["waiter"] = await self.browsers["waiter"].new_context(
            viewport={"width": 1366, "height": 768},  # Desktop
            locale="es-MX",
        )

        # Crear páginas
        self.pages["client"] = await self.contexts["client"].new_page()
        self.pages["chef"] = await self.contexts["chef"].new_page()
        self.pages["waiter"] = await self.contexts["waiter"].new_page()

        self.playwright = playwright
        self.report_success("Playwright configurado correctamente")

    async def step1_client_create_order(self):
        """
        PASO 1: Crear orden en localhost:6080 con múltiples productos.
        """
        print("=" * 60)
        print("PASO 1: Crear orden como cliente")
        print("=" * 60)

        try:
            # Navegar a cliente app
            await self.pages["client"].goto("http://localhost:6080", timeout=10000)
            await asyncio.sleep(2)

            # Verificar DEBUG PANEL
            debug_panel = await self.pages["client"].query_selector("#debug-table-panel")
            if debug_panel:
                is_visible = await debug_panel.is_visible()
                if is_visible:
                    self.report_error(
                        severity="HIGH",
                        description="DEBUG PANEL visible en producción",
                        location="http://localhost:6080 - #debug-table-panel",
                        impact="Permite manipular estado de mesas en producción",
                        suggested_solution="Verificar que DEBUG_MODE=False y DEBUG_AUTO_TABLE=False en config.py",
                    )
                else:
                    self.report_success("DEBUG PANEL oculto correctamente")
            else:
                self.report_success("DEBUG PANEL no encontrado o no visible")

            # Validar campos obligatorios en login/registro
            await self.validate_required_fields()

            # Agregar productos al carrito
            print("🛒 Agregando productos al carrito...")

            # Buscar productos (simular scroll)
            await self.pages["client"].evaluate(
                """
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """
            )
            await asyncio.sleep(1)

            # Intentar agregar productos
            try:
                # Buscar botones de agregar al carrito
                add_buttons = await self.pages["client"].query_selector_all(
                    "button[class*='add-to-cart'], button[class*='add-item']"
                )

                if len(add_buttons) == 0:
                    # Buscar productos por nombre
                    menu_items = await self.pages["client"].query_selector_all(
                        ".menu-item, [class*='product']"
                    )
                    if len(menu_items) > 0:
                        # Agregar primeros 2 productos
                        for i in range(min(2, len(menu_items))):
                            await menu_items[i].click()
                            await asyncio.sleep(0.5)
                            self.report_success(f"Producto {i + 1} agregado al carrito")
                    else:
                        self.report_error(
                            severity="CRITICAL",
                            description="No se encontraron productos en el menú",
                            location="http://localhost:6080 - Menu principal",
                            impact="El usuario no puede crear órdenes",
                            suggested_solution="Verificar que existan productos activos en base de datos",
                        )
                else:
                    for i in range(min(2, len(add_buttons))):
                        await add_buttons[i].click()
                        await asyncio.sleep(0.5)
                        self.report_success(f"Producto {i + 1} agregado al carrito")

            except Exception as e:
                self.report_error(
                    severity="HIGH",
                    description=f"Error al agregar productos: {str(e)}",
                    location="http://localhost:6080 - Agregar al carrito",
                    impact="No se puede completar la orden",
                    suggested_solution="Verificar event listeners de botones de carrito",
                )

            # Verificar carrito
            await asyncio.sleep(1)
            cart_badge = await self.pages["client"].query_selector(
                ".cart-count, [class*='cart-badge']"
            )

            if cart_badge:
                cart_count = await cart_badge.inner_text()
                self.report_success(f"Carrito tiene {cart_count} productos")
            else:
                self.report_warning("No se encontró indicador de carrito")

        except Exception as e:
            self.report_error(
                severity="CRITICAL",
                description=f"Error en paso 1 (crear orden): {str(e)}",
                location="http://localhost:6080",
                impact="No se puede iniciar el flujo",
                suggested_solution="Verificar que la app de cliente esté corriendo",
            )

    async def validate_required_fields(self):
        """Validar que los campos obligatorios tienen atributo 'required'."""
        print("📋 Validando campos obligatorios...")

        # Buscar formularios y campos con validación
        required_fields = await self.pages["client"].query_selector_all(
            "input[required], select[required], textarea[required]"
        )

        if required_fields:
            self.report_success(
                f"Se encontraron {len(required_fields)} campos con validación 'required'"
            )

            # Verificar que algunos campos clave estén marcados
            email_inputs = await self.pages["client"].query_selector_all(
                "input[type='email'][required]"
            )
            if email_inputs:
                self.report_success("Campos email tienen validación 'required'")
            else:
                self.report_warning("No se encontraron campos email con 'required'")

            phone_inputs = await self.pages["client"].query_selector_all(
                "input[type='tel'][required]"
            )
            if phone_inputs:
                self.report_success("Campos teléfono tienen validación 'required'")
            else:
                self.report_warning("No se encontraron campos teléfono con 'required'")
        else:
            self.report_error(
                severity="MEDIUM",
                description="No se encontraron campos con validación 'required'",
                location="http://localhost:6080",
                impact="Los usuarios pueden enviar formularios sin datos requeridos",
                suggested_solution="Agregar atributo 'required' a campos obligatorios en HTML",
            )

    async def step2_confirm_with_email(self):
        """
        PASO 2: Confirmar con email luartx@gmail.com.
        """
        print("=" * 60)
        print("PASO 2: Confirmar orden con email")
        print("=" * 60)

        try:
            # Buscar campo de email en checkout
            email_input = await self.pages["client"].query_selector(
                "input[type='email'], input[name*='email']", timeout=5000
            )

            if email_input:
                await email_input.click()
                await email_input.fill("")
                await email_input.type("luartx@gmail.com")
                self.report_success("Email ingresado: luartx@gmail.com")

                # Buscar botón de confirmar/checkout
                checkout_button = await self.pages["client"].query_selector(
                    "button[type='submit'], button[class*='checkout'], button[class*='confirm']",
                    timeout=3000,
                )

                if checkout_button:
                    # Hacer screenshot antes de confirmar
                    await self.pages["client"].screenshot(
                        path="screenshots/step2_before_checkout.png"
                    )

                    await checkout_button.click()
                    await asyncio.sleep(2)

                    self.report_success("Botón de confirmar presionado")

                    # Verificar confirmación visual de email
                    await self.verify_email_confirmation()

                else:
                    self.report_error(
                        severity="CRITICAL",
                        description="No se encontró botón de confirmar/checkout",
                        location="http://localhost:6080 - Checkout",
                        impact="El usuario no puede completar la orden",
                        suggested_solution="Agregar botón de confirmar con clase/clara acción",
                    )
            else:
                self.report_error(
                    severity="CRITICAL",
                    description="No se encontró campo de email",
                    location="http://localhost:6080 - Checkout",
                    impact="El usuario no puede confirmar la orden",
                    suggested_solution="Agregar campo de email con type='email' en formulario de checkout",
                )

        except Exception as e:
            self.report_error(
                severity="CRITICAL",
                description=f"Error en paso 2 (confirmar email): {str(e)}",
                location="http://localhost:6080",
                impact="No se puede confirmar la orden",
                suggested_solution="Verificar flujo de checkout",
            )

    async def verify_email_confirmation(self):
        """Verificar confirmación visual de email enviado."""
        print("📧 Verificando confirmación visual de email...")

        try:
            # Buscar mensaje de confirmación de email
            confirmation_message = await self.pages["client"].query_selector(
                "[class*='email-sent'], [class*='confirmation'], [class*='thank-you']", timeout=3000
            )

            if confirmation_message:
                message_text = await confirmation_message.inner_text()
                self.report_success(f"Confirmación visible: {message_text[:50]}")

                # Hacer screenshot
                await self.pages["client"].screenshot(
                    path="screenshots/step2_email_confirmation.png"
                )
            else:
                self.report_warning(
                    "No se encontró confirmación visual de email enviado. "
                    "Es posible que el email se envíe en segundo plano."
                )

        except Exception as e:
            self.report_warning(f"Error al verificar confirmación de email: {str(e)}")

    async def step3_chef_workflow(self):
        """
        PASO 3: Chef en localhost:6081: Iniciar → Listo.
        """
        print("=" * 60)
        print("PASO 3: Chef inicia y completa órdenes")
        print("=" * 60)

        try:
            # Navegar a app de empleados
            await self.pages["chef"].goto("http://localhost:6081/waiter/login", timeout=10000)
            await asyncio.sleep(2)

            # Iniciar sesión como chef
            # Nota: Usamos el login de mesero pero debería redirigir según rol
            # En producción habría login específico para chef
            email_input = await self.pages["chef"].query_selector("input[type='email']")
            password_input = await self.pages["chef"].query_selector("input[type='password']")

            if email_input and password_input:
                await email_input.fill("chef@pronto.test")
                await password_input.fill("chef123")

                login_button = await self.pages["chef"].query_selector("button[type='submit']")
                if login_button:
                    await login_button.click()
                    await asyncio.sleep(2)

                    # Buscar órdenes en cocina
                    print("🍳 Buscando órdenes en cocina...")

                    # Intentar encontrar botón de "Iniciar preparación" o similar
                    start_buttons = await self.pages["chef"].query_selector_all(
                        "button[class*='start'], button[class*='iniciar']"
                    )

                    if start_buttons:
                        self.report_success("Se encontraron botones de iniciar preparación")

                        for btn in start_buttons[:1]:  # Iniciar primera orden
                            await btn.click()
                            await asyncio.sleep(1)
                            self.report_success("Orden iniciada por chef")

                        # Esperar y marcar como lista
                        await asyncio.sleep(2)
                        ready_buttons = await self.pages["chef"].query_selector_all(
                            "button[class*='ready'], button[class*='listo']"
                        )

                        if ready_buttons:
                            await ready_buttons[0].click()
                            self.report_success("Orden marcada como lista por chef")

                            # Screenshot de cocina
                            await self.pages["chef"].screenshot(
                                path="screenshots/step3_chef_ready.png"
                            )
                        else:
                            self.report_error(
                                severity="MEDIUM",
                                description="No se encontró botón de marcar como listo",
                                location="http://localhost:6081 - Panel cocina",
                                impact="El chef no puede completar el flujo",
                                suggested_solution="Agregar botón para marcar orden como lista",
                            )
                    else:
                        self.report_error(
                            severity="HIGH",
                            description="No se encontraron órdenes para preparar",
                            location="http://localhost:6081 - Panel cocina",
                            impact="El chef no puede iniciar su trabajo",
                            suggested_solution="Verificar que existan órdenes en cola",
                        )
            else:
                self.report_error(
                    severity="CRITICAL",
                    description="No se encontró formulario de login de chef",
                    location="http://localhost:6081/waiter/login",
                    impact="No se puede acceder como chef",
                    suggested_solution="Verificar endpoint de login de chef",
                )

        except Exception as e:
            self.report_error(
                severity="CRITICAL",
                description=f"Error en paso 3 (chef workflow): {str(e)}",
                location="http://localhost:6081",
                impact="El chef no puede completar órdenes",
                suggested_solution="Verificar panel de cocina",
            )

    async def step4_waiter_deliver_collect(self):
        """
        PASO 4: Mesero: Entregar → Cobrar (Efectivo).
        """
        print("=" * 60)
        print("PASO 4: Mesero entrega y cobra orden")
        print("=" * 60)

        try:
            # Ir a dashboard de mesero
            await self.pages["waiter"].goto("http://localhost:6081/waiter/dashboard", timeout=10000)
            await asyncio.sleep(2)

            # Buscar botón de Entregar
            deliver_buttons = await self.pages["waiter"].query_selector_all(
                "button[class*='deliver'], button[class*='entregar']"
            )

            if deliver_buttons:
                self.report_success("Se encontraron botones de entregar")

                # Entregar orden
                await deliver_buttons[0].click()
                await asyncio.sleep(1)
                self.report_success("Orden entregada por mesero")

                # Buscar botón de Cobrar
                pay_buttons = await self.pages["waiter"].query_selector_all(
                    "button[class*='pay'], button[class*='cobrar']"
                )

                if pay_buttons:
                    # Hacer screenshot antes de cobrar
                    await self.pages["waiter"].screenshot(path="screenshots/step4_before_pay.png")

                    await pay_buttons[0].click()
                    await asyncio.sleep(2)
                    self.report_success("Botón de cobrar presionado")

                    # Seleccionar método de pago (Efectivo)
                    cash_option = await self.pages["waiter"].query_selector(
                        "input[value='cash'], [class*='cash'], [class*='efectivo']"
                    )

                    if cash_option:
                        await cash_option.click()
                        await asyncio.sleep(1)

                        # Confirmar pago
                        confirm_pay_button = await self.pages["waiter"].query_selector(
                            "button[type='submit'], button[class*='confirm']"
                        )

                        if confirm_pay_button:
                            await confirm_pay_button.click()
                            await asyncio.sleep(2)

                            # Verificar estado de orden (Pagada)
                            await self.verify_order_paid()

                        else:
                            self.report_error(
                                severity="HIGH",
                                description="No se encontró botón de confirmar pago",
                                location="http://localhost:6081 - Modal pago",
                                impact="No se puede completar el cobro",
                                suggested_solution="Agregar botón de confirmar en modal de pago",
                            )
                    else:
                        self.report_error(
                            severity="HIGH",
                            description="No se encontró opción de pago en efectivo",
                            location="http://localhost:6081 - Modal pago",
                            impact="No se puede seleccionar método de pago",
                            suggested_solution="Verificar opciones de método de pago",
                        )

                else:
                    self.report_error(
                        severity="HIGH",
                        description="No se encontró botón de cobrar",
                        location="http://localhost:6081 - Panel mesero",
                        impact="El mesero no puede cobrar órdenes",
                        suggested_solution="Agregar botón de cobrar en panel de mesero",
                    )
            else:
                self.report_error(
                    severity="HIGH",
                    description="No se encontraron órdenes para entregar",
                    location="http://localhost:6081 - Panel mesero",
                    impact="El mesero no puede completar su trabajo",
                    suggested_solution="Verificar que existan órdenes listas para entregar",
                )

        except Exception as e:
            self.report_error(
                severity="CRITICAL",
                description=f"Error en paso 4 (mesero workflow): {str(e)}",
                location="http://localhost:6081",
                impact="El mesero no puede completar órdenes",
                suggested_solution="Verificar panel de mesero",
            )

    async def verify_order_paid(self):
        """Verificar que la orden está en estado Pagada."""
        print("💰 Verificando estado de orden (Pagada)...")

        try:
            # Buscar indicador de estado "Pagada" o similar
            paid_status = await self.pages["waiter"].query_selector(
                "[class*='paid'], [class*='pagada'], [status*='paid']", timeout=3000
            )

            if paid_status:
                status_text = await paid_status.inner_text()
                self.report_success(f"Estado de orden: {status_text}")

                # Screenshot final
                await self.pages["waiter"].screenshot(path="screenshots/step4_order_paid.png")

                # Verificar transición de estado (no "ATRASADO" sin razón)
                await self.verify_no_invalid_status()
            else:
                self.report_error(
                    severity="HIGH",
                    description="No se encontró indicador de orden pagada",
                    location="http://localhost:6081 - Panel mesero",
                    impact="No se puede verificar estado final de orden",
                    suggested_solution="Agregar indicador visual de estado pagada",
                )

        except Exception as e:
            self.report_warning(f"Error al verificar estado pagada: {str(e)}")

    async def verify_no_invalid_status(self):
        """Verificar que no exista estado 'ATRASADO' sin razón."""
        print("⚠️  Verificando estados inválidos...")

        try:
            # Buscar texto "ATRASADO" o "ATRASADA"
            delayed_text = await self.pages["waiter"].query_selector(
                ":text('ATRASADO'), :text('ATRASADA')", timeout=2000
            )

            if delayed_text:
                self.report_error(
                    severity="HIGH",
                    description="Estado 'ATRASADO' visible sin razón/justificación",
                    location="http://localhost:6081 - Panel mesero",
                    impact="Estado confuso para usuario, posible error en lógica de transiciones",
                    suggested_solution="Agregar justificación obligatoria para estado ATRASADO o usar estado más descriptivo",
                )
            else:
                self.report_success("No se encontró estado 'ATRASADO' sin justificación")

        except Exception as e:
            self.report_warning(f"Error al verificar estados inválidos: {str(e)}")

    async def step5_verify_email_and_pdf(self):
        """
        PASO 5: Verifica: email enviado, PDF descargable, orden en "Pagadas".
        """
        print("=" * 60)
        print("PASO 5: Verificar email y PDF")
        print("=" * 60)

        try:
            # Ir a tabla de pagadas
            await self.pages["waiter"].goto("http://localhost:6081", timeout=10000)
            await asyncio.sleep(2)

            # Buscar tabla de pagadas/órdenes completas
            paid_orders_tab = await self.pages["waiter"].query_selector(
                "[class*='paid'], [href*='paid'], [class*='completed']", timeout=3000
            )

            if paid_orders_tab:
                await paid_orders_tab.click()
                await asyncio.sleep(1)
                self.report_success("Tab de pagadas encontrada")

                # Buscar botón de generar PDF o enviar email
                pdf_buttons = await self.pages["waiter"].query_selector_all(
                    "button[class*='pdf'], button[class*='email'], [download*='pdf']"
                )

                if pdf_buttons:
                    self.report_success(f"Se encontraron {len(pdf_buttons)} botones de PDF/email")

                    # Intentar generar PDF
                    for btn in pdf_buttons[:1]:  # Primer botón
                        await btn.click()
                        await asyncio.sleep(2)

                        # Verificar si hay confirmación visual
                        pdf_confirmation = await self.pages["waiter"].query_selector(
                            "[class*='pdf-sent'], [class*='email-sent'], [class*='generated']",
                            timeout=2000,
                        )

                        if pdf_confirmation:
                            conf_text = await pdf_confirmation.inner_text()
                            self.report_success(f"Confirmación visible: {conf_text[:50]}")
                        else:
                            self.report_warning(
                                "No se encontró confirmación visual de PDF/email generado"
                            )
                else:
                    self.report_error(
                        severity="HIGH",
                        description="No se encontraron botones de PDF/email en tabla de pagadas",
                        location="http://localhost:6081 - Tabla pagadas",
                        impact="No se puede generar PDF o reenviar email",
                        suggested_solution="Agregar botones para generar PDF y enviar email en tabla de pagadas",
                    )
            else:
                self.report_error(
                    severity="HIGH",
                    description="No se encontró tab de pagadas",
                    location="http://localhost:6081",
                    impact="No se puede verificar órdenes pagadas ni generar PDF",
                    suggested_solution="Agregar sección de órdenes pagadas/terminadas",
                )

        except Exception as e:
            self.report_error(
                severity="HIGH",
                description=f"Error en paso 5 (verificar email/PDF): {str(e)}",
                location="http://localhost:6081",
                impact="No se puede verificar entrega de email/PDF",
                suggested_solution="Verificar funcionalidad de PDF y email",
            )

    def generate_report(self):
        """Genera reporte completo de errores."""
        print("\n" + "=" * 60)
        print("REPORTE DE ERRORES - PRONTO CAFETERÍA")
        print("=" * 60 + "\n")

        if not self.errors:
            print("✅ No se encontraron errores críticos")
            print("✅ El flujo funciona correctamente")
        else:
            print(f"⚠️  Se encontraron {len(self.errors)} errores:\n")
            for i, error in enumerate(self.errors, 1):
                print(f"ERROR #{i}")
                print(f"  Severidad: {error['severity']}")
                print(f"  Descripción: {error['description']}")
                print(f"  Ubicación: {error['location']}")
                print(f"  Impacto: {error['impact']}")
                print(f"  Solución sugerida: {error['suggested_solution']}")
                print()

        print("=" * 60)
        print("PUNTOS A VERIFICAR:")
        print("=" * 60)
        print("✓ Validación de campos obligatorios ANTES de agregar al carrito")
        print("✓ Confirmación visual de email enviado")
        print("✓ Generación correcta de PDF")
        print("✓ Generación correcta de email")
        print("✓ Generación de email y guardar PDF desde el tab de pagadas")
        print("✓ No existe DEBUG PANEL en producción")
        print("✓ Estados transicionan correctamente (no 'ATRASADO' sin razón)")
        print("=" * 60 + "\n")

        # Guardar reporte en JSON
        with open("test_results.json", "w", encoding="utf-8") as f:
            json.dump(
                {"timestamp": time.time(), "total_errors": len(self.errors), "errors": self.errors},
                f,
                indent=2,
                ensure_ascii=False,
            )

        print("📄 Reporte guardado en test_results.json")

    async def cleanup(self):
        """Limpia recursos."""
        print("\n🧹 Limpiando recursos...")

        for page in self.pages.values():
            await page.close()

        for context in self.contexts.values():
            await context.close()

        for browser in self.browsers.values():
            await browser.close()

        await self.playwright.stop()
        self.report_success("Recursos limpiados")


async def main():
    """Ejecuta pruebas completas."""
    import os

    # Crear directorio de screenshots
    os.makedirs("screenshots", exist_ok=True)

    tester = ProntoTester()

    try:
        await tester.setup()

        # Ejecutar flujo completo
        await tester.step1_client_create_order()
        await tester.step2_confirm_with_email()
        await tester.step3_chef_workflow()
        await tester.step4_waiter_deliver_collect()
        await tester.step5_verify_email_and_pdf()

        # Generar reporte
        tester.generate_report()

    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
