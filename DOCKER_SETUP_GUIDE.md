# Docker Setup Guide for Smart Bandwidth Monitor

## Overview

Running the Smart Bandwidth Monitor in Docker **completely bypasses macOS limitations** including:

- ✅ **No sudo password needed** - Docker handles privileges
- ✅ **Full packet capture** - Linux container has native support
- ✅ **Real iptables/tc** - Traffic control works properly
- ✅ **Network monitoring** - Scapy works without BPF restrictions
- ✅ **Isolated environment** - Clean, reproducible setup

---

## Quick Start

### 1. Prerequisites

Install Docker Desktop for Mac:

```bash
# Download from https://www.docker.com/products/docker-desktop
# Or install via Homebrew:
brew install --cask docker
```

**Start Docker Desktop** and ensure it's running.

### 2. Build and Run

```bash
# Navigate to project directory
cd /Users/admin/Documents/smart_bandwith

# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access the Application

- **Frontend**: <http://localhost:5173>
- **Backend API**: <http://localhost:8000>
- **API Docs**: <http://localhost:8000/docs>

---

## How Docker Bypasses macOS Limitations

### 1. **Packet Capture (Scapy/BPF)**

**macOS Problem**:

```bash
# On macOS, requires sudo and has BPF device limitations
sudo python src/main.py
# Permission denied: /dev/bpf0
```

**Docker Solution**:

```dockerfile
# Container runs Linux with native packet capture
cap_add:
  - NET_ADMIN
  - NET_RAW
privileged: true
network_mode: "host"
```

✅ **Result**: Full packet capture without password prompts

### 2. **Traffic Control (iptables/tc)**

**macOS Problem**:

```bash
# iptables doesn't exist on macOS
iptables -A INPUT -s 192.168.1.100 -j DROP
# command not found
```

**Docker Solution**:

```dockerfile
# Linux container has iptables and tc pre-installed
RUN apt-get install -y iptables iproute2
```

✅ **Result**: Real bandwidth throttling and blocking

### 3. **Network Interface Access**

**macOS Problem**:

```python
# Limited network interface access
import scapy.all as scapy
scapy.sniff(iface="en0")  # Requires root
```

**Docker Solution**:

```yaml
# Host network mode gives direct access
network_mode: "host"
environment:
  - NETWORK_INTERFACE=eth0
```

✅ **Result**: Direct network monitoring

### 4. **System Calls**

**macOS Problem**:

- Different system call interface
- Security restrictions (SIP)
- Code signing requirements

**Docker Solution**:

- Linux kernel in container
- Native system call support
- No SIP restrictions

✅ **Result**: All monitoring features work

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      macOS Host                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │         Docker Desktop (Linux VM)                  │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │   bandwidth-monitor-api (Python)            │  │ │
│  │  │   - FastAPI backend                         │  │ │
│  │  │   - Scapy packet capture                    │  │ │
│  │  │   - iptables/tc traffic control             │  │ │
│  │  │   - SQLite database                         │  │ │
│  │  │   Capabilities: NET_ADMIN, NET_RAW          │  │ │
│  │  │   Port: 8000                                │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │   bandwidth-monitor-dashboard (Node)        │  │ │
│  │  │   - React + TypeScript                      │  │ │
│  │  │   - Vite dev server                         │  │ │
│  │  │   - Hot Module Replacement                  │  │ │
│  │  │   Port: 5173                                │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────────────┐  │ │
│  │  │   bandwidth-monitor-redis (Optional)        │  │ │
│  │  │   - Caching layer                           │  │ │
│  │  │   - Session storage                         │  │ │
│  │  │   Port: 6379                                │  │ │
│  │  └─────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
        ↓                    ↓                    ↓
    Browser             API Requests         Network Traffic
```

---

## Docker Commands

### Basic Operations

```bash
# Build images
docker-compose build

# Start services (detached)
docker-compose up -d

# Start services (with logs)
docker-compose up

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
docker-compose logs -f dashboard
```

### Development

```bash
# Rebuild after code changes
docker-compose up -d --build

# Execute command in running container
docker-compose exec api bash
docker-compose exec api python -c "import scapy; print(scapy.__version__)"

# View container stats
docker stats

# Inspect network
docker network inspect smart_bandwith_bandwidth-monitor-network
```

### Debugging

```bash
# Check if services are running
docker-compose ps

# View container details
docker inspect bandwidth-monitor-api

# Check logs for errors
docker-compose logs api | grep ERROR

# Shell into container
docker-compose exec api bash

# Test packet capture inside container
docker-compose exec api python -c "from scapy.all import sniff; print('Scapy works!')"

# Check network interfaces in container
docker-compose exec api ip addr show

# Test iptables in container
docker-compose exec api iptables -L

# Check running processes
docker-compose exec api ps aux
```

---

## Network Modes

### Option 1: Host Network (Recommended for Monitoring)

```yaml
api:
  network_mode: "host"
```

**Pros**:

- Direct access to host network interfaces
- Can monitor real network traffic
- Best for packet capture

**Cons**:

- Less isolation
- Port conflicts with host

### Option 2: Bridge Network (Default)

```yaml
networks:
  bandwidth-monitor-network:
    driver: bridge
```

**Pros**:

- Better isolation
- No port conflicts
- Standard Docker networking

**Cons**:

- Monitors Docker network, not host
- Limited visibility into host traffic

### Recommendation

For **development/testing**: Use bridge network
For **production monitoring**: Use host network mode

---

## Environment Variables

Create `.env` file in project root:

```bash
# Application
ENV=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./bandwidth_monitor.db

# Monitoring
ENABLE_MONITORING=true
MONITORING_INTERVAL=30
NETWORK_INTERFACE=eth0

# Security
SECRET_KEY=change-this-to-a-random-secret-key-in-production

# Redis (Optional)
REDIS_ENABLED=false
REDIS_HOST=redis
REDIS_PORT=6379
```

---

## Volume Mounts

### Persistent Data

```yaml
volumes:
  - ./bandwidth_monitor.db:/app/bandwidth_monitor.db  # Database
  - ./logs:/app/logs                                   # Application logs
  - ./data:/app/data                                   # Additional data
```

### Hot Reload (Development)

```yaml
volumes:
  - ./src:/app/src  # Backend code changes reflect immediately
  - ./dashboard-react:/app  # Frontend code changes reflect immediately
```

---

## Production Deployment

### 1. Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bandwidth-monitor-api
    restart: always
    network_mode: "host"
    cap_add:
      - NET_ADMIN
      - NET_RAW
    privileged: true
    environment:
      - ENV=production
      - LOG_LEVEL=WARNING
      - ENABLE_MONITORING=true
    volumes:
      - ./bandwidth_monitor.db:/app/bandwidth_monitor.db
      - ./logs:/app/logs

  dashboard:
    build:
      context: ./dashboard-react
      dockerfile: Dockerfile.prod
    container_name: bandwidth-monitor-dashboard
    restart: always
    ports:
      - "80:80"
    depends_on:
      - api
```

### 2. Build Production Images

```bash
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

---

## Security Considerations

### 1. Privileged Mode

Docker containers run with `privileged: true` for network access:

```yaml
privileged: true
cap_add:
  - NET_ADMIN
  - NET_RAW
  - SYS_ADMIN
```

**Security**: Only use on trusted networks. Consider:

- Running on dedicated monitoring host
- Using firewall rules
- Implementing authentication
- Regular security updates

### 2. Network Isolation

For production, use separate networks:

```yaml
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### 3. Secrets Management

Never commit secrets to Git. Use:

- Docker secrets
- Environment files (.env)
- Secret management tools (Vault, AWS Secrets Manager)

---

## Performance Tuning

### 1. Resource Limits

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
      reservations:
        cpus: '1'
        memory: 1G
```

### 2. Logging

```yaml
api:
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### 3. Health Checks

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Troubleshooting

### Issue: Permission Denied

```bash
# Error: Permission denied accessing /dev/bpf
```

**Solution**: Ensure privileged mode is enabled:

```yaml
privileged: true
cap_add:
  - NET_ADMIN
  - NET_RAW
```

### Issue: Cannot Find Network Interface

```bash
# Error: Interface 'en0' not found
```

**Solution**: Check available interfaces in container:

```bash
docker-compose exec api ip addr show
# Use eth0 or available interface
```

### Issue: Port Already in Use

```bash
# Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**Solution**: Stop conflicting service or change port:

```yaml
ports:
  - "8001:8000"  # Map to different host port
```

### Issue: Database Locked

```bash
# Error: SQLite database is locked
```

**Solution**: Ensure single instance:

```bash
docker-compose down
docker-compose up -d
```

### Issue: Packet Capture Not Working

```bash
# No packets captured
```

**Solution**: Use host network mode:

```yaml
network_mode: "host"
```

---

## Comparison: Native vs Docker

| Feature | macOS Native | Docker Container |
|---------|-------------|------------------|
| Packet Capture | ❌ Requires sudo | ✅ Works automatically |
| iptables | ❌ Not available | ✅ Fully functional |
| Traffic Control (tc) | ❌ Not available | ✅ Fully functional |
| Network Monitoring | ⚠️ Limited | ✅ Complete access |
| Setup Complexity | ⚠️ Moderate | ✅ Simple |
| Password Prompts | ❌ Every time | ✅ Never |
| Isolation | ✅ Native | ⚠️ Containerized |
| Performance | ✅ Best | ⚠️ Near-native |
| Portability | ❌ macOS only | ✅ Any platform |

---

## Next Steps

1. **Start the stack**:

   ```bash
   docker-compose up -d
   ```

2. **Verify services**:

   ```bash
   docker-compose ps
   curl http://localhost:8000/api/v1/health
   ```

3. **Access dashboard**:
   - Open <http://localhost:5173>

4. **Check logs**:

   ```bash
   docker-compose logs -f api
   ```

5. **Test packet capture**:

   ```bash
   docker-compose exec api python -c "from scapy.all import sniff; print('Packet capture working!')"
   ```

---

## Benefits Summary

### ✅ What Docker Solves

1. **No More Sudo**: No password prompts ever
2. **Real Traffic Control**: iptables and tc work properly
3. **Full Packet Capture**: Scapy works without restrictions
4. **Clean Environment**: Isolated from macOS quirks
5. **Easy Setup**: One command to start everything
6. **Reproducible**: Same environment everywhere
7. **Production-Ready**: Deploy anywhere Docker runs

### 🚀 Getting All Features Working

With Docker, **ALL** bandwidth monitoring features work:

- ✅ Real-time packet capture
- ✅ Device blocking (iptables)
- ✅ Bandwidth throttling (tc)
- ✅ Network scanning
- ✅ Traffic statistics
- ✅ No macOS limitations!

---

## Support

For issues or questions:

1. Check logs: `docker-compose logs -f`
2. Verify services: `docker-compose ps`
3. Inspect containers: `docker inspect <container>`
4. Shell into container: `docker-compose exec api bash`

**Docker completely eliminates macOS limitations and provides a production-ready monitoring solution!** 🎉
