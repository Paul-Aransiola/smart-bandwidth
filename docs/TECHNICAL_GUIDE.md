# Smart Bandwidth Monitor - Technical Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [System Design](#system-design)
4. [Installation & Setup](#installation--setup)
5. [Configuration](#configuration)
6. [API Reference](#api-reference)
7. [Database Schema](#database-schema)
8. [Development Guide](#development-guide)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  React Frontend │◄───────►│  FastAPI Backend│
│   (Dashboard)   │  REST   │   (Python 3.13) │
└─────────────────┘  WebSocket└────────┬────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            ┌───────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
            │   SQLite     │    │    Redis    │    │   Network   │
            │  (Async)     │    │   (Cache)   │    │  Interface  │
            └──────────────┘    └─────────────┘    └─────────────┘
```

### Clean Architecture Layers

The application follows SOLID principles with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│           Presentation Layer (API)              │
│   FastAPI Routes, WebSocket, Dependencies       │
├─────────────────────────────────────────────────┤
│          Business Logic Layer                   │
│   Services (Network Monitor, Alerts, Reports)   │
├─────────────────────────────────────────────────┤
│          Data Access Layer                      │
│   Repositories (Generic Base + Concrete)        │
├─────────────────────────────────────────────────┤
│          Domain Layer                           │
│   Models, Schemas, Exceptions                   │
└─────────────────────────────────────────────────┘
```

### Design Patterns Used

- **Repository Pattern**: Abstracts database operations with `BaseRepository[ModelType]`
- **Dependency Injection**: FastAPI's DI for loose coupling
- **Factory Pattern**: Service creation and initialization
- **Strategy Pattern**: Different bandwidth control strategies (iptables, tc)
- **Observer Pattern**: Real-time WebSocket updates
- **Singleton Pattern**: Configuration and database session management

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.13+ | Core language |
| **Framework** | FastAPI | Latest | REST API & WebSocket |
| **ORM** | SQLAlchemy | 2.0+ (async) | Database operations |
| **Database** | SQLite | 3.x | Data persistence |
| **Validation** | Pydantic | 2.x | Schema validation |
| **Authentication** | JWT | - | Token-based auth |
| **Password Hashing** | bcrypt | - | Secure passwords |
| **Migrations** | Alembic | Latest | Database versioning |
| **Caching** | Redis | 7.x | Session & rate limiting |
| **Testing** | pytest | Latest | Unit & integration tests |
| **Network Capture** | scapy | Latest | Packet sniffing |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Framework** | React | 19.2.0 | UI framework |
| **Language** | TypeScript | Latest | Type safety |
| **Build Tool** | Vite | 7.2.4 | Fast dev server & bundler |
| **Styling** | Tailwind CSS | Latest | Utility-first CSS |
| **HTTP Client** | Axios | Latest | API calls |
| **Charts** | Recharts | Latest | Data visualization |
| **Icons** | Lucide React | Latest | Icon library |
| **State** | React Hooks | - | Component state |

### DevOps

- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **Process Manager**: systemd (production)
- **Version Control**: Git

---

## System Design

### Directory Structure

```
smart_bandwith/
├── src/                           # Backend source code
│   ├── api/
│   │   ├── routes/               # API endpoints
│   │   │   ├── auth.py           # Authentication & users
│   │   │   ├── devices.py        # Device management
│   │   │   ├── alerts.py         # Alert rules & history
│   │   │   ├── control.py        # Bandwidth control
│   │   │   ├── stats.py          # Statistics
│   │   │   ├── reports.py        # Reporting & export
│   │   │   ├── websocket.py      # WebSocket connections
│   │   │   └── health.py         # Health checks
│   │   └── dependencies/
│   │       └── auth.py           # JWT dependencies
│   ├── core/
│   │   ├── config.py             # Settings & environment
│   │   ├── database.py           # Database setup
│   │   ├── security.py           # JWT & password hashing
│   │   └── exceptions.py         # Custom exceptions
│   ├── models/                   # SQLAlchemy models
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── alert.py
│   │   ├── bandwidth_usage.py
│   │   └── threshold.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user.py
│   │   ├── device.py
│   │   ├── alert.py
│   │   └── bandwidth.py
│   ├── services/                 # Business logic
│   │   ├── network_monitor.py   # Real-time monitoring
│   │   ├── bandwidth_controller.py  # Traffic control
│   │   ├── alert_service.py     # Alert processing
│   │   ├── device_service.py    # Device discovery
│   │   ├── reporting_service.py # Report generation
│   │   └── websocket_manager.py # WebSocket management
│   ├── repositories/             # Data access
│   │   ├── base.py              # Generic repository
│   │   ├── user_repository.py
│   │   ├── device_repository.py
│   │   ├── alert_repository.py
│   │   └── bandwidth_repository.py
│   └── utils/
│       ├── logging.py           # Logging configuration
│       └── helpers.py           # Utility functions
├── dashboard-react/              # Frontend application
│   ├── src/
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   ├── lib/                 # Utilities (axios)
│   │   └── App.tsx              # Main app
│   └── public/
├── tests/                        # Test suite
│   ├── api/                     # API endpoint tests
│   ├── services/                # Service layer tests
│   └── repositories/            # Repository tests
├── alembic/                      # Database migrations
│   └── versions/
├── docs/                         # Documentation
├── scripts/                      # Utility scripts
├── docker-compose.yml           # Docker orchestration
├── Dockerfile                   # Container definition
└── pyproject.toml               # Python dependencies
```

### Data Flow

#### 1. Real-Time Monitoring Flow

```
Network Interface → scapy capture → NetworkMonitor Service
                                          ↓
                                   Parse packets
                                          ↓
                              Device/Bandwidth Repository
                                          ↓
                                    SQLite Database
                                          ↓
                                WebSocket Manager
                                          ↓
                              Connected React Clients
```

#### 2. Alert Flow

```
Bandwidth Threshold Exceeded → Alert Service
                                     ↓
                          Check Alert Rules
                                     ↓
                     ┌────────────────┴────────────────┐
                     ▼                                  ▼
            Create Alert Record              Trigger Notifications
                     ↓                                  ↓
              Alert Repository                   (Email/SMS/etc)
                     ↓
              SQLite Database
```

#### 3. Bandwidth Control Flow

```
User Request → API Endpoint → Bandwidth Controller
                                      ↓
                          Apply iptables/tc rules
                                      ↓
                            Update Device Status
                                      ↓
                            Device Repository
                                      ↓
                              SQLite Database
```

---

## Installation & Setup

### Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.11 or higher
- **Permissions**: Root/sudo for network monitoring
- **Optional**: Docker & Docker Compose

### Installation Methods

#### Method 1: Manual Installation

```bash
# 1. Clone repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth.git
cd smart-bandwidth

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -e .

# 4. Run database migrations
alembic upgrade head

# 5. Create admin user
python scripts/create_admin.py

# 6. Start backend
uvicorn src.main:app --host 0.0.0.0 --port 8000

# 7. Start frontend (separate terminal)
cd dashboard-react
npm install
npm run dev
```

#### Method 2: Docker Installation

```bash
# 1. Clone repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth.git
cd smart-bandwidth

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f api
```

See [DOCKER_SETUP_GUIDE.md](../DOCKER_SETUP_GUIDE.md) for detailed Docker instructions.

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/bandwidth_monitor.db

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Network Monitoring
NETWORK_INTERFACE=eth0
PACKET_CAPTURE_FILTER=ip

# Redis (Optional)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

### Configuration Class

Located in `src/core/config.py`:

```python
class Settings(BaseSettings):
    # API settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bandwidth_monitor.db"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Network
    NETWORK_INTERFACE: str = "eth0"
    
    class Config:
        env_file = ".env"
```

---

## API Reference

### Authentication Endpoints

#### POST `/api/v1/auth/login`

Login and receive JWT token.

**Request:**

```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

#### POST `/api/v1/auth/register`

Register new user (admin only).

**Request:**

```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "role": "user"
}
```

### Device Endpoints

#### GET `/api/v1/devices`

List all devices with pagination.

**Query Parameters:**

- `skip` (int): Offset for pagination
- `limit` (int): Number of results
- `status` (str): Filter by status (active/blocked/throttled)

**Response:**

```json
{
  "devices": [
    {
      "id": 1,
      "ip_address": "192.168.1.100",
      "mac_address": "AA:BB:CC:DD:EE:FF",
      "device_name": "John's Laptop",
      "status": "active",
      "total_bytes": 1073741824,
      "last_seen": "2025-12-12T01:00:00"
    }
  ],
  "total": 45
}
```

#### PUT `/api/v1/devices/{device_id}/control`

Control device bandwidth.

**Request:**

```json
{
  "action": "throttle",
  "bandwidth_limit_mbps": 5.0
}
```

### Alert Endpoints

#### POST `/api/v1/alerts/rules`

Create alert rule.

**Request:**

```json
{
  "name": "High Bandwidth Alert",
  "threshold_type": "bandwidth",
  "threshold_value": 10737418240,
  "time_window_minutes": 60,
  "notification_channels": ["email"],
  "is_active": true
}
```

#### GET `/api/v1/alerts/history`

Get alert history with filters.

### WebSocket Endpoint

#### WS `/api/v1/ws/stats`

Real-time bandwidth statistics.

**Client receives:**

```json
{
  "type": "bandwidth_stats",
  "data": {
    "total_devices": 45,
    "active_devices": 32,
    "total_bandwidth": 1073741824,
    "bandwidth_history": [
      {"timestamp": "2025-12-12T01:00:00", "bytes": 10485760}
    ]
  }
}
```

For complete API documentation, visit `/docs` (Swagger UI) or `/redoc` when the server is running.

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────┐
│    User     │       │   Device     │
├─────────────┤       ├──────────────┤
│ id (PK)     │       │ id (PK)      │
│ username    │       │ ip_address   │
│ email       │       │ mac_address  │
│ password    │       │ device_name  │
│ role        │       │ status       │
│ created_at  │       │ last_seen    │
└─────────────┘       └──────┬───────┘
                              │
                              │ 1:N
                              │
                      ┌───────▼────────┐
                      │ BandwidthUsage │
                      ├────────────────┤
                      │ id (PK)        │
                      │ device_id (FK) │
                      │ bytes_sent     │
                      │ bytes_received │
                      │ timestamp      │
                      └────────────────┘

┌─────────────┐       ┌──────────────┐
│  AlertRule  │       │ AlertHistory │
├─────────────┤       ├──────────────┤
│ id (PK)     │ 1:N   │ id (PK)      │
│ name        ├───────┤ rule_id (FK) │
│ threshold   │       │ device_id    │
│ time_window │       │ triggered_at │
│ is_active   │       │ status       │
└─────────────┘       └──────────────┘
```

### Key Models

#### User Model

```python
class User(Base):
    id: int
    username: str (unique)
    email: str (unique)
    hashed_password: str
    role: str  # "admin" or "user"
    is_active: bool
    created_at: datetime
```

#### Device Model

```python
class Device(Base):
    id: int
    ip_address: str
    mac_address: str (unique)
    device_name: str
    status: str  # "active", "blocked", "throttled"
    bandwidth_limit_mbps: float
    total_bytes: int
    last_seen: datetime
```

#### AlertRule Model

```python
class AlertRule(Base):
    id: int
    name: str
    threshold_type: str  # "bandwidth", "device_count"
    threshold_value: float
    time_window_minutes: int
    notification_channels: JSON
    is_active: bool
    created_at: datetime
```

---

## Development Guide

### Setting Up Development Environment

```bash
# 1. Install development dependencies
pip install -e ".[dev]"

# 2. Install pre-commit hooks
pre-commit install

# 3. Run tests
pytest

# 4. Run with auto-reload
uvicorn src.main:app --reload
```

### Code Style

- **Formatter**: Black (line length: 88)
- **Linter**: Ruff
- **Type Checker**: mypy
- **Import Sorting**: isort

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type check
mypy src/
```

### Repository Pattern Usage

All data access goes through repositories:

```python
from src.repositories.device_repository import DeviceRepository

# In your service/route
async def get_device(device_id: int, db: AsyncSession):
    device_repo = DeviceRepository(db)
    device = await device_repo.get_by_id(device_id)
    
    if not device:
        raise HTTPException(status_code=404)
    
    return device
```

**IMPORTANT**: Repository methods expect model instances, not dicts or IDs:

```python
# ✅ CORRECT
device = Device(ip_address="192.168.1.1", mac_address="AA:BB:CC:DD:EE:FF")
await device_repo.create(device)

# ❌ WRONG
device_dict = {"ip_address": "192.168.1.1"}
await device_repo.create(device_dict)  # Will fail!
```

### Adding New Features

1. **Create Model** (`src/models/`)
2. **Create Schema** (`src/schemas/`)
3. **Create Repository** (`src/repositories/`)
4. **Create Service** (`src/services/`)
5. **Create Route** (`src/api/routes/`)
6. **Write Tests** (`tests/`)
7. **Create Migration** (`alembic revision --autogenerate`)

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/api/test_devices.py

# Run specific test
pytest tests/api/test_devices.py::test_get_devices
```

### Test Structure

```
tests/
├── conftest.py              # Fixtures
├── api/
│   ├── test_auth.py        # Authentication tests
│   ├── test_devices.py     # Device endpoint tests
│   └── test_alerts.py      # Alert endpoint tests
├── services/
│   ├── test_network_monitor.py
│   └── test_alert_service.py
└── repositories/
    └── test_device_repository.py
```

### Writing Tests

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_device(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/devices",
        json={"ip_address": "192.168.1.1", "mac_address": "AA:BB:CC:DD:EE:FF"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ip_address"] == "192.168.1.1"
```

---

## Deployment

### Production Deployment

#### Using systemd

1. Create service file `/etc/systemd/system/bandwidth-monitor.service`:

```ini
[Unit]
Description=Smart Bandwidth Monitor API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/smart_bandwidth
Environment="PATH=/opt/smart_bandwidth/.venv/bin"
ExecStart=/opt/smart_bandwidth/.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Enable and start:

```bash
sudo systemctl enable bandwidth-monitor
sudo systemctl start bandwidth-monitor
sudo systemctl status bandwidth-monitor
```

#### Using Docker Compose (Production)

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

#### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name bandwidth.example.com;

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location / {
        proxy_pass http://localhost:5173;
        proxy_set_header Host $host;
    }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Permission Denied for Network Capture

**Error**: `PermissionError: [Errno 1] Operation not permitted`

**Solution**:

```bash
# Run with sudo
sudo uvicorn src.main:app --host 0.0.0.0 --port 8000

# Or grant capabilities
sudo setcap cap_net_raw,cap_net_admin=eip $(which python3)
```

#### 2. WebSocket Connection Refused

**Error**: `WebSocket connection failed`

**Solution**:

- Check backend is running on correct port
- Verify CORS settings in `.env`
- Check firewall rules

#### 3. Database Migration Errors

**Error**: `alembic.util.exc.CommandError`

**Solution**:

```bash
# Check current revision
alembic current

# Stamp to latest (if out of sync)
alembic stamp head

# Run migration
alembic upgrade head
```

#### 4. High Memory Usage

**Symptom**: Backend using excessive RAM

**Solution**:

- Reduce packet capture buffer size
- Lower bandwidth history retention
- Enable database query optimization
- Consider Redis for caching

#### 5. Frontend Build Errors

**Error**: `Module not found` or `Type errors`

**Solution**:

```bash
cd dashboard-react
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Debug Mode

Enable debug logging:

```python
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

View logs:

```bash
# Backend logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f api
```

---

## Performance Optimization

### Database Optimization

```python
# Use eager loading to prevent N+1 queries
from sqlalchemy.orm import selectinload

devices = await db.execute(
    select(Device).options(selectinload(Device.bandwidth_usage))
)
```

### Caching with Redis

```python
from redis import asyncio as aioredis

# Cache frequently accessed data
redis = aioredis.from_url("redis://localhost")
await redis.set("device:1", json.dumps(device_data), ex=300)
```

### WebSocket Optimization

- Limit message frequency (debounce)
- Compress large payloads
- Use binary protocols for high-throughput

---

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` template
2. **Rotate JWT secrets regularly** - Update `SECRET_KEY`
3. **Use HTTPS in production** - Configure SSL certificates
4. **Implement rate limiting** - Prevent API abuse
5. **Validate all inputs** - Pydantic schemas + sanitization
6. **Use parameterized queries** - SQLAlchemy ORM handles this
7. **Keep dependencies updated** - Regular `pip install --upgrade`
8. **Audit logs** - Track admin actions
9. **Principle of least privilege** - Role-based access control
10. **Regular backups** - Automated database backups

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [React Documentation](https://react.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Scapy Documentation](https://scapy.readthedocs.io/)

For specific feature documentation, see the `docs/` directory:

- [Bandwidth Threshold Implementation](./BANDWIDTH_THRESHOLD.md)
- [Global Threshold Implementation](./GLOBAL_THRESHOLD_IMPLEMENTATION.md)
- [Scapy Integration Guide](./SCAPY_INTEGRATION.md)
- [Responsive Design Guide](./RESPONSIVE_DESIGN_GUIDE.md)
- [Docker Setup Guide](../DOCKER_SETUP_GUIDE.md)
- [Quick Start Guide](../QUICKSTART.md)
