# EDMS — 企业级电子文档管理系统 (Electronic Document Management System)

[English](./README.md) | [简体中文](./README.zh-CN.md) 

基于 Vue 3 + Element Plus 的前端与 Flask 后端构建的企业级文档管理系统。支持主数据（Master Data）导入、多空间分类、AI 智能辅助创作、实时协同编辑、文档差异对比、评论互动以及完整的审批工作流。

## ✨ 核心特性

- **多空间分类 (Multi-Space Categorization)**：打破传统单文件夹限制，文档可同时关联多个“知识空间”（多对多关系），实现灵活的多维度知识管理。
- **AI 智能辅助 (AI-Powered Intelligence)**：内置 AI 助手，支持对话式文档生成、知识问答以及“图生文”（OCR + 智能排版）等功能。
- **实时协同与版本控制 (Real-time Collab & Versioning)**：基于 WebSocket 支持多人实时协同编辑，内置文档历史版本管理与双向差异对比（Diff）视图。
- **审批工作流 (Approval Workflows)**：提供完整的文档生命周期管理，涵盖“草稿”、“审批中”、“已批准”与“已拒绝”等状态。
- **灵活的权限控制 (Flexible Access Control)**：基于用户、部门和空间（只读、编辑、评论）的多维度 RBAC 权限管理体系。
- **文档防篡改溯源 (Blockchain Traceability)**：底层集成 Mock 区块链服务，对核心文档进行哈希上链存证，确保企业数据资产的完整性与不可篡改性。
- **全栈国际化 (Full-Stack i18n)**：支持中英文无缝切换，包含系统生成的标签、空间名称及部门职级等数据的国际化处理。

## 🛠️ 环境准备

- Python 3.10+（推荐）
- Node.js 18+
- Docker & Docker Compose（如需容器化部署）

## 🚀 快速开始 (本地开发)

### 1. 前端启动

```bash
cd sources/frontend
npm install
npm run dev
```
前端默认运行在 `http://localhost:5173`

### 2. 后端启动

```bash
cd sources/backend
python -m venv .venv
# Windows 环境激活虚拟环境: .venv\Scripts\activate
# Linux/Mac 环境激活: source .venv/bin/activate

pip install -r requirements.txt
python wsgi.py
```
后端 API 默认运行在 `http://127.0.0.1:5000`

## 🐳 Docker 容器化部署
系统内置了完整的 Docker 支持，可一键部署：

```bash
# 进入 docker 目录
cd sources/docker

# 复制环境变量模板
cp .env.example .env

# 一键构建并启动 (或者运行 build.sh / build.bat)
docker-compose up -d --build
```
部署完成后，可通过 Nginx 代理的地址直接访问系统。

## 🖥️ 一键手动启停脚本
对于 Windows / Linux 本地环境，代码库提供了便捷的批处理脚本：

- **Windows**: 运行根目录下的 `start_manual.bat`（启动前后端）和 `stop_manual.bat`（停止服务）；或使用 `sources/bin/Windows/` 下的脚本。
- **Linux**: 运行 `sources/bin/Linux/start.sh` 和 `stop.sh`。

## ⚙️ 初次使用与配置
- **初始超管账号**：默认管理员账号为 `admin`，密码为 `123456`。
- **主数据导入**：首次登录后，请导航至 “主数据管理 (Master Data)”，上传组织架构表格（包含部门、岗位、员工信息的 XLSX 文件）或手动添加成员。
- **空间与分类管理**：管理员/经理可以直接在左侧边栏（Library）点击 `+` 按钮，快速创建和管理新的知识空间。

## 📡 核心 API 概览
- `GET /api/documents?scope=all|mine|collab` — 多维度查询文档列表（全部/我的/协作）。
- `GET /api/documents/tree` — 获取层级目录结构（支持空间视图和部门视图）。
- `PATCH /api/documents/:id` — 更新文档元数据。支持通过 `space_ids`（列表）进行批量空间关联。
- `POST /api/documents/batch-move` — 批量管理分类。使用 `append: true` 支持增量追加空间。
- `GET /api/documents/:id/diff` — 获取文档历史版本的差异对比数据。
- `POST /api/spaces` — 管理员/空间负责人创建新知识空间的端点。

## 📚 文档说明
如需深入了解系统架构或查阅用户手册，请参考以下文档（同时提供 Markdown 与 PDF 版本）：

- **用户指南**: [sources/docs/user-guide.zh-CN.md](sources/docs/user-guide.zh-CN.md)
- **技术文档**: [sources/docs/technical-documentation/technical-documentation.zh-CN.md](sources/docs/technical-documentation/technical-documentation.zh-CN.md)
- **部署指南**: [sources/docs/deployment-guide/deployment-guide.zh-CN.md](sources/docs/deployment-guide/deployment-guide.zh-CN.md)

## 📄 许可证
本项目采用 MIT 许可证。详情请参阅项目中的 [LICENSE](LICENSE) 文件。
