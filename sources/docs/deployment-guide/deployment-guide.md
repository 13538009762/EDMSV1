# EDMS Deployment Guide

This manual is for system administrators to perform the installation and deployment of the EDMS (Electronic Document Management System). The current architecture is based on **MySQL 8.0+** and integrates AI and WebSocket services.

---

## 1. System Requirements

### 1.1 Hardware
| Component | Minimum | Recommended |
| :--- | :--- | :--- |
| CPU | 2 Cores | 4 Cores+ |
| RAM | 4 GB | 8 GB+ |
| Disk | 20 GB | 50 GB+ |

### 1.2 Software
- **Container Engine**: Docker 20.10+ and Docker Compose 2.0+.
- **Database**: **MySQL 8.0+** (must support `utf8mb4` charset).
- **OS**: Windows, Linux (Ubuntu/CentOS), or macOS.

---

## 2. Deployment Steps

### Step 1: Prepare Environment
1. **Unzip the deployment package**.
2. **Edit Configuration**: Create a `.env` file in `sources/docker/` or the startup directory.

### Step 2: Start Services

#### 【Option A: One-click Docker Deployment (Recommended)】
1. **Enter Directory**: `cd sources/docker`.
2. **Start**:
   - Windows: Run `build.bat`.
   - Linux: Run `./build.sh`.
   - Or manually: `docker-compose up -d --build`.

#### 【Option B: Manual Local Deployment】
1. **MySQL Initialization**:
   ```sql
   CREATE DATABASE edms_db CHARSET utf8mb4;
   ```
2. **Backend Startup**:
   ```bash
   cd sources/backend
   pip install -r requirements.txt
   pip install pymysql
   python wsgi.py
   ```
3. **Frontend Startup**:
   ```bash
   cd sources/frontend
   npm install
   npm run dev
   ```

---

## 3. Configuration Guide (.env Variables)

You must correctly configure the `.env` file, especially the database connection string:

| Variable | Description | Example |
| :--- | :--- | :--- |
| WEB_PORT | Access port | 80 |
| DATABASE_URL | MySQL Connection String | mysql+pymysql://root:123456@db:3306/edms_db?charset=utf8mb4 |
| JWT_SECRET_KEY | Token signing secret | production-secure-key |
| AI_API_KEY | AI Engine API Key | sk-xxxxxx |

*Note: `DATABASE_URL` must include `charset=utf8mb4` to support rich text and special characters.*

---

## 4. Troubleshooting

### 4.1 Database Connection Failure
- **Check Driver**: Ensure the URL starts with `mysql+pymysql://`.
- **Permissions**: Ensure MySQL allows remote connections and the credentials are correct.
- **Encoding Errors**: Ensure the default database charset is `utf8mb4`.

### 4.2 WebSocket Disconnections
- If forwarding via Nginx, ensure the following headers are configured:
  ```nginx
  proxy_set_header Upgrade $http_upgrade;
  proxy_set_header Connection "Upgrade";
  ```

---

## 5. Maintenance & Backup

### 5.1 Database Backup
Regularly backup data using `mysqldump`:
```bash
docker exec edms-mysql mysqldump -u root -p'password' edms_db > backup.sql
```

### 5.2 Asset Backup
Synchronously backup the persistent storage directory (usually the `data/` folder) containing attachments and blockchain ledgers.
