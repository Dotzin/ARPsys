import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)


def test_full_order_workflow():
    """Test complete order workflow: insert SKU/nicho, then orders, then reports"""
    # 1. Insert SKU/nicho
    payload = {"sku": "INTTEST123", "nicho": "Integration Test Nicho"}
    response = client.post("/sku_nicho/inserir", params=payload)
    assert response.status_code == 200

    # 2. Verify SKU/nicho was inserted
    response = client.get("/sku_nicho/listar")
    assert response.status_code == 200
    data = response.json()
    sku_found = any(row[0] == "INTTEST123" for row in data["dados"])
    assert sku_found

    # 3. List orders (should work even with empty data)
    response = client.get("/orders")
    assert response.status_code == 200

    # 4. Test report generation
    response = client.get("/relatorio_flex")
    # Report might return 400 if no data, which is acceptable
    assert response.status_code in [200, 400]


def test_period_order_listing():
    """Test order listing by period"""
    # Test with valid date range
    response = client.get("/orders/periodo?data_inicio=2024-01-01&data_fim=2024-12-31")
    assert response.status_code == 200
    data = response.json()
    assert "periodo" in data
    assert "total_pedidos" in data
    assert "pedidos" in data


def test_sku_nicho_crud_operations():
    """Test complete CRUD operations for SKU/nicho"""
    test_sku = "CRUDTEST123"

    # Create
    response = client.post(
        "/sku_nicho/inserir", params={"sku": test_sku, "nicho": "CRUD Test"}
    )
    assert response.status_code == 200

    # Read (verify creation)
    response = client.get("/sku_nicho/listar")
    assert response.status_code == 200
    data = response.json()
    sku_found = any(row[0] == test_sku for row in data["dados"])
    assert sku_found

    # Update
    response = client.put(
        "/sku_nicho/atualizar",
        params={"sku": test_sku, "novo_nicho": "Updated CRUD Test"},
    )
    assert response.status_code == 200

    # Delete
    response = client.delete("/sku_nicho/deletar", params={"sku": test_sku})
    assert response.status_code == 200


def test_error_handling():
    """Test error handling for invalid inputs"""
    # Invalid date format
    response = client.get("/orders/periodo?data_inicio=invalid&data_fim=2024-01-31")
    assert response.status_code == 400
    assert "erro" in response.json()

    # Missing required parameters
    response = client.put("/sku_nicho/atualizar", params={"sku": "TEST"})
    assert response.status_code == 422  # Validation error


def test_websocket_route_registration():
    """Test that WebSocket route is properly registered"""
    # Check that the WebSocket route exists in the app
    websocket_routes = [
        route
        for route in app.routes
        if hasattr(route, "path") and route.path == "/ws/relatorio_diario"
    ]
    assert len(websocket_routes) == 1
    assert websocket_routes[0].path == "/ws/relatorio_diario"


def test_app_startup_and_shutdown():
    """Test that the app can start and shut down properly"""
    # This is more of a smoke test to ensure no import errors
    from app.app_factory import create_app

    test_app = create_app()
    assert test_app is not None
    assert len(test_app.routes) > 0


def test_database_connection():
    """Test that database connection works"""
    # Test basic database operations through API
    response = client.get("/orders")
    assert response.status_code == 200
    # If this works, database connection is functional


def test_service_dependencies():
    """Test that all service dependencies are properly injected"""
    # Test an endpoint that uses dependency injection
    response = client.get("/sku_nicho/listar")
    assert response.status_code == 200
    # If this works, dependency injection is working


def test_background_task_initialization():
    """Test that background task service is properly initialized"""
    # Check that the background task service exists in app state
    assert hasattr(app.state, "background_task_service")
    assert app.state.background_task_service is not None


def test_concurrent_requests():
    """Test handling multiple concurrent requests"""
    import asyncio
    import httpx

    async def make_requests():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            tasks = []
            for i in range(5):
                tasks.append(client.get("/orders"))
                tasks.append(client.get("/sku_nicho/listar"))
            responses = await asyncio.gather(*tasks)
            assert all(r.status_code == 200 for r in responses)

    # Run the async test
    asyncio.run(make_requests())
