# Smart Bandwidth Monitor - Deployment Checklist

## Pre-Deployment

### Security

- [ ] Generate unique SECRET_KEY: `openssl rand -hex 32`
- [ ] Update SECRET_KEY in .env file
- [ ] Change default admin passwords
- [ ] Configure CORS origins for your domain
- [ ] Review and enable security headers
- [ ] Set ENV=production in .env

### Database

- [ ] Set up PostgreSQL or MySQL database
- [ ] Create database and user with proper permissions
- [ ] Update DATABASE_URL in .env
- [ ] Configure connection pool settings (DB_POOL_SIZE, DB_MAX_OVERFLOW)
- [ ] Run migrations: `alembic upgrade head`
- [ ] Set up database backups

### Redis

- [ ] Install and configure Redis server
- [ ] Set Redis password (if applicable)
- [ ] Update Redis connection settings in .env
- [ ] Enable Redis: REDIS_ENABLED=true
- [ ] Test Redis connection: `redis-cli ping`

### Network Configuration

- [ ] Identify network interface to monitor (eth0, ens0, etc.)
- [ ] Update NETWORK_INTERFACE in .env
- [ ] Verify iptables and tc (traffic control) are available
- [ ] Test network monitoring permissions
- [ ] Configure capture filters if needed

### Application Settings

- [ ] Set appropriate LOG_LEVEL (WARNING or ERROR for production)
- [ ] Configure monitoring intervals
- [ ] Set bandwidth limits (MAX_BANDWIDTH_MBPS)
- [ ] Enable/disable features (ENABLE_BLOCKING, ENABLE_THROTTLING)
- [ ] Configure rate limiting

### Notifications (Optional)

- [ ] Configure SMTP settings for email notifications
- [ ] Test email delivery
- [ ] Set up Slack webhook (if using)
- [ ] Set up Discord webhook (if using)
- [ ] Configure notification preferences

## Deployment

### Docker Deployment

- [ ] Install Docker and Docker Compose
- [ ] Copy .env.production to .env and configure
- [ ] Build images: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Check service health: `docker-compose ps`
- [ ] View logs: `docker-compose logs -f`

### Manual Deployment

- [ ] Install Python 3.11+
- [ ] Install system dependencies (libpcap, iptables, iproute2)
- [ ] Create virtual environment
- [ ] Install Python dependencies: `uv pip install -e .`
- [ ] Run database migrations
- [ ] Set up systemd service (see systemd.service.example)
- [ ] Enable and start service: `systemctl enable --now bandwidth-monitor`

### Reverse Proxy (Recommended)

- [ ] Install Nginx or Caddy
- [ ] Configure SSL/TLS certificates (Let's Encrypt recommended)
- [ ] Set up reverse proxy (see nginx.conf.example)
- [ ] Configure WebSocket support
- [ ] Test SSL configuration
- [ ] Enable HTTP/2

## Post-Deployment

### Verification

- [ ] Access API health check: `curl https://yourdomain.com/api/v1/health`
- [ ] Check API documentation: <https://yourdomain.com/docs>
- [ ] Test WebSocket connection
- [ ] Verify database connectivity
- [ ] Confirm Redis caching is working
- [ ] Test bandwidth monitoring
- [ ] Verify device blocking/throttling

### Monitoring

- [ ] Set up log rotation
- [ ] Configure monitoring alerts
- [ ] Set up health check automation: `scripts/health-check.sh`
- [ ] Monitor resource usage (CPU, memory, disk)
- [ ] Track API response times
- [ ] Monitor database performance

### Backups

- [ ] Configure automated database backups
- [ ] Set up configuration backups: `scripts/backup.sh`
- [ ] Test backup restoration process
- [ ] Document backup locations
- [ ] Set up off-site backup storage

### Security Hardening

- [ ] Configure firewall rules (ufw/iptables)
- [ ] Disable unnecessary services
- [ ] Set up fail2ban (if applicable)
- [ ] Enable automatic security updates
- [ ] Review and restrict file permissions
- [ ] Implement network segmentation
- [ ] Set up intrusion detection (optional)

### Documentation

- [ ] Document deployment architecture
- [ ] Create runbook for common operations
- [ ] Document troubleshooting procedures
- [ ] Record credentials securely (password manager)
- [ ] Document backup/restore procedures
- [ ] Create disaster recovery plan

## Maintenance

### Daily

- [ ] Check service health: `scripts/health-check.sh`
- [ ] Review error logs
- [ ] Monitor disk space
- [ ] Check Redis memory usage

### Weekly

- [ ] Review application metrics
- [ ] Check bandwidth usage trends
- [ ] Verify backups are running
- [ ] Review security alerts

### Monthly

- [ ] Test backup restoration
- [ ] Review and rotate logs
- [ ] Update dependencies (security patches)
- [ ] Audit user access
- [ ] Review system resource usage
- [ ] Check for application updates

### Quarterly

- [ ] Review and update documentation
- [ ] Disaster recovery drill
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Capacity planning

## Useful Commands

### Docker

```bash
# View logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Update and restart
docker-compose pull && docker-compose up -d

# Stop all services
docker-compose down

# Clean up
docker-compose down -v  # Warning: removes volumes
```

### Service Management (systemd)

```bash
# Check status
systemctl status bandwidth-monitor

# View logs
journalctl -u bandwidth-monitor -f

# Restart
systemctl restart bandwidth-monitor

# Stop
systemctl stop bandwidth-monitor
```

### Database

```bash
# Backup PostgreSQL
pg_dump -U username bandwidth_monitor > backup.sql

# Restore PostgreSQL
psql -U username bandwidth_monitor < backup.sql

# Run migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Health Checks

```bash
# API health
curl http://localhost:8000/api/v1/health

# Redis
redis-cli ping

# Database connection test
psql -U username -d bandwidth_monitor -c "SELECT 1;"
```

## Troubleshooting

### Common Issues

**SECRET_KEY error**

- Generate new key: `openssl rand -hex 32`
- Update .env file

**Database connection failed**

- Verify DATABASE_URL is correct
- Check database is running
- Confirm user has permissions

**Redis connection failed**

- Verify Redis is running: `redis-cli ping`
- Check REDIS_HOST and REDIS_PORT
- Verify Redis password if set

**Permission denied (network monitoring)**

- Ensure NET_ADMIN and NET_RAW capabilities (Docker)
- Or run with sudo / set capabilities (manual)

**High memory usage**

- Check Redis memory: `redis-cli INFO memory`
- Review database connection pool size
- Monitor network packet capture

## Support

- Documentation: See DEPLOYMENT.md
- API Docs: /docs endpoint
- Health Check: /api/v1/health endpoint
- Logs: Check logs/ directory or docker-compose logs
