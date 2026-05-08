# EDMS — Enterprise Document Management System

[English](./README.md) | [简体中文](./README.zh-CN.md) 

Enterprise-grade document management system built with Vue 3 + Element Plus frontend and Flask backend. Supports Master Data management, multi-space categorization, AI-powered generation, real-time collaborative editing, version diffing, interactive comments, and full approval workflows.

## ✨ Core Features

- **Multi-Space Categorization**: Break free from traditional folder structures. Documents can be associated with multiple "Knowledge Spaces" (Many-to-Many) for flexible multi-dimensional management.
- **AI-Powered Intelligence**: Built-in AI assistant for conversational document generation, knowledge Q&A, and "Image-to-Doc" (OCR + Smart Layout) capabilities.
- **Real-time Collab & Versioning**: WebSocket-based multi-user real-time editing with integrated version history management and side-by-side Diff views.
- **Approval Workflows**: Complete document lifecycle management covering Draft, In Approval, Approved, and Rejected states.
- **Flexible Access Control**: Multi-dimensional RBAC permission system based on Users, Departments, and Spaces (Read, Edit, Comment).
- **Blockchain Traceability**: Integrated Mock blockchain service for hashing and timestamping core documents to ensure data integrity and non-repudiation.
- **Full-Stack i18n**: Seamless switching between English and Chinese, including localization of system-generated labels, space names, and department titles.

## 🛠️ Prerequisites

- Python 3.10+ (Recommended)
- Node.js 18+
- Docker & Docker Compose (Optional for containerized deployment)

## 🚀 Quick Start (Local Development)

### 1. Frontend Setup

```bash
cd sources/frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173` by default.

### 2. Backend Setup

```bash
cd sources/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate

pip install -r requirements.txt
python wsgi.py
```
Backend API runs at `http://127.0.0.1:5000` by default.

Environment variables (optional):

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy URL (e.g. `mysql+pymysql://...`) |
| `JWT_SECRET_KEY` | JWT signing secret |
| `SECRET_KEY` | Flask secret |
| `ADMIN_IMPORT_TOKEN` | If set, clients must send `X-Admin-Token` on master data import |

## 🐳 Docker Deployment
The system includes full Docker support for one-click deployment:

```bash
# Enter docker directory
cd sources/docker

# Copy environment template
cp .env.example .env

# Build and start (or run build.sh / build.bat)
docker-compose up -d --build
```
Access the system via the Nginx proxy address after deployment.

## 🖥️ Manual Startup Scripts
For Windows / Linux local environments, convenient batch scripts are provided:

- **Windows**: Run `start_manual.bat` (starts both) and `stop_manual.bat` in the root, or scripts in `sources/bin/Windows/`.
- **Linux**: Run `sources/bin/Linux/start.sh` and `stop.sh`.

## ⚙️ First-Time Setup & Config
- **Admin Account**: Default admin username is `admin`, password is `123456`.
- **Master Data Import**: After logging in, navigate to "Master Data" to upload organizational XLSX (Departments, Positions, Employees) or add members manually.
- **Space Management**: Admins/Managers can click the `+` button in the Library sidebar to quickly create and manage new knowledge spaces.

## 📡 Core API Overview
- `GET /api/documents?scope=all|mine|collab` — Query documents across various scopes.
- `GET /api/documents/tree` — Fetch hierarchical directory structure (Space and Department views).
- `PATCH /api/documents/:id` — Update metadata. Supports bulk space assignment via `space_ids` (List).
- `POST /api/documents/batch-move` — Bulk category management. Use `append: true` for incremental addition.
- `GET /api/documents/:id/diff` — Get diff data between document versions.
- `POST /api/spaces` — Endpoint for Admins/Managers to create new knowledge spaces.

## 📚 Documentation
For detailed architecture or user manuals, refer to the following documents:

- **User Guide**: [sources/docs/user-guide.zh-CN.md](sources/docs/user-guide.zh-CN.md)
- **Technical Documentation**: [sources/docs/technical-documentation/technical-documentation.zh-CN.md](sources/docs/technical-documentation/technical-documentation.zh-CN.md)
- **Deployment Guide**: [sources/docs/deployment-guide/deployment-guide.zh-CN.md](sources/docs/deployment-guide/deployment-guide.zh-CN.md)

## 📄 License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.