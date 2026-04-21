# EDMS — Electronic Document Management System

[English](./README.md) | [简体中文](./README.zh-CN.md) 

Vue 3 + Element Plus frontend, Flask backend. Master data import, document editing, collaboration, comments, and approval workflows.

## Prerequisites

- Python 3.10+ (recommended)
- Node.js 18+ and **cnpm** (or npm) for the frontend

### Frontend package install (China / restricted networks)

If `npm` is slow or unavailable, use **cnpm** (same `package.json`):

```bash
cd frontend
npm install
npm run dev
```

Production build:

```bash
npm run build
```

Static files are emitted to `frontend/dist/`. Serve them behind any static host and proxy `/api` and `/socket.io` to the Flask server.

## Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py
```

API defaults to `http://127.0.0.1:5000`.

Environment variables (optional):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy URL (default `sqlite:///edms.db`) |
| `JWT_SECRET_KEY` | JWT signing secret |
| `SECRET_KEY` | Flask secret |
| `ADMIN_IMPORT_TOKEN` | If set, clients must send `X-Admin-Token` on master data import |

## Frontend dev proxy

`vite.config.ts` proxies `/api` and `/socket.io` to `http://127.0.0.1:5000`. Override API base with `VITE_API_BASE` and Socket.IO with `VITE_SOCKET_URL` if needed.

## Document API (library)

- `GET /api/documents?scope=mine|approved` — personal library (owned, shared, approvals, plus all approved) vs approved-only catalog.
- `GET /api/documents?...&status=draft|in_approval|approved|rejected` — optional status filter.
- `PATCH /api/documents/:id` — title / page settings **only** if the user may edit metadata (draft + owner or `edit` collaborator).
- `POST/GET /api/documents/:id/permissions` — owner only, **draft** only for changes; roles `view` | `edit` | `comment`.
- `DELETE /api/documents/:id/permissions/:user_id` — remove one grant (owner, draft).

## First-time setup (no users yet)

If login fails with "invalid login name", the database has no employees yet.

1. Open **`/admin`** in the browser (e.g. `http://localhost:5173/admin` in dev).
2. Upload your **Input Data.xlsx** (or the same layout: `Departments`, `Positions`, `Managers`, `Employees`).
3. Use any **Login** from the spreadsheet on the sign-in page (e.g. `user1`, `ruk1`).

If `ADMIN_IMPORT_TOKEN` is set on the server, enter it on the admin page (or send `X-Admin-Token`).

Once users exist and `ADMIN_IMPORT_TOKEN` is **not** set, importing again requires you to **sign in** first (destructive operation protection).

## Internationalization (i18n)

- Default UI locale is **English** (`en`).
- Users can switch to **中文** (`zh-CN`) via **Language** in the header (or on the login page).
- Choice is stored in `localStorage` under `edms_locale`.
- Element Plus component locale follows the same setting.

## Manual Deployment (Alternative)

For development or when Docker is not available, you can use the manual deployment scripts provided in the project root directory:

### Windows Scripts

- **`backend_start.bat`** - Start the Flask backend service (port 5000)
- **`frontend_start.bat`** - Start the Vue frontend service (port 5173)  
- **`start_manual.bat`** - Start both backend and frontend services simultaneously
- **`stop_manual.bat`** - Stop all running services

### Usage

#### Option A: Start services separately
```cmd
# In D:\HHH\EDMSV1 directory:
backend_start.bat
# In another terminal:
frontend_start.bat
```

#### Option B: One-click start/stop
```cmd
# Start both services
start_manual.bat

# Stop all services
stop_manual.bat
```

### Service Access
- **Frontend**: http://localhost:5173
- **Backend API**: http://127.0.0.1:5000

These scripts automatically handle:
- Python virtual environment creation and dependency installation
- Node.js dependency installation (with cnpm/npm fallback)
- Proper service startup and cleanup

## Docker Deployment (Recommended)

For production deployment, using Docker is the easiest way:

```bash
# Windows
docker\build.bat
bin\start.bat

# Linux/macOS
./docker/build.sh
./bin/start.sh
```

See [docker/README.md](docker/README.md) for detailed instructions.

## Documentation

- [docs/architecture.md](docs/architecture.md) — modules and data flow (if present)
- [docs/deployment.md](docs/deployment.md) — deployment notes
- [docs/user-guide.md](docs/user-guide.md) — end-user steps

## License

MIT (see [LICENSE](LICENSE) if shipped with the project).