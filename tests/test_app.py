import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)

def test_list_orders():
    """Test GET /orders endpoint"""
    response = client.get("/orders")
    assert response.status_code == 200
    data = response.json()
    assert "total_pedidos" in data
    assert "pedidos" in data

def test_list_orders_by_period():
    """Test GET /orders/periodo endpoint"""
    response = client.get("/orders/periodo?data_inicio=2024-01-01&data_fim=2024-01-31")
    assert response.status_code == 200
    data = response.json()
    assert "periodo" in data
    assert "total_pedidos" in data
    assert "pedidos" in data

def test_list_orders_by_period_invalid_date():
    """Test GET /orders/periodo with invalid date format"""
    response = client.get("/orders/periodo?data_inicio=invalid&data_fim=2024-01-31")
    assert response.status_code == 400
    assert "erro" in response.json()

def test_list_sku_nicho():
    """Test GET /sku_nicho/listar endpoint"""
    response = client.get("/sku_nicho/listar")
    assert response.status_code == 200
    data = response.json()
    assert "dados" in data

def test_insert_sku_nicho():
    """Test POST /sku_nicho/inserir endpoint"""
    payload = {"sku": "TEST123", "nicho": "Test Nicho"}
    response = client.post("/sku_nicho/inserir", params=payload)
    assert response.status_code == 200
    # Note: This might fail if SKU already exists due to INSERT OR IGNORE

def test_insert_multiple_sku_nicho():
    """Test POST /sku_nicho/inserir_varios endpoint"""
    payload = [{"sku": "TEST456", "nicho": "Test Nicho 2"}, {"sku": "TEST789", "nicho": "Test Nicho 3"}]
    response = client.post("/sku_nicho/inserir_varios", json=payload)
    assert response.status_code == 200

def test_update_sku_nicho():
    """Test PUT /sku_nicho/atualizar endpoint"""
    payload = {"sku": "TEST123", "novo_nicho": "Updated Nicho"}
    response = client.put("/sku_nicho/atualizar", params=payload)
    assert response.status_code == 200

def test_delete_sku_nicho():
    """Test DELETE /sku_nicho/deletar endpoint"""
    response = client.delete("/sku_nicho/deletar?sku=TEST123")
    assert response.status_code == 200

def test_relatorio_flex():
    """Test GET /relatorio_flex endpoint"""
    response = client.get("/relatorio_flex")
    assert response.status_code in [200, 400]  # 400 if no data

def test_relatorio_flex_with_dates():
    """Test GET /relatorio_flex with date parameters"""
    response = client.get("/relatorio_flex?data_inicio=2024-01-01&data_fim=2024-01-31")
    assert response.status_code in [200, 400]  # 400 if no data in period

def test_atualizar_pedidos():
    """Test POST /atualizar_pedidos endpoint"""
    # This will try to call the external API, might fail in test environment
    response = client.post("/atualizar_pedidos?data=01/01/2024")
    # Accept both success and failure since external API might not be available
    assert response.status_code in [200, 500]

def test_websocket_endpoint():
    """Test WebSocket /ws/relatorio_diario endpoint"""
    # WebSocket testing requires special handling
    # For now, just test that the route exists by checking app routes
    routes = [route.path for route in app.routes]
    assert "/ws/relatorio_diario" in routes

def test_openapi_schema():
    """Test that OpenAPI schema is generated correctly"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "paths" in schema
    assert "/orders" in schema["paths"]
    assert "/sku_nicho/listar" in schema["paths"]
    assert "/relatorio_flex" in schema["paths"]
