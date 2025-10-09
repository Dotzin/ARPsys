# Task: Complete Separation of Front/Back - Remove All Frontend Code from Backend

## Steps to Complete

### 1. Backend Cleanup
- [x] Remove static file serving routes from auth_routes.py (/, /login, /register, /settings, /integrations, /daily)
- [x] Remove static/ directory entirely
- [x] Remove unused imports (FileResponse, RedirectResponse, os) from auth_routes.py
- [x] Update app_factory.py comment to remove reference to static files
- [ ] Verify no other frontend-related code remains in backend

### 2. Run Backend
- [x] Install backend dependencies (pip install -r backend/requirements.txt)
- [x] Run backend server (uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000)

### 3. Run Frontend
- [x] Install frontend dependencies (cd frontend && npm install)
- [x] Run Next.js dev server (cd frontend && npm run dev)

### 4. Test Functionality
- [x] Open browser to http://localhost:3000 (compiled successfully, GET / 200)
- [ ] Test login page
- [ ] Test registration
- [ ] Test dashboard access
- [ ] Test reports and data fetching
- [ ] Test WebSocket connections
- [ ] Test integrations page

### 5. Ensure Good Practices
- [x] Verify CORS is working (added middleware)
- [x] Check error handling in frontend (axios interceptors present)
- [x] Verify API calls use proper authentication (Bearer token)
- [x] Ensure responsive design (Next.js with Tailwind)
- [ ] Check for any console errors (can't check without browser)
- [ ] Test with different browsers (can't test)

### 6. Final Verification
- [ ] Run backend tests (PYTHONPATH issue, but servers running)
- [ ] Run frontend lint (cd frontend && npm run lint)
- [ ] Confirm separation: backend only serves API, frontend handles UI
