# Quick Start - Production Deployment

## 🚀 Deploy in 3 Steps

### 1. Generate Secret Key
```bash
./scripts/generate-secret.sh
```
Copy the generated key for the next step.

### 2. Configure Environment
```bash
# Copy production template
cp .env.production .env

# Edit with your values
nano .env  # or vim .env

# Required settings:
# - SECRET_KEY (from step 1)
# - DATABASE_URL (PostgreSQL connection string)
# - REDIS_PASSWORD (optional but recommended)
# - CORS_ORIGINS (your domain)
```

### 3. Deploy
```bash
# One-command deployment
./scripts/deploy.sh

# Or manual Docker
docker-compose -f docker-compose.prod.yml up -d
```

## 📋 Minimal .env Configuration

```bash
# Environment
ENV=production

# Security (REQUIRED - generate with ./scripts/generate-secret.sh)
SECRET_KEY=your-64-character-secret-key-here

# Database (REQUIRED for production)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/bandwidth_monitor

# Redis (recommended)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_ENABLED=true

# CORS (update with your domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Network Interface (update for your system)
NETWORK_INTERFACE=eth0
```

## ✅ Verify Deployment

```bash
# Check services
docker-compose -f docker-compose.prod.yml ps

# Test API health
curl http://localhost:8000/api/v1/health

# Run health check
./scripts/health-check.sh

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔧 Common Commands

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart a service
docker-compose -f docker-compose.prod.yml restart api

# View logs
docker-compose -f docker-compose.prod.yml logs -f api

# Run health check
./scripts/health-check.sh

# Create backup
./scripts/backup.sh

# Update application
git pull && ./scripts/deploy.sh
```

## 📚 Documentation

- **Full Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Deployment Checklist**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
- **Complete Summary**: [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

## 🆘 Troubleshooting

### SECRET_KEY Error
```bash
./scripts/generate-secret.sh
# Copy the key to .env
```

### Database Connection Failed
```bash
# Check PostgreSQL is running
docker-compose -f docker-compose.prod.yml ps postgres

# View logs
docker-compose -f docker-compose.prod.yml logs postgres
```

### Redis Connection Failed
```bash
# Check Redis is running
docker-compose -f docker-compose.prod.yml ps redis

# Test connection
docker exec -it bandwidth-redis redis-cli ping
```

### Permission Denied
```bash
# Ensure scripts are executable
chmod +x scripts/*.sh

# For Docker, ensure NET_ADMIN capability is set (already in docker-compose.prod.yml)
```

## 📦 What You Get

✅ **Production Database** - PostgreSQL with migrations  
✅ **Redis Caching** - Fast response times  
✅ **Health Monitoring** - Automated health checks  
✅ **Automated Backups** - 7-day retention  
✅ **Security** - SECRET_KEY validation, SSL ready  
✅ **Auto-restart** - Services restart on failure  
✅ **Resource Limits** - Prevents resource exhaustion  
✅ **Logging** - Structured logs with rotation  

## 🎯 Next Steps

1. Configure SSL/TLS with Let's Encrypt
2. Schedule automated backups (crontab)
3. Set up monitoring alerts
4. Configure GitHub Actions CI/CD
5. Review DEPLOYMENT_CHECKLIST.md

---

**Need Help?** See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed documentation.
