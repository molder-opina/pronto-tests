"""
Test: Verificar estado del usuario y órdenes
"""

import pytest
from playwright.sync_api import Page, expect


def test_verificar_rol_y_scope_usuario(page: Page):
    """
    Verificar rol y scope del usuario logueado
    """
    page.goto("http://localhost:6081/waiter")

    # Esperar a que cargue la página
    page.wait_for_load_state("networkidle")

    # 1. Verificar rol del usuario
    rol_usuario = page.evaluate(
        """() => {
        return {
            employee_role: window.APP_DATA?.employee_role,
            employee_id: window.APP_DATA?.employee_id,
            employee_name: window.APP_DATA?.employee_name,
        };
    }"""
    )
    print(f"\n=== INFORMACIÓN DEL USUARIO ===")
    print(f"Rol: {rol_usuario.get('employee_role', 'No definido')}")
    print(f"ID: {rol_usuario.get('employee_id', 'No definido')}")
    print(f"Nombre: {rol_usuario.get('employee_name', 'No definido')}")

    # 2. Verificar cookies de autenticación
    cookies = page.context.cookies()
    print(f"\n=== COOKIES ===")
    for cookie in cookies:
        if (
            "access" in cookie["name"].lower()
            or "refresh" in cookie["name"].lower()
            or "session" in cookie["name"].lower()
        ):
            print(f"{cookie['name']}: {cookie['value'][:50]}...")

    # 3. Verificar todas las órdenes
    ordenes = page.evaluate(
        """() => {
        return (window.WAITER_ORDERS_DATA || []).map(o => ({
            id: o.id,
            workflow_status: o.workflow_status,
            status_display: o.status_display,
            waiter_id: o.waiter_id,
            customer_email: o.customer?.email,
            requires_kitchen: o.requires_kitchen
        }));
    }"""
    )

    print(f"\n=== ÓRDENES ===")
    for orden in ordenes:
        print(
            f"Orden {orden['id']}: Estado={orden['workflow_status']}, Display={orden['status_display']}, Waiter={orden['waiter_id']}, Email={orden.get('customer_email', 'N/A')}"
        )

    # Verificar si hay órdenes en estado 'new'
    ordenes_new = [o for o in ordenes if o["workflow_status"] == "new"]
    print(f"\nÓrdenes en estado 'new': {len(ordenes_new)}")

    # Verificar si hay órdenes en estado 'queued'
    ordenes_queued = [o for o in ordenes if o["workflow_status"] == "queued"]
    print(f"Órdenes en estado 'queued': {len(ordenes_queued)}")


def test_verificar_botones_por_estado(page: Page):
    """
    Verificar qué botones están disponibles para cada orden
    """
    page.goto("http://localhost:6081/waiter")
    page.wait_for_load_state("networkidle")

    # Obtener información de las órdenes y sus botones
    info_botones = page.evaluate(
        """() => {
        const orders = window.WAITER_ORDERS_DATA || [];
        return orders.map(order => ({
            id: order.id,
            status: order.workflow_status,
            display: order.status_display,
            botones: []
        }));
    }"""
    )

    print(f"\n=== BOTONES POR ORDEN ===")
    for info in info_botones:
        print(f"Orden {info['id']}: Estado={info['status']}, Display={info['display']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
