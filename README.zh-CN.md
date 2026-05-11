# EDMS — 电子文档管理系统

[English](./README.md) | [简体中文](./README.zh-CN.md) 

Vue 3 + Element Plus 前端，Flask 后端。支持主数据导入、多维文档分类、AI 识图建档、协作编辑、评论和审批工作流。

## 核心特性

- **多维分类系统**：文档支持关联多个“知识空间”（Many-to-Many），支持跨空间检索。
- **AI 智能增强**：内置智能助手，支持 AI 对话生成、AI 识图建档（OCR 识别 + 自动排版）。
- **灵活权限控制**：支持基于用户、部门和空间的多维度权限管理（查看、编辑、评论）。
- **审批工作流**：完整的文档生命周期管理，支持草稿、审批中、已批准、已驳回状态流转。
- **全栈国际化**：支持中英文无缝切换，包括系统生成的分类标签和部门名称。

## 前提条件

- Python 3.10+（推荐）
- Node.js 18+ 和 **cnpm**（或 npm）用于前端

### 前端包安装（中国/受限网络）

如果 `npm` 速度慢或不可用，请使用 **cnpm**（使用相同的 `package.json`）：

```bash
cd sources/frontend
cnpm install
cnpm run dev
```

## 后端

```bash
cd sources/backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
python wsgi.py
```

API 默认运行在 `http://127.0.0.1:5000`。

## 文档 API（精选）

- `GET /api/documents?scope=all|mine|collab` — 多维度文档列表查询。
- `GET /api/documents/tree` — 获取分层目录结构（支持空间与部门视图）。
- `PATCH /api/documents/:id` — 更新文档元数据。支持 `space_ids` (List) 批量分配分类。
- `POST /api/documents/batch-move` — 批量操作分类。参数 `append: true` 可实现增量添加分类。
- `POST /api/spaces` — 管理员/经理可在此接口创建新的知识空间分类。

## 首次设置（尚无用户）

如果登录时提示"无效的用户名"，说明数据库中没有员工数据。

1. 系统预留 `admin` 账号，密码为 `123456`。
2. 登录后可在 **主数据** 页面上传组织架构 XLSX，或手动添加成员。
3. **增加分类**：管理员可在文库左侧“知识库目录”点击 `+` 按钮直接新增分类种类。

## 手动部署（Windows）

项目根目录下提供了一键启动脚本：
- **`start_manual.bat`** - 同时启动前后端服务。
- **`stop_manual.bat`** - 停止所有 EDMS 相关服务。

## 文档

- [docs/architecture.md](docs/architecture.zh-CN.md) — 架构与数据流
- [docs/user-guide.md](docs/user-guide.zh-CN.md) — 用户操作指南

## 许可证

MIT (参阅 [LICENSE](LICENSE))
