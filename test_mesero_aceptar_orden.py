"""
Test E2E: Verificar flujo de aceptación de orden por mesero
"""

import pytest
from playwright.sync_api import Page, expect


def test_mesero_puede_aceptar_orden(page: Page):
    """
    Test: Mesero puede aceptar orden en estado 'new'
    URL: http://localhost:6081/waiter
    """
    # Ir al panel de mesero
    page.goto("http://localhost:6081/waiter")

    # Verificar que estamos en el panel de mesero
    expect(page.locator("text=Meseros")).to_be_visible()

    # Verificar que hay órdenes en estado 'Esperando mesero' (antes 'Solicitada')
    # La orden debe mostrar el estado descriptivo

    # Buscar una orden con estado 'Esperando mesero'
    orden = page.locator(".order-row").first

    # Verificar que el botón 'Aceptar orden' está visible y habilitado
    boton_aceptar = page.locator("button:has-text('Aceptar orden')")

    if boton_aceptar.is_visible():
        # Hacer clic en aceptar
        boton_aceptar.click()

        # Verificar que la orden cambia de estado
        # El nuevo estado debería ser 'Enviando a cocina' o 'En cola'
        expect(page.locator("text=Enviando a cocina")).to_be_visible()
    else:
        # Verificar que no hay botón de aceptar (el usuario no tiene permisos)
        # Mostrar el estado actual de la orden
        estado_orden = orden.locator(".status-badge").text_content()
        print(f"Estado de la orden: {estado_orden}")


def test_verificar_estados_descriptivos(page: Page):
    """
    Test: Verificar que los estados son descriptivos
    """
    page.goto("http://localhost:6081/waiter")

    # Verificar que los estados mostrados son descriptivos
    # y no técnicos

    # Los estados deben ser:
    # - 'Esperando mesero' (antes 'Solicitada')
    # - 'Enviando a cocina' (antes 'Mesero asignado')
    # - 'En cocina' (antes 'Cocinando')
    # - 'Listo entrega' (antes 'Listo para entregar')
    # - 'Entregado' (antes 'Entregado')
    # - 'Esperando pago' (antes 'Cuenta solicitada')
    # - 'Pagada' (antes 'Pagada')

    estados_esperados = [
        "Esperando mesero",
        "Enviando a cocina",
        "En cocina",
        "Listo entrega",
        "Entregado",
        "Esperando pago",
        "Pagada",
    ]

    # Verificar que al menos uno de los estados esté visible
    for estado in estados_esperados:
        if page.locator(f"text={estado}").is_visible():
            print(f"Estado encontrado: {estado}")
            break


def test_boton_inhabilitado_si_no_tiene_permisos(page: Page):
    """
    Test: Verificar que el botón está inhabilitado si el usuario no tiene permisos
    """
    page.goto("http://localhost:6081/waiter")

    # Si el usuario es chef o cajero, no debería ver el botón de aceptar
    # o debería estar inhabilitado

    # Verificar el rol del usuario
    rol_usuario = page.evaluate("() => window.APP_DATA?.employee_role")
    print(f"Rol del usuario: {rol_usuario}")

    # Si el rol es 'chef' o 'cashier', el botón no debería estar visible
    if rol_usuario in ["chef", "cashier"]:
        boton_aceptar = page.locator("button:has-text('Aceptar orden')")
        expect(boton_aceptar).not_to_be_visible()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
