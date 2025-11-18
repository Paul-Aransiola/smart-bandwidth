# Deployment Guide

This guide covers deploying the Smart Bandwidth Monitor in production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Manual Deployment](#manual-deployment)
- [Database Setup](#database-setup)
- [Security Hardening](#security-hardening)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Memory**: Minimum 2GB RAM (4GB+ recommended)
- **Storage**: 10GB+ available disk space
- **Network**: Access to network interface for monitoring

### Required Software

- Docker 20.10+ and Docker Compose 2.0+ (for containerized deployment)
- Python 3.11+ (for manual deployment)
- Redis 7.0+ (for caching and rate limiting)
- PostgreSQL 14+ or MySQL 8+ (recommended for production)

### Network Permissions

The application requires elevated network permissions to monitor traffic and control bandwidth:
- `NET_ADMIN` capability for iptables rules
- `NET_RAW` capability for packet capture
- Access to network interfaces

## Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Generate Secret Key

```bash
# Generate a secure 64-character secret key
openssl rand -hex 32
```

### 3. Essential Configuration

Edit `.env` with your settings:

```bash
# Environment
ENV=production

# Security (CRITICAL!)
SECRET_KEY=<your-generated-secret-key>

# Database (PostgreSQL recommended)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bandwidth_monitor
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis Configuration
REDIS_ENABLED=true
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<optional-redis-password>

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# CORS (specify your frontend domain)
CORS_ORIGINS=["https://yourdomain.com"]

# Logging
LOG_LEVEL=WARNING
```

### 4. Notification Configuration (Optional)

```bash
# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_ADDRESS=your-email@gmail.com
SMTP_USE_TLS=true

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL
```

## Docker Deployment

### Production Deployment with Docker Compose

#### 1. Set SECRET_KEY Environment Variable

```bash
export SECRET_KEY=$(openssl rand -hex 32)
```

#### 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Check service health
docker-compose ps
```

#### 3. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Expected response:
# {"status":"healthy","version":"0.2.0","timestamp":"..."}
```

#### 4. Create Admin User

```bash
# Access API container
docker exec -it bandwidth-monitor-api bash

# Create admin user (if needed)
python -c "from src.core.security import get_password_hash; print(get_password_hash('your-password'))"
```

### Docker Compose Services

The stack includes:

- **redis**: Caching and rate limiting backend
  - Port: 6379
  - Data persisted in named volume
  
- **api**: Main application server
  - Port: 8000
  - Runs database migrations on startup
  - Requires NET_ADMIN and NET_RAW capabilities
  
- **dashboard**: Web interface (Nginx)
  - Port: 3000

### Service Dependencies

```
dashboard → api → redis
```

All services have health checks and will restart automatically on failure.

## Manual Deployment

### 1. Install System Dependencies

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    libpcap-dev \
    iptables \
    iproute2 \
    redis-server

# CentOS/RHEL
sudo yum install -y \
    python311 \
    python311-devel \
    libpcap-devel \
    iptables \
    iproute \
    redis
```

### 2. Install Python Dependencies

```bash
# Install uv package manager
pip install uv

# Install project dependencies
uv pip install -e .
```

### 3. Start Redis

```bash
sudo systemctl start redis
sudo systemctl enable redis
```

### 4. Run Database Migrations

```bash
alembic upgrade head
```

### 5. Start Application

```bash
# Development mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode with Gunicorn
gunicorn src.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log \
    --log-level warning
```

## Database Setup

### PostgreSQL (Recommended)

#### 1. Install PostgreSQL

```bash
sudo apt-get install postgresql-14
```

#### 2. Create Database

```bash
sudo -u postgres psql

CREATE DATABASE bandwidth_monitor;
CREATE USER bandwidthuser WITH PASSWORD 'secure-password';
GRANT ALL PRIVILEGES ON DATABASE bandwidth_monitor TO bandwidthuser;
\q
```

#### 3. Configure Connection

```bash
# In .env
DATABASE_URL=postgresql+asyncpg://bandwidthuser:secure-password@localhost:5432/bandwidth_monitor
```

#### 4. Run Migrations

```bash
alembic upgrade head
```

### MySQL/MariaDB Alternative

```sql
CREATE DATABASE bandwidth_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bandwidthuser'@'localhost' IDENTIFIED BY 'secure-password';
GRANT ALL PRIVILEGES ON bandwidth_monitor.* TO 'bandwidthuser'@'localhost';
FLUSH PRIVILEGES;
```

```bash
# In .env
DATABASE_URL=mysql+aiomysql://bandwidthuser:secure-password@localhost:3306/bandwidth_monitor
```

## Security Hardening

### 1. SECRET_KEY Management

```bash
# Generate unique key per environment
openssl rand -hex 32

# Store securely (never commit to git)
echo "SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

### 2. Firewall Configuration

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API
sudo ufw allow 3000/tcp  # Dashboard
sudo ufw enable
```

### 3. Redis Security

```bash
# Set Redis password
redis-cli CONFIG SET requirepass "your-redis-password"

# Update .env
REDIS_PASSWORD=your-redis-password
```

### 4. SSL/TLS Configuration

For production, use a reverse proxy (Nginx/Caddy) with SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 5. Rate Limiting

Already configured with slowapi and Redis. Adjust in `.env`:

```bash
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## Monitoring & Maintenance

### Application Logs

```bash
# Docker logs
docker-compose logs -f api

# Manual deployment
tail -f logs/app.log
tail -f logs/access.log
tail -f logs/error.log
```

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Redis health
redis-cli ping

# Database connection
psql -U bandwidthuser -d bandwidth_monitor -c "SELECT 1;"
```

### Backup Strategy

#### Database Backups

```bash
# PostgreSQL
pg_dump -U bandwidthuser bandwidth_monitor > backup_$(date +%Y%m%d).sql

# Restore
psql -U bandwidthuser bandwidth_monitor < backup_20240101.sql
```

#### Configuration Backups

```bash
# Backup environment configuration
cp .env .env.backup_$(date +%Y%m%d)

# Backup Docker volumes
docker run --rm -v redis-data:/data -v $(pwd):/backup \
    alpine tar czf /backup/redis_backup_$(date +%Y%m%d).tar.gz /data
```

### Log Rotation

Configure logrotate for application logs:

```bash
# /etc/logrotate.d/bandwidth-monitor
/app/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 appuser appuser
    sharedscripts
}
```

### Performance Tuning

#### Redis Optimization

```bash
# Increase max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### Database Optimization

```sql
-- Add indexes (if not exists)
CREATE INDEX idx_devices_ip ON devices(ip_address);
CREATE INDEX idx_devices_mac ON devices(mac_address);
CREATE INDEX idx_bandwidth_device_time ON bandwidth_usage(device_id, timestamp);
CREATE INDEX idx_alerts_device_time ON alerts(device_id, triggered_at);
```

## Troubleshooting

### Issue: "SECRET_KEY must be changed in production"

**Solution**: Generate and set a unique SECRET_KEY:
```bash
export SECRET_KEY=$(openssl rand -hex 32)
# Or add to .env file
```

### Issue: Cannot connect to Redis

**Solution**: Check Redis status and connection:
```bash
docker-compose ps redis
redis-cli ping
# Update REDIS_HOST in .env if needed
```

### Issue: Permission denied for network monitoring

**Solution**: Ensure proper capabilities:
```bash
# Docker: Already configured in docker-compose.yml
# Manual: Run with sudo or set capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

### Issue: Database connection failed

**Solution**: Verify database credentials and connectivity:
```bash
# Test PostgreSQL connection
psql -U bandwidthuser -h localhost -d bandwidth_monitor

# Check DATABASE_URL in .env
# Ensure database exists and user has permissions
```

### Issue: Rate limiting not working

**Solution**: Verify Redis is enabled and running:
```bash
# Check .env
REDIS_ENABLED=true

# Test Redis connection
redis-cli -h localhost -p 6379 ping
```

## Production Checklist

Before going live, verify:

- [ ] SECRET_KEY is unique and secure (not default value)
- [ ] ENV is set to `production`
- [ ] Database is PostgreSQL or MySQL (not SQLite)
- [ ] Redis is enabled and running
- [ ] CORS origins are properly configured
- [ ] SSL/TLS is configured (reverse proxy)
- [ ] Firewall rules are configured
- [ ] Backup strategy is in place
- [ ] Log rotation is configured
- [ ] Health checks are passing
- [ ] Monitoring is set up
- [ ] Notification channels are tested
- [ ] Database indexes are created
- [ ] Application logs are accessible

## Support & Resources

- **Documentation**: See `README.md` and `FEATURES_5_6_7_SUMMARY.md`
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health

## License

See LICENSE file for details.
