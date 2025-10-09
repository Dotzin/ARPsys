import pytest
from fastapi.testclient import TestClient
from app.main import app
import time

client = TestClient(app)

@pytest.fixture
def auth_token():
    """Fixture to get authentication token for tests"""
    # Register a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    client.post("/auth/register", json=user_data)

    # Login to get token
    login_data = {
        "username": "testuser",
        "password": "testpass123"
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    token_data = response.json()
    return token_data["access_token"]

@pytest.fixture
def auth_headers(auth_token):
    """Fixture to get authorization headers"""
    return {"Authorization": f"Bearer {auth_token}"}


def test_full_order_workflow(auth_headers):
    """Test complete order workflow: insert SKU/nicho, then orders, then reports"""
    # 1. Insert SKU/nicho
    payload = {"sku": "INTTEST123", "nicho": "Integration Test Nicho"}
    response = client.post("/sku_nicho/inserir", params=payload, headers=auth_headers)
    assert response.status_code == 200

    # 2. Verify SKU/nicho was inserted
    response = client.get("/sku_nicho/listar", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    sku_found = any(row[0] == "INTTEST123" for row in data["dados"])
    assert sku_found

    # 3. List orders (should work even with empty data)
    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200

    # 4. Test report generation
    response = client.get("/relatorio_flex", headers=auth_headers)
    # Report might return 400 if no data, which is acceptable
    assert response.status_code in [200, 400]


def test_period_order_listing(auth_headers):
    """Test order listing by period"""
    # Test with valid date range
    response = client.get("/orders/periodo?data_inicio=2024-01-01&data_fim=2024-12-31", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "periodo" in data
    assert "total_pedidos" in data
    assert "pedidos" in data


def test_sku_nicho_crud_operations(auth_headers):
    """Test complete CRUD operations for SKU/nicho"""
    test_sku = "CRUDTEST123"

    # Create
    response = client.post(
        "/sku_nicho/inserir", params={"sku": test_sku, "nicho": "CRUD Test"}, headers=auth_headers
    )
    assert response.status_code == 200

    # Read (verify creation)
    response = client.get("/sku_nicho/listar", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    sku_found = any(row[0] == test_sku for row in data["dados"])
    assert sku_found

    # Update
    response = client.put(
        "/sku_nicho/atualizar",
        params={"sku": test_sku, "novo_nicho": "Updated CRUD Test"}, headers=auth_headers
    )
    assert response.status_code == 200

    # Delete
    response = client.delete("/sku_nicho/deletar", params={"sku": test_sku}, headers=auth_headers)
    assert response.status_code == 200


def test_error_handling(auth_headers):
    """Test error handling for invalid inputs"""
    # Invalid date format
    response = client.get("/orders/periodo?data_inicio=invalid&data_fim=2024-01-31", headers=auth_headers)
    assert response.status_code == 400
    assert "erro" in response.json()

    # Missing required parameters
    response = client.put("/sku_nicho/atualizar", params={"sku": "TEST"}, headers=auth_headers)
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


def test_database_connection(auth_headers):
    """Test that database connection works"""
    # Test basic database operations through API
    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == 200
    # If this works, database connection is functional


def test_service_dependencies(auth_headers):
    """Test that all service dependencies are properly injected"""
    # Test an endpoint that uses dependency injection
    response = client.get("/sku_nicho/listar", headers=auth_headers)
    assert response.status_code == 200
    # If this works, dependency injection is working


def test_background_task_initialization():
    """Test that background task service is properly initialized"""
    # Check that the background task service exists in app state
    assert hasattr(app.state, "background_task_service")
    assert app.state.background_task_service is not None


def test_concurrent_requests(auth_headers):
    """Test handling multiple concurrent requests"""
    import asyncio
    import httpx

    async def make_requests():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver") as client:
            tasks = []
            for i in range(5):
                tasks.append(client.get("/orders", headers=auth_headers))
                tasks.append(client.get("/sku_nicho/listar", headers=auth_headers))
            responses = await asyncio.gather(*tasks)
            assert all(r.status_code == 200 for r in responses)

    # Run the async test
    asyncio.run(make_requests())
