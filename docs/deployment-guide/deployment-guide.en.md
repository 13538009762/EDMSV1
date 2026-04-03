# EDMS System Deployment Manual

This manual is intended for system administrators to install and deploy the EDMS (Electronic Document Management System).

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Deployment Steps](#deployment-steps)
3. [Configuration Guide](#configuration-guide)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Operations](#maintenance-operations)

---

## System Requirements

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| Memory | 2 GB | 4 GB |
| Disk Space | 5 GB | 20 GB |
| Network | 100 Mbps | 1 Gbps |

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+

### Supported Operating Systems

- Mainstream Windows and Linux systems
- All X86 architecture systems that can properly install Docker

---

## Deployment Steps

### Step 1: Extract Deployment Package

1. **Download the deployment package** (`edms-deployment.zip`)
2. **Extract the package** to a suitable directory:
   - Windows: Right-click and select "Extract All"
   - Linux/macOS: Use `unzip edms-deployment.zip`

### Step 2: Install Docker

- **Windows**: Install Docker Desktop from the official website
- **Linux**: Follow the official Docker installation guide for your distribution
- **Verify installation**:
  ```bash
  docker --version
  docker-compose --version
  ```

### Step 3: Start Services

#### Windows

1. **Open Command Prompt** as administrator
2. **Navigate to the bin directory**:
   ```cmd
   cd path\to\edms-deployment\bin\Windows
   ```
3. **Start the services**:
   ```cmd
   start.bat
   ```

#### Linux/macOS

1. **Open Terminal**
2. **Navigate to the bin directory**:
   ```bash
   cd path/to/edms-deployment/bin/Linux
   ```
3. **Add execute permissions**:
   ```bash
   chmod +x Linux/*.sh
   ```
4. **Start the services**:
   ```bash
   ./start.sh
   ```

### Step 4: Stop Services

#### Windows

```cmd
stop.bat
```

#### Linux/macOS

```bash
./stop.sh
```

---

## Configuration Guide

### Environment Variables

You can customize the deployment by editing the `bin/.env` file:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `WEB_PORT` | Web service port | 80 | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Auto-generated | Yes |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost | No |
| `DATABASE_URL` | Database connection string | sqlite:///app/data/edms.db | No |

**Example configuration**:
```env
# Custom web port
WEB_PORT=8080

# Custom JWT secret key (recommended for production)
JWT_SECRET_KEY=your-secure-secret-key-here

# Allow multiple origins
CORS_ORIGINS=http://localhost,http://your-domain.com
```

### Data Persistence

All persistent data is stored in the `bin/data/` directory:
- `bin/data/backend/` - Application data and SQLite database

**Important**: Back up this directory regularly to prevent data loss.

---

## Post-Deployment Verification

1. **Service Status Check**
   ```bash
   docker ps
   ```

2. **Log Verification**
   ```bash
   # Windows
   docker-compose -f bin\docker-compose.yml logs -f
   
   # Linux/macOS
   docker compose -f bin/docker-compose.yml logs -f
   ```

3. **Frontend Access Test**
   - Open browser and navigate to http://localhost
   - Verify login page loads correctly

---

## Troubleshooting

### Port Already in Use

**Error**: `Port 80 is already in use`

**Solution**:
1. Edit `bin/.env` file
2. Change `WEB_PORT` to an available port (e.g., 8080)
3. Restart services

### Container Fails to Start

**Check Logs**:
```bash
docker logs edms-backend
docker logs edms-frontend
```

**Common Causes**:
- Insufficient disk space
- Memory limits
- Port conflicts

### Database Connection Issues

**Solution**:
1. Verify data directory permissions
2. Check database file integrity
3. Review backend logs for specific errors

---

## Maintenance Operations

### View Logs

```bash
# Windows
docker-compose -f bin\docker-compose.yml logs -f

# Linux/macOS
docker compose -f bin/docker-compose.yml logs -f
```

### Restart Services

```bash
# Windows
docker-compose -f bin\docker-compose.yml restart

# Linux/macOS
docker compose -f bin/docker-compose.yml restart
```

### Backup Data

```bash
# Stop services first
./Linux/stop.sh  # or Windows\stop.bat

# Backup data directory
tar -czvf edms-backup-$(date +%Y%m%d).tar.gz bin/data/

# Restart services
./Linux/start.sh  # or Windows\start.bat
```

### Update Deployment

1. **Backup existing data**
2. **Stop services**
3. **Extract new version over existing files**
4. **Start services**

---

## Support and Feedback

For technical support, please contact the system administrator or development team.
