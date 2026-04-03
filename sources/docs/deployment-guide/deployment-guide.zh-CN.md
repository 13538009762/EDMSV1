# EDMS 系统部署手册

本手册供系统管理员进行 EDMS（电子文档管理系统）的安装部署操作。

## 目录

1. [系统要求](#系统要求)
2. [部署步骤](#部署步骤)
3. [配置指南](#配置指南)
4. [部署后验证](#部署后验证)
5. [故障排查](#故障排查)
6. [维护操作](#维护操作)

---

## 系统要求

### 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|----------|----------|
| CPU | 2 核 | 4 核 |
| 内存 | 2 GB | 4 GB |
| 磁盘空间 | 5 GB | 20 GB |
| 网络 | 100 Mbps | 1 Gbps |

### 软件要求

- Docker 20.10+
- Docker Compose 2.0+

### 支持的操作系统

- 支持主流 Windows、Linux 及所有可以正常安装 Docker 的 X86 架构系统

---

## 部署步骤

### 步骤 1：解压部署包

1. **下载部署包** (`edms-deployment.zip`)
2. **解压到合适目录**：
   - Windows：右键选择"全部提取"
   - Linux/macOS：使用 `unzip edms-deployment.zip` 命令

### 步骤 2：安装 Docker

- **Windows**：从官方网站安装 Docker Desktop
- **Linux**：按照官方 Docker 安装指南操作
- **验证安装**：
  ```bash
  docker --version
  docker-compose --version
  ```

### 步骤 3：启动服务

#### Windows

1. **以管理员身份打开命令提示符**
2. **导航到 bin 目录**：
   ```cmd
   cd path\to\edms-deployment\bin\Windows
   ```
3. **启动服务**：
   ```cmd
   start.bat
   ```

#### Linux/macOS

1. **打开终端**
2. **导航到 bin 目录**：
   ```bash
   cd path/to/edms-deployment/bin/Linux
   ```
3. **添加执行权限**：
   ```bash
   chmod +x *.sh
   ```
4. **启动服务**：
   ```bash
   ./start.sh
   ```

### 步骤 4：停止服务

#### Windows

```cmd
stop.bat
```

#### Linux/macOS

```bash
./stop.sh
```

---

## 配置指南

### 环境变量

您可以通过编辑 `bin/.env` 文件来自定义部署：

| 变量名 | 说明 | 默认值 | 是否必填 |
|--------|------|--------|----------|
| `WEB_PORT` | Web 服务端口 | 80 | 是 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 自动生成 | 是 |
| `CORS_ORIGINS` | 允许的 CORS 来源 | http://localhost | 否 |
| `DATABASE_URL` | 数据库连接字符串 | sqlite:///app/data/edms.db | 否 |

**配置示例**：
```env
# 自定义 web 端口
WEB_PORT=8080

# 自定义 JWT 密钥（生产环境推荐）
JWT_SECRET_KEY=your-secure-secret-key-here

# 允许多个来源
CORS_ORIGINS=http://localhost,http://your-domain.com
```

### 数据持久化

所有持久化数据存储在 `bin/data/` 目录：
- `bin/data/backend/` - 应用数据和 SQLite 数据库

**重要**：定期备份此目录以防止数据丢失。

---

## 部署后验证

1. **服务状态检查**
   ```bash
   docker ps
   ```

2. **日志验证**
   ```bash
   # Windows
   docker-compose -f bin\docker-compose.yml logs -f
   
   # Linux/macOS
   docker compose -f bin/docker-compose.yml logs -f
   ```

3. **前端访问测试**
   - 打开浏览器访问 http://localhost
   - 验证登录页面是否正常加载

---

## 故障排查

### 端口已被占用

**错误**：`Port 80 is already in use`

**解决方案**：
1. 编辑 `bin/.env` 文件
2. 将 `WEB_PORT` 改为可用端口（如 8080）
3. 重启服务

### 容器启动失败

**查看日志**：
```bash
docker logs edms-backend
docker logs edms-frontend
```

**常见原因**：
- 磁盘空间不足
- 内存限制
- 端口冲突

### 数据库连接问题

**解决方案**：
1. 验证数据目录权限
2. 检查数据库文件完整性
3. 查看后端日志获取具体错误

---

## 维护操作

### 查看日志

```bash
# Windows
docker-compose -f bin\docker-compose.yml logs -f

# Linux/macOS
docker compose -f bin/docker-compose.yml logs -f
```

### 重启服务

```bash
# Windows
docker-compose -f bin\docker-compose.yml restart

# Linux/macOS
docker compose -f bin/docker-compose.yml restart
```

### 备份数据

```bash
# 先停止服务
./Linux/stop.sh  # 或 Windows\stop.bat

# 备份数据目录
tar -czvf edms-backup-$(date +%Y%m%d).tar.gz bin/data/

# 重启服务
./Linux/start.sh  # 或 Windows\start.bat
```

### 更新部署

1. **备份现有数据**
2. **停止服务**
3. **解压新版本覆盖现有文件**
4. **启动服务**

---

## 支持与反馈

如需技术支持，请联系系统管理员或开发团队。
