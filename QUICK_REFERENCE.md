# Quick Reference Guide - Smart Bandwidth Monitor

## 🚀 Quick Start Commands

```bash
# Development Setup
uv sync                          # Install dependencies
cp .env.example .env             # Create environment file
sudo uv run python src/main.py  # Run application (requires sudo)

# Docker
docker-compose up --build        # Build and run
docker-compose logs -f api       # View logs

# Testing
uv run pytest                    # Run tests
uv run pytest --cov=src         # Run with coverage

# Code Quality
uv run black src/               # Format code
uv run isort src/               # Sort imports
uv run ruff check src/          # Lint code
```

## 📁 Project Structure

```
smart_bandwith/
├── src/
│   ├── api/routes/         # API endpoints
│   │   ├── devices.py      # Device CRUD operations
│   │   ├── health.py       # Health checks
│   │   └── stats.py        # Statistics endpoints
│   ├── core/               # Core business logic
│   │   ├── config.py       # Configuration management
│   │   ├── database.py     # Database setup
│   │   └── exceptions.py   # Custom exceptions
│   ├── models/             # SQLAlchemy models
│   │   └── device.py       # Device, BandwidthUsage, BlockHistory
│   ├── repositories/       # Data access layer
│   │   ├── base.py         # Base repository
│   │   ├── device_repository.py
│   │   └── bandwidth_repository.py
│   ├── schemas/            # Pydantic schemas
│   │   └── device.py       # Request/response models
│   ├── services/           # Business services
│   │   ├── network_monitor.py      # Packet capture
│   │   └── bandwidth_controller.py # Traffic control
│   ├── utils/              # Utilities
│   │   └── logger.py       # Logging setup
│   └── main.py             # FastAPI application
├── tests/                  # Test suite
├── docs/                   # Documentation
├── dashboard/              # Web dashboard
├── Dockerfile              # Docker build
├── docker-compose.yml      # Docker services
├── pyproject.toml          # Dependencies
├── .env.example            # Environment template
└── README.md               # Main documentation
```

## 🔌 API Endpoints

### Base URL: `http://localhost:8000/api/v1`

```
GET    /health                     # Health check
GET    /health/detailed            # Detailed health info

GET    /devices                    # List all devices
GET    /devices/{id}               # Get device by ID
GET    /devices/ip/{ip}            # Get device by IP
POST   /devices                    # Create device
PATCH  /devices/{id}               # Update device
DELETE /devices/{id}               # Delete device

GET    /stats                      # Overall statistics
GET    /stats/top-consumers        # Top bandwidth users

# TODO: Control endpoints (to be implemented)
POST   /control/block/{ip}         # Block device
POST   /control/unblock/{ip}       # Unblock device
POST   /control/throttle/{ip}      # Throttle device
```

## 🔧 Environment Variables

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Database
DATABASE_URL=sqlite+aiosqlite:///./bandwidth_monitor.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Network Monitoring
NETWORK_INTERFACE=eth0           # Change to your interface!
MONITOR_INTERVAL=5
PACKET_CAPTURE_TIMEOUT=10

# Bandwidth Control
MAX_BANDWIDTH_MBPS=100
DEFAULT_THROTTLE_MBPS=10
ENABLE_BLOCKING=true
ENABLE_THROTTLING=true

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
```

## 🐛 Common Issues & Solutions

### 1. Permission Denied for Packet Capture

**Error**: `PermissionError: packet capture requires root/admin privileges`

**Solution**:

```bash
# Option 1: Run with sudo
sudo uv run python src/main.py

# Option 2: Set capabilities (Linux only)
sudo setcap cap_net_raw,cap_net_admin=eip $(which python)
```

### 2. Network Interface Not Found

**Error**: `NetworkMonitorException: Network interface 'eth0' not found`

**Solution**:

```bash
# List available interfaces
ip link show

# or
ifconfig

# Update .env with correct interface
NETWORK_INTERFACE=wlan0  # or your interface name
```

### 3. iptables Command Not Found

**Error**: `BandwidthControlException: Command failed: iptables`

**Solution**:

```bash
# Install iptables (Ubuntu/Debian)
sudo apt-get install iptables

# Install iptables (CentOS/RHEL)
sudo yum install iptables
```

### 4. Database Locked Error

**Error**: `sqlite3.OperationalError: database is locked`

**Solution**: SQLite has limitations with concurrent access. For production:

```bash
# Use PostgreSQL instead
DATABASE_URL=postgresql+asyncpg://user:password@localhost/bandwidth_db
```

### 5. Port Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Solution**:

```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change port in .env
API_PORT=8001
```

## 📊 Database Schema

### Device Table

```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    ip_address VARCHAR(45) UNIQUE NOT NULL,
    mac_address VARCHAR(17) UNIQUE NOT NULL,
    hostname VARCHAR(255),
    device_name VARCHAR(255),
    status VARCHAR(20) NOT NULL,
    first_seen TIMESTAMP NOT NULL,
    last_seen TIMESTAMP NOT NULL,
    is_blocked BOOLEAN NOT NULL DEFAULT 0,
    is_throttled BOOLEAN NOT NULL DEFAULT 0,
    throttle_limit_mbps FLOAT,
    total_bytes_sent INTEGER NOT NULL DEFAULT 0,
    total_bytes_received INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);
```

### BandwidthUsage Table

```sql
CREATE TABLE bandwidth_usage (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMP NOT NULL,
    bytes_sent INTEGER NOT NULL DEFAULT 0,
    bytes_received INTEGER NOT NULL DEFAULT 0,
    packets_sent INTEGER NOT NULL DEFAULT 0,
    packets_received INTEGER NOT NULL DEFAULT 0,
    upload_speed_mbps FLOAT NOT NULL DEFAULT 0.0,
    download_speed_mbps FLOAT NOT NULL DEFAULT 0.0
);
```

### BlockHistory Table

```sql
CREATE TABLE block_history (
    id INTEGER PRIMARY KEY,
    device_id INTEGER NOT NULL REFERENCES devices(id),
    action VARCHAR(20) NOT NULL,
    reason TEXT,
    throttle_limit_mbps FLOAT,
    created_at TIMESTAMP NOT NULL,
    created_by VARCHAR(255)
);
```

## 🧪 Testing Patterns

### Unit Test Example

```python
import pytest
from src.repositories.device_repository import DeviceRepository

@pytest.mark.asyncio
async def test_get_device_by_ip(db_session):
    repo = DeviceRepository(db_session)
    device = await repo.get_by_ip("192.168.1.100")
    assert device is not None
    assert device.ip_address == "192.168.1.100"
```

### Integration Test Example

```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_list_devices():
    response = client.get("/api/v1/devices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## 🎯 Next Implementation Steps

1. **Control Endpoints** (Priority 1)
   - File: `src/api/routes/control.py`
   - Endpoints: block, unblock, throttle, unthrottle

2. **Device Service** (Priority 2)
   - File: `src/services/device_service.py`
   - Orchestrate repositories and business logic

3. **Background Monitoring** (Priority 3)
   - Integrate NetworkMonitor with FastAPI lifecycle
   - Periodic bandwidth recording task

4. **Authentication** (Priority 4)
   - JWT token generation
   - Login endpoint
   - Protected routes

## 📚 Useful Resources

- FastAPI Docs: <https://fastapi.tiangolo.com/>
- SQLAlchemy 2.0: <https://docs.sqlalchemy.org/en/20/>
- Scapy Tutorial: <https://scapy.readthedocs.io/>
- UV Package Manager: <https://github.com/astral-sh/uv>

## 👤 Contact

**Author**: Paul Aransiola  
**Email**: <paularansiola60@gmail.com>  
**GitHub**: @Paul-Aransiola

---

**Last Updated**: November 17, 2025
