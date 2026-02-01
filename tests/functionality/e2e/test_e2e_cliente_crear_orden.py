"""
Test E2E: Cliente crea orden con múltiples productos
URL: http://localhost:6080
"""

import pytest
from playwright.sync_api import Page, expect


def test_cliente_crear_orden_con_multiples_productos(page: Page):
    """
    Flujo: Cliente abre menú → agrega productos → verifica carrito → checkout → confirma orden

    Validaciones:
    - Campos obligatorios validados antes de agregar al carrito
    - Confirmación visual de orden creada
    """

    # ═══════════════════════════════════════════════════════════════
    # FASE 1: ABRIR MENÚ Y SELECCIONAR PRODUCTOS
    # ═══════════════════════════════════════════════════════════════

    # Abrir página del cliente
    page.goto("http://localhost:6080")
    page.wait_for_load_state("networkidle")

    # Verificar que el menú cargó
    expect(page.locator("#menu-sections")).to_be_visible(timeout=10000)

    # Contar productos disponibles
    productos = page.locator(".menu-item-card")
    expect(productos.first()).to_be_visible()

    # ═══════════════════════════════════════════════════════════════
    # FASE 2: AGREGAR PRODUCTO 1 (con validación de campos obligatorios)
    # ═══════════════════════════════════════════════════════════════

    # Click en primer producto
    productos.first().click()
    page.wait_for_timeout(1500)

    # Verificar que modal se abrió
    modal = page.locator("#item-modal.open, .modal--item-customization.active")
    expect(modal).to_be_visible(timeout=5000)

    # Verificar campos obligatorios
    nombre_producto = page.locator("#modal-item-name").text_content()
    assert nombre_producto is not None, "ERROR: Nombre del producto no visible"

    precio = page.locator("#modal-total-price").text_content()
    assert precio is not None, "ERROR: Precio no visible"

    # Si hay campos de modificación obligatorios, completarlos
    campos_obligatorios = page.locator(".modifier-group.required")
    for grupo in campos_obligatorios:
        opciones = grupo.locator(".modifier-option")
        if opciones.count() > 0:
            opciones.first().click()

    # Click en agregar al carrito
    page.locator("#modal-add-to-cart-btn").click()
    page.wait_for_timeout(1000)

    # Verificar que se agregó (carrito debe tener items)
    contador_carrito = page.locator("#cart-items-count").text_content()
    assert int(contador_carrito) >= 1, "ERROR: Producto no se agregó al carrito"

    # Cerrar modal
    page.locator(".modal-close").click()
    page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # FASE 3: AGREGAR PRODUCTO 2
    # ═══════════════════════════════════════════════════════════════

    productos.nth(1).click()
    page.wait_for_timeout(1500)

    # Verificar modal
    expect(page.locator("#item-modal.open, .modal--item-customization.active")).to_be_visible(
        timeout=5000
    )

    # Click en agregar
    page.locator("#modal-add-to-cart-btn").click()
    page.wait_for_timeout(1000)

    # Verificar contador actualizado
    contador_actualizado = page.locator("#cart-items-count").text_content()
    assert int(contador_actualizado) >= 2, "ERROR: Segundo producto no se agregó"

    # Cerrar modal
    page.locator(".modal-close").click()
    page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # FASE 4: VERIFICAR CARRITO
    # ═══════════════════════════════════════════════════════════════

    # Abrir carrito
    page.locator("[data-toggle-cart], .cart-btn").first().click()
    page.wait_for_timeout(1000)

    # Verificar items en carrito
    items_carrito = page.locator(".cart-item, .cart-item-card")
    expect(items_carrito.first()).to_be_visible()

    # Verificar que hay al menos 2 items
    assert items_carrito.count() >= 2, "ERROR: Items del carrito no visibles"

    # ═══════════════════════════════════════════════════════════════
    # FASE 5: IR A CHECKOUT
    # ═══════════════════════════════════════════════════════════════

    # Click en checkout
    page.locator("#checkout-btn").click()
    page.wait_for_timeout(2000)

    # Verificar formulario de checkout
    expect(page.locator("#checkout-form")).to_be_visible(timeout=5000)

    # ═══════════════════════════════════════════════════════════════
    # FASE 6: COMPLETAR FORMULARIO DE CHECKOUT
    # ═══════════════════════════════════════════════════════════════

    # Completar campos obligatorios
    page.fill("#customer-name", "LuArtX Test")
    page.fill("#customer-email", "luartx@gmail.com")
    page.fill("#customer-phone", "5551234567")

    # Seleccionar método de pago (Pagar después)
    page.locator('button:has-text("Pagar después")').click()
    page.wait_for_timeout(500)

    # ═══════════════════════════════════════════════════════════════
    # FASE 7: CONFIRMAR ORDEN
    # ═══════════════════════════════════════════════════════════════

    # Click en confirmar
    page.locator('button[type="submit"]').click()
    page.wait_for_timeout(5000)

    # Verificar que la orden fue creada
    current_url = page.url()
    assert (
        "thank-you" in current_url or "feedback" in current_url or "orders" in current_url
    ), f"ERROR: Orden no confirmada. URL: {current_url}"

    # ═══════════════════════════════════════════════════════════════
    # RESULTADO ESPERADO
    # ═══════════════════════════════════════════════════════════════
    # - Orden creada exitosamente
    # - Email de confirmación enviado a luartx@gmail.com
    # - Carrito con 2 productos
    # - Redirección a página de confirmación

    print("✅ Test completado: Orden creada exitosamente")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
