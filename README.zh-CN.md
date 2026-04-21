# EDMS — 电子文档管理系统

[English](./README.md) | [简体中文](./README.zh-CN.md) 

Vue 3 + Element Plus 前端，Flask 后端。支持主数据导入、文档编辑、协作、评论和审批工作流。

## 前提条件

- Python 3.10+（推荐）
- Node.js 18+ 和 **cnpm**（或 npm）用于前端

### 前端包安装（中国/受限网络）

如果 `npm` 速度慢或不可用，请使用 **cnpm**（使用相同的 `package.json`）：

```bash
cd frontend
cnpm install
cnpm run dev
```

生产构建：

```bash
cnpm run build
```

静态文件输出到 `frontend/dist/`。可以通过任何静态主机提供服务，并将 `/api` 和 `/socket.io` 代理到 Flask 服务器。

## 后端

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py
```

API 默认运行在 `http://127.0.0.1:5000`。

环境变量（可选）：

| 变量 | 说明 |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy URL（默认 `sqlite:///edms.db`） |
| `JWT_SECRET_KEY` | JWT 签名密钥 |
| `SECRET_KEY` | Flask 密钥 |
| `ADMIN_IMPORT_TOKEN` | 如果设置，客户端在主数据导入时必须发送 `X-Admin-Token` |

## 前端开发代理

`vite.config.ts` 将 `/api` 和 `/socket.io` 代理到 `http://127.0.0.1:5000`。如需要，可以使用 `VITE_API_BASE` 和 `VITE_SOCKET_URL` 覆盖 API 基础地址。

## 文档 API（文库）

- `GET /api/documents?scope=mine|approved` — 个人文库（拥有的、共享的、审批的，以及所有已批准的）与仅已批准的目录。
- `GET /api/documents?...&status=draft|in_approval|approved|rejected` — 可选的状态筛选。
- `PATCH /api/documents/:id` — 标题/页面设置 **仅当** 用户可以编辑元数据（草稿 + 所有者或 `edit` 协作者）。
- `POST/GET /api/documents/:id/permissions` — 仅所有者，**草稿** 仅用于更改；角色 `view` | `edit` | `comment`。
- `DELETE /api/documents/:id/permissions/:user_id` — 移除一个授权（所有者，草稿）。

## 首次设置（尚无用户）

如果登录时提示"无效的用户名"，说明数据库中没有员工数据。

1. 系统预留admin账号和密码123456 
2. 登录后可在主数据上传所有人的信息、也可管理员手动添加
3. 成功导入可登录

如果服务器上设置了 `ADMIN_IMPORT_TOKEN`，请在管理页面输入它（或发送 `X-Admin-Token`）。

一旦用户存在且 **未设置** `ADMIN_IMPORT_TOKEN`，再次导入时需要你 **先登录**（破坏性操作保护）。

## 国际化 (i18n)

- 默认 UI 语言为 **英文**（`en`）。
- 用户可以通过顶栏的 **Language**（或在登录页面）切换到 **中文**（`zh-CN`）。
- 选择存储在 `localStorage` 的 `edms_locale` 中。
- Element Plus 组件语言跟随相同设置。

## Docker 部署（推荐）

生产环境部署，使用 Docker 是最简单的方式：

```bash
# Windows
docker\build.bat
bin\start.bat

# Linux/macOS
./docker/build.sh
./bin/start.sh
```

详细说明请参阅 [docker/README.md](docker/README.zh-CN.md)。

## 文档

- [docs/architecture.md](docs/architecture.zh-CN.md) — 模块和数据流（如果存在）
- [docs/deployment.md](docs/deployment.zh-CN.md) — 部署说明
- [docs/user-guide.md](docs/user-guide.zh-CN.md) — 用户指南

## 许可证

MIT（请参阅项目中的 [LICENSE](LICENSE)）。
