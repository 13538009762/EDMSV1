# EDMS — Electronic Document Management System

[English](./README.md) | [简体中文](./README.zh-CN.md) 

Vue 3 + Element Plus frontend, Flask backend. Supports master data import, multi-space categorization, AI-powered document creation, collaborative editing, comments, and approval workflows.

## Core Features

- **Multi-Space Categorization**: Documents can be associated with multiple "Knowledge Spaces" (Many-to-Many), breaking the limits of traditional single-folder structures.
- **AI-Powered Intelligence**: Built-in AI assistant for conversation-based generation and AI Image-to-Doc (OCR + Auto-layout).
- **Flexible Access Control**: Multi-dimensional permission management based on Users, Departments, and Spaces (View, Edit, Comment).
- **Approval Workflows**: Complete document lifecycle management with Draft, In Approval, Approved, and Rejected states.
- **Full-Stack i18n**: Seamless switching between English and Chinese, including system-generated labels like space names and department titles.

## Prerequisites

- Python 3.10+ (Recommended)
- Node.js 18+

### Frontend Installation

```bash
cd sources/frontend
npm install
npm run dev
```

## Backend Setup

```bash
cd sources/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py
```

API defaults to `http://127.0.0.1:5000`.

## Document API (Highlights)

- `GET /api/documents?scope=all|mine|collab` — Query document list with various scopes.
- `GET /api/documents/tree` — Get hierarchical directory structure (Supports Space and Department views).
- `PATCH /api/documents/:id` — Update document metadata. Supports bulk category assignment via `space_ids` (List).
- `POST /api/documents/batch-move` — Batch manage categories. Use `append: true` for incremental assignment.
- `POST /api/spaces` — Endpoint for Admins/Managers to create new knowledge spaces.

## First-Time Setup

1. Default admin account is `admin` with password `123456`.
2. After login, navigate to **Master Data** to upload organizational XLSX or add members manually.
3. **Manage Categories**: Admins can click the `+` button in the Library sidebar to add new document categories directly.

## Manual Deployment (Windows)

One-click scripts are provided in the root directory:
- **`start_manual.bat`** - Start both frontend and backend services.
- **`stop_manual.bat`** - Stop all EDMS-related services.

## Documentation

- [docs/architecture.md](docs/architecture.md) — Architecture & Data Flow
- [docs/user-guide.md](docs/user-guide.md) — User Guide

## License

MIT (See [LICENSE](LICENSE))
 if shipped with the project).