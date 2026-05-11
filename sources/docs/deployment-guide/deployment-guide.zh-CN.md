# EDMS 系统部署手册

本手册供系统管理员进行 EDMS（电子文档管理系统）的安装部署操作。当前架构基于 **MySQL 8.0+** 并集成了 AI 与 WebSocket 服务。

---

## 1. 系统要求

### 1.1 硬件要求
| 组件 | 最低配置 | 推荐配置 |
| :--- | :--- | :--- |
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 磁盘空间 | 20 GB | 50 GB+ |

### 1.2 软件要求
- **容器引擎**：Docker 20.10+ 及 Docker Compose 2.0+ (容器化部署必备)。
- **数据库**：**MySQL 8.0+** (必须支持 `utf8mb4` 字符集)。
- **操作系统**：Windows、Linux (Ubuntu/CentOS) 或 macOS。

---

## 2. 部署步骤

### 步骤 1：准备环境
1. **解压部署包**。
2. **编辑配置**：在 `sources/docker/.env` 或启动目录创建 `.env` 文件。

### 步骤 2：启动服务

#### 【选项 A：Docker 一键部署（推荐）】
1. **进入目录**：`cd sources/docker`。
2. **启动**：
   - Windows: 运行 `build.bat`。
   - Linux: 运行 `./build.sh`。
   - 或者手动执行：`docker-compose up -d --build`。

#### 【选项 B：手动本地部署】
1. **MySQL 初始化**：
   ```sql
   CREATE DATABASE edms_db CHARSET utf8mb4;
   ```
2. **后端启动**：
   ```bash
   cd sources/backend
   pip install -r requirements.txt
   pip install pymysql
   python wsgi.py
   ```
3. **前端启动**：
   ```bash
   cd sources/frontend
   npm install
   npm run dev
   ```

---

## 3. 配置指南 (.env 环境变量)

您必须正确配置 `.env` 文件，特别是数据库连接串：

| 变量名 | 说明 | 示例值 |
| :--- | :--- | :--- |
| WEB_PORT | 系统访问端口 | 80 |
| DATABASE_URL | MySQL 连接串 | mysql+pymysql://root:123456@db:3306/edms_db?charset=utf8mb4 |
| JWT_SECRET_KEY | 令牌签名密钥 | production-secure-key |
| AI_API_KEY | 大模型 API Key | sk-xxxxxx |

*注意：`DATABASE_URL` 必须包含 `charset=utf8mb4` 以支持复杂富文本。*

---

## 4. 故障排查

### 4.1 数据库连接失败
- **检查驱动**：确保 URL 以 `mysql+pymysql://` 开头。
- **权限问题**：确保 MySQL 允许远程连接且账号密码正确。
- **编码报错**：确保数据库默认字符集为 `utf8mb4`。

### 4.2 实时协同断连 (WebSocket)
- 如果前端通过 Nginx 转发，请确保配置了以下 Header：
  ```nginx
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "Upgrade";
  ```

---

## 5. 维护与备份

### 5.1 数据库备份
定期使用 `mysqldump` 备份数据：
```bash
docker exec edms-mysql mysqldump -u root -p'password' edms_db > backup.sql
```

### 5.2 文件资产备份
请同步备份存放上传附件及区块链账本的持久化存储目录（通常为 `data/` 目录）。
