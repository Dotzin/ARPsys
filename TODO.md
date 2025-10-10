# Task: Fix API errors, CORS, WebSocket issues, and add sale hour to orders

## Plan Breakdown

### 1. Fix SQLite query in report_service.py
- [x] Change BETWEEN to >= and <= in _fetch_data_from_db to avoid InterfaceError

### 2. Add sale hour to orders list
- [x] Include "hour" field in pedidos_lista in generate_relatorio_flex

### 3. Update CORS configuration
- [x] Set allow_origins to ["*"] in app_factory.py for broader access

### 4. Add logging to WebSocket
- [x] Enhance logging in websocket_endpoint for connection debugging

### 5. Followup: Restart and Test
- [ ] Restart the backend server (e.g., run `uvicorn app.main:app --reload` in backend directory)
- [ ] Test /relatorios/diario and /relatorios/flex endpoints (should return 200 without errors)
- [ ] Verify WebSocket connections in frontend dashboard (no disconnections, logs show successful connects)
- [ ] Check orders display includes sale hour in reports/orders page
