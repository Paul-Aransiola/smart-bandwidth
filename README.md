# 🌐 Smart Bandwidth Monitor & Control System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.2.0-61DAFB?logo=react&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-Latest-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

**A comprehensive, real-time network bandwidth monitoring and control system for shared Wi-Fi environments**

[Features](#-features) • [Demo](#-demo) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

Smart Bandwidth Monitor is a production-ready, full-stack solution for managing bandwidth in shared Wi-Fi networks such as hostels, cafés, co-working spaces, and small offices. Built with Python 3.13 and React 19, it provides real-time packet-level monitoring, intelligent alerting, and granular bandwidth control through a responsive web dashboard.

### 🎯 Problem Statement

In shared Wi-Fi environments, a few users can monopolize bandwidth, degrading the experience for everyone. Enterprise-grade solutions cost thousands of dollars and require specialized expertise. **Smart Bandwidth Monitor** bridges this gap with an open-source, easy-to-deploy system that gives administrators complete visibility and control over network usage without breaking the bank.

### ✨ Why Smart Bandwidth Monitor?

- **💰 Cost-Effective**: Open-source (MIT License) alternative to $3,000+ enterprise tools
- **🚀 Easy Deployment**: Docker Compose setup in 5 minutes, no networking expertise required
- **📊 Real-Time Insights**: Live packet-level bandwidth tracking per device with WebSocket updates
- **🎛️ Advanced Control**: Throttle, block, schedule, and set quotas for devices
- **🔔 Intelligent Alerts**: Customizable rules with email/SMS/webhook notifications
- **📱 Responsive UI**: Mobile-first design with hamburger navigation for all screen sizes
- **🔒 Production-Ready Security**: JWT authentication, bcrypt hashing, role-based access control
- **🏗️ Clean Architecture**: Repository pattern, dependency injection, SOLID principles, 48% test coverage

---

## 🎁 Features

### Core Monitoring & Control

#### 📡 Real-Time Network Monitoring

- **Live packet capture** using Scapy with async processing (3-5 second intervals)
- **Per-device tracking**: Bytes sent/received, protocols, active connections
- **Protocol analysis**: TCP, UDP, ICMP breakdown with port identification
- **WebSocket live updates**: Sub-second dashboard refresh without polling
- **Network scanner**: Automatic device discovery with MAC/IP correlation

#### 🖥️ Device Management

- **Auto-discovery**: Scapy-based ARP scanning for new devices
- **Device profiling**: Assign friendly names, track first/last seen timestamps
- **Status management**: Active, blocked, throttled, unlimited states
- **Bulk operations**: Select multiple devices for batch actions
- **MAC filtering**: Whitelist/blacklist by hardware address
- **Bandwidth history**: Historical usage graphs per device

#### 🎛️ Advanced Bandwidth Control

- **Traffic shaping**: Linux iptables/tc integration for rate limiting
- **Device throttling**: Set per-device limits (e.g., 5 Mbps down, 2 Mbps up)
- **Complete blocking**: Instantly disconnect abusive devices
- **Bandwidth quotas**: Daily/weekly/monthly data caps with auto-throttle
- **Scheduled controls**: Time-based rules (e.g., limit streaming 9 PM-6 AM)
- **QoS policies**: Priority levels (Critical, High, Medium, Low) for traffic shaping

### Alert & Notification System

#### 🔔 Smart Alerts

- **Threshold monitoring**: Bandwidth, device count, connection duration
- **Alert conditions**: Greater than, less than, equal to, between ranges
- **Alert severities**: Critical, Warning, Info levels
- **Time windows**: 15 min, 1 hour, 24 hours, 7 days
- **Multi-channel notifications**: Email, SMS, webhook (Slack/Discord ready)
- **Auto-actions**: Trigger throttle/block on threshold breach
- **Alert history**: Full audit trail with timestamps and resolution status
- **Cooldown periods**: Prevent alert spam with configurable delays

### Reporting & Analytics

#### 📊 Advanced Reporting

- **Usage reports**: Daily, weekly, monthly summaries with CSV/JSON export
- **Top consumers**: Identify bandwidth hogs with sortable tables
- **Trend analysis**: Line/bar/pie charts with Recharts visualization
- **Protocol distribution**: See what's consuming bandwidth (streaming, gaming, web)
- **Peak hour detection**: Identify high-traffic periods for capacity planning
- **Custom date ranges**: Generate reports for any time period
- **Bandwidth forecasting**: Predict future usage based on trends

### User Management & Security

#### 🔐 Authentication & Authorization

- **JWT-based authentication**: Secure token-based login with expiration
- **Role-based access control (RBAC)**: Admin and User roles with distinct permissions
- **Password security**: bcrypt hashing with configurable work factor
- **User registration**: Admin-controlled account creation
- **Session management**: Token refresh, logout, concurrent session handling
- **API key support**: Programmatic access for integrations

### Technical Features

#### 🏗️ Architecture & Code Quality

- **Repository pattern**: Abstracted data access with generic base repository
- **Dependency injection**: FastAPI's DI for loose coupling and testability
- **Async/await throughout**: High-performance async database and HTTP operations
- **SOLID principles**: Single responsibility, clean separation of concerns
- **Comprehensive testing**: pytest with 48% coverage (44+ test cases)
- **Type safety**: Full type hints with Pydantic v2 validation
- **Database migrations**: Alembic for versioned schema changes

#### 📦 Deployment & Operations

- **Docker Compose**: Multi-container orchestration (API, Dashboard, Redis)
- **Health checks**: `/api/v1/health` endpoint with dependency validation
- **Structured logging**: JSON logs with rotation and levels
- **Configuration management**: Environment-based settings with validation
- **Nginx integration**: Reverse proxy configs for production
- **Systemd service**: Native Linux service with auto-restart
- **Database choice**: SQLite (default) with async support via aiosqlite

---

## 🏛️ Architecture

### High-Level Overview

```
┌──────────────────────────────────────────────────────────────┐
│                        End Users                              │
│              (Browsers, Mobile Devices)                       │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   React Frontend (Dashboard)                  │
│         TypeScript • Vite • Tailwind CSS • Recharts          │
│              WebSocket Connection for Real-Time               │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API / WebSocket
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Backend (Python)                    │
│        Routes → Services → Repositories → Models              │
│     JWT Auth • Alert Engine • Network Monitor • Reports      │
└─────┬────────────────┬───────────────────┬───────────────────┘
      │                │                   │
      ▼                ▼                   ▼
┌──────────┐     ┌──────────┐       ┌─────────────┐
│  SQLite  │     │  Redis   │       │   Network   │
│ (Async)  │     │ (Cache)  │       │  Interface  │
│          │     │          │       │  (eth0, etc)│
└──────────┘     └──────────┘       └─────────────┘
```

### Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Frontend** | React + TypeScript | 19.2.0 | Modern, type-safe UI |
| **UI Framework** | Tailwind CSS | 4.x | Responsive, utility-first styling |
| **Icons** | Lucide React | 0.555+ | Beautiful, consistent icons |
| **Charts** | Recharts | 3.5.1 | Interactive data visualization |
| **Build Tool** | Vite | 7.2.4 | Lightning-fast dev server & bundler |
| **Backend** | FastAPI + Python | 3.13+ | High-performance async API |
| **ORM** | SQLAlchemy | 2.0.35+ | Async database operations |
| **Database** | SQLite + aiosqlite | 3.x | Lightweight, serverless DB |
| **Cache** | Redis | 7.x (optional) | Session & rate limiting |
| **Auth** | JWT + bcrypt | - | Secure token authentication |
| **Network** | Scapy + psutil | 2.5.0+ | Packet capture & system info |
| **Validation** | Pydantic | 2.9.2+ | Schema validation & settings |
| **Migrations** | Alembic | 1.13.3+ | Database versioning |
| **Testing** | pytest + pytest-asyncio | 8.3.3+ | Comprehensive test suite |
| **HTTP Client** | httpx (tests) + aiohttp | - | Async HTTP operations |
| **Containerization** | Docker + Docker Compose | - | Multi-container deployment |

### Project Structure

```
smart_bandwith/
├── src/                              # Backend source code
│   ├── api/
│   │   ├── routes/                   # API endpoints
│   │   │   ├── auth.py              # Authentication & JWT login
│   │   │   ├── users.py             # User management (CRUD)
│   │   │   ├── devices.py           # Device monitoring & control
│   │   │   ├── alerts.py            # Alert rules & history
│   │   │   ├── control.py           # Bandwidth throttling/blocking
│   │   │   ├── advanced_controls.py # Quotas, QoS, schedules
│   │   │   ├── threshold.py         # Global threshold settings
│   │   │   ├── stats.py             # Real-time statistics
│   │   │   ├── dashboard.py         # Dashboard aggregations
│   │   │   ├── reports.py           # Usage reports & exports
│   │   │   ├── websocket.py         # WebSocket connections
│   │   │   └── health.py            # Health check endpoint
│   │   └── dependencies/
│   │       └── auth.py              # JWT auth dependencies
│   ├── core/
│   │   ├── config.py                # Settings & environment vars
│   │   ├── database.py              # Async DB session management
│   │   ├── security.py              # JWT & password hashing
│   │   └── exceptions.py            # Custom exception classes
│   ├── models/                      # SQLAlchemy ORM models
│   │   ├── user.py                  # User & UserRole
│   │   ├── device.py                # Device, BandwidthUsage, BlockHistory
│   │   ├── alert.py                 # AlertRule, Alert, enums
│   │   ├── advanced_controls.py     # BandwidthQuota, QoSPolicy, ThrottleSchedule
│   │   └── settings.py              # GlobalSettings
│   ├── schemas/                     # Pydantic validation schemas
│   │   ├── user.py                  # UserCreate, UserUpdate, UserResponse
│   │   ├── device.py                # DeviceCreate, DeviceControl, etc.
│   │   ├── alert.py                 # AlertRuleCreate, AlertResponse
│   │   ├── bandwidth.py             # BandwidthStats, UsageData
│   │   └── response.py              # Generic API responses
│   ├── services/                    # Business logic layer
│   │   ├── network_monitor.py       # Scapy packet capture service
│   │   ├── network_scanner.py       # ARP scanning for device discovery
│   │   ├── bandwidth_controller.py  # iptables/tc integration
│   │   ├── alert_service.py         # Alert rule evaluation
│   │   ├── notification_handlers.py # Email/SMS/webhook handlers
│   │   ├── device_service.py        # Device business logic
│   │   ├── auth_service.py          # Authentication logic
│   │   ├── reporting_service.py     # Report generation & CSV export
│   │   ├── threshold_monitor.py     # Global threshold checks
│   │   ├── realtime_stats.py        # WebSocket stats aggregator
│   │   └── websocket_manager.py     # WebSocket connection manager
│   ├── repositories/                # Data access layer
│   │   ├── base.py                  # Generic repository with CRUD
│   │   ├── user_repository.py       # User data operations
│   │   ├── device_repository.py     # Device data operations
│   │   ├── alert_repository.py      # Alert data operations
│   │   ├── bandwidth_repository.py  # Bandwidth usage operations
│   │   └── advanced_controls_repository.py  # Quotas, QoS, schedules
│   └── utils/
│       ├── logging.py               # Structured logging setup
│       └── helpers.py               # Utility functions
│
├── dashboard-react/                  # Frontend application
│   ├── src/
│   │   ├── components/              # Reusable React components
│   │   │   ├── Layout.tsx          # Main layout with responsive sidebar
│   │   │   ├── Card.tsx            # Card container component
│   │   │   ├── StatCard.tsx        # Statistics display card
│   │   │   ├── Badge.tsx           # Status badge component
│   │   │   └── ...
│   │   ├── pages/                   # Page components
│   │   │   ├── Dashboard.tsx       # Main dashboard with charts
│   │   │   ├── Devices.tsx         # Device management page
│   │   │   ├── Alerts.tsx          # Alert configuration page
│   │   │   ├── AdvancedControls.tsx # Quotas, QoS, schedules
│   │   │   ├── Reports.tsx         # Usage reports page
│   │   │   ├── Users.tsx           # User management (admin only)
│   │   │   ├── Health.tsx          # System health page
│   │   │   ├── Login.tsx           # Login page
│   │   │   ├── Register.tsx        # Registration page
│   │   │   └── Auth.tsx            # Auth wrapper
│   │   ├── lib/
│   │   │   └── axios.ts            # Axios instance with interceptors
│   │   ├── App.tsx                 # Main app with routing
│   │   ├── App.css                 # Global styles + responsive
│   │   └── main.tsx                # React entry point
│   ├── public/                      # Static assets
│   ├── index.html                   # HTML template
│   ├── vite.config.ts               # Vite configuration
│   ├── tsconfig.json                # TypeScript config
│   ├── tailwind.config.js           # Tailwind CSS config
│   └── package.json                 # Frontend dependencies
│
├── tests/                            # Test suite (pytest)
│   ├── conftest.py                  # Test fixtures & config
│   ├── api/                         # API endpoint tests
│   │   ├── test_auth.py
│   │   ├── test_devices.py
│   │   ├── test_alerts.py
│   │   └── ...
│   ├── services/                    # Service layer tests
│   │   ├── test_network_monitor.py
│   │   ├── test_alert_service.py
│   │   └── ...
│   └── repositories/                # Repository tests
│       └── test_device_repository.py
│
├── alembic/                          # Database migrations
│   ├── versions/                    # Migration files
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_advanced_controls.py
│   │   ├── 003_bandwidth_threshold_fields.py
│   │   └── ...
│   ├── env.py                       # Alembic environment
│   └── alembic.ini                  # Alembic configuration
│
├── docs/                             # Documentation
│   ├── TECHNICAL_GUIDE.md           # Comprehensive dev docs
│   ├── PRESENTATION_SCRIPT.md       # 30-min presentation
│   ├── BANDWIDTH_THRESHOLD.md       # Threshold feature docs
│   ├── GLOBAL_THRESHOLD_IMPLEMENTATION.md
│   ├── SCAPY_INTEGRATION.md         # Network capture guide
│   └── RESPONSIVE_DESIGN_GUIDE.md   # UI/UX patterns
│
├── scripts/                          # Utility scripts
│   └── create_admin.py              # Admin user creation script
│
├── data/                             # Database & logs (gitignored)
│   ├── bandwidth_monitor.db         # SQLite database
│   └── logs/                        # Application logs
│
├── docker-compose.yml               # Development Docker setup
├── docker-compose.prod.yml          # Production Docker setup
├── Dockerfile                       # Backend container definition
├── nginx.conf.example               # Nginx reverse proxy config
├── systemd.service.example          # Systemd service template
├── pyproject.toml                   # Python dependencies (uv/pip)
├── uv.lock                          # Dependency lock file
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── README.md                        # This file
├── QUICKSTART.md                    # Quick start guide
└── DOCKER_SETUP_GUIDE.md            # Docker deployment guide
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (or Docker)
- **Linux OS** (for iptables/tc support)
- **Root/sudo privileges** (for packet capture)
- **Node.js 18+** (for frontend development)

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth.git
cd smart-bandwidth

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**Default Credentials:**

- Username: `admin`
- Password: `admin123` (change immediately!)

### Option 2: Manual Installation

```bash
# 1. Clone the repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth.git
cd smart-bandwidth

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -e .

# 4. Run database migrations
alembic upgrade head

# 5. Create admin user
python scripts/create_admin.py
# Follow prompts to create your admin account

# 6. Start backend (with sudo for network capture)
sudo .venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000

# 7. Install frontend dependencies (in new terminal)
cd dashboard-react
npm install

# 8. Start frontend
npm run dev
# Open http://localhost:5173 in your browser
```

### Configuration

Create a `.env` file in the project root:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/bandwidth_monitor.db

# Security (CHANGE THESE!)
SECRET_KEY=your-very-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Network Monitoring
NETWORK_INTERFACE=eth0  # Change to your network interface
PACKET_CAPTURE_FILTER=ip

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]
```

**Finding Your Network Interface:**

```bash
# Linux
ip addr show

# macOS
ifconfig
```

---

## 📸 Demo

### Dashboard Overview

Real-time bandwidth statistics with live WebSocket updates, device count, trend indicators, and protocol distribution charts.

**Key Metrics:**

- Total/Active devices • Total bandwidth • Average per device • WebSocket status (Live/Disconnected)

**Visualizations:**

- Real-time bandwidth line chart • Protocol pie chart • Device status breakdown • Network health

### Device Management

Comprehensive device table with inline controls and bulk operations.

**Features:**

- IP/MAC/Name display • Status badges • Bandwidth usage • Last seen • Quick actions
- Bulk operations: Select multiple, apply limits, block/unblock, export CSV

### Alert Configuration

Sophisticated alert rules with flexible conditions and auto-actions.

**Builder:**

- Metric selection • Condition operators • Threshold values • Time windows • Severity levels
- Notification channels (Email/SMS/Webhook) • Auto-actions (Throttle/Block)

### Advanced Controls

Fine-grained bandwidth management for power users.

**Features:**

- **Quotas**: Daily/weekly/monthly caps with auto-throttle
- **QoS**: Priority levels with bandwidth guarantees
- **Schedules**: Time-based limits with recurrence

### Responsive Design

Mobile-first UI adapting to all screen sizes (hamburger menu, collapsible sidebar, touch-optimized).

Seamless experience across all devices with hamburger menu navigation on mobile.

---

## 📚 Documentation

### User Guides

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[Docker Setup Guide](DOCKER_SETUP_GUIDE.md)** - Complete Docker deployment instructions

### Technical Documentation

- **[Technical Guide](docs/TECHNICAL_GUIDE.md)** - Comprehensive developer documentation
- **[API Reference](docs/TECHNICAL_GUIDE.md#api-reference)** - REST API endpoints
- **[Architecture](docs/TECHNICAL_GUIDE.md#architecture-overview)** - System design and patterns
- **[Database Schema](docs/TECHNICAL_GUIDE.md#database-schema)** - Data models and relationships

### Feature-Specific Guides

- **[Bandwidth Threshold Implementation](docs/BANDWIDTH_THRESHOLD.md)** - Threshold monitoring details
- **[Global Threshold Implementation](docs/GLOBAL_THRESHOLD_IMPLEMENTATION.md)** - Network-wide limits
- **[Scapy Integration](docs/SCAPY_INTEGRATION.md)** - Packet capture guide
- **[Responsive Design Guide](docs/RESPONSIVE_DESIGN_GUIDE.md)** - UI/UX patterns

### API Documentation

When the backend is running, access interactive API documentation:

- **Swagger UI**: <http://localhost:8000/docs> (Try API calls directly)
- **ReDoc**: <http://localhost:8000/redoc> (Clean, readable docs)

**Available API Endpoints:**

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Auth** | `/api/v1/auth/login` | POST | Login with username/password, get JWT token |
| | `/api/v1/auth/register` | POST | Register new user (admin only) |
| **Users** | `/api/v1/users` | GET | List all users (admin only) |
| | `/api/v1/users/{id}` | GET/PUT/DELETE | Get/update/delete user |
| **Devices** | `/api/v1/devices` | GET | List devices with pagination & filters |
| | `/api/v1/devices/{id}` | GET/PUT/DELETE | Get/update/delete device |
| | `/api/v1/devices/{id}/control` | PUT | Throttle/block/unblock device |
| | `/api/v1/devices/scan` | POST | Trigger network scan for new devices |
| **Alerts** | `/api/v1/alerts/rules` | GET/POST | List/create alert rules |
| | `/api/v1/alerts/rules/{id}` | GET/PUT/DELETE | Manage specific alert rule |
| | `/api/v1/alerts/history` | GET | Get alert history with filters |
| **Advanced Controls** | `/api/v1/advanced/quotas` | GET/POST | Bandwidth quotas management |
| | `/api/v1/advanced/qos` | GET/POST | QoS policies management |
| | `/api/v1/advanced/schedules` | GET/POST | Throttle schedules management |
| **Threshold** | `/api/v1/threshold` | GET/PUT | Global threshold settings |
| **Stats** | `/api/v1/stats/current` | GET | Current bandwidth statistics |
| | `/api/v1/stats/history` | GET | Historical bandwidth data |
| **Dashboard** | `/api/v1/dashboard/overview` | GET | Aggregated dashboard metrics |
| **Reports** | `/api/v1/reports/usage` | GET | Usage reports with date ranges |
| | `/api/v1/reports/top-consumers` | GET | Top bandwidth consumers |
| | `/api/v1/reports/export` | GET | Export report as CSV/JSON |
| **WebSocket** | `/api/v1/ws/stats` | WS | Real-time bandwidth stats stream |
| **Health** | `/api/v1/health` | GET | System health check |

All authenticated endpoints require `Authorization: Bearer <token>` header.

---

## 🧪 Testing

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/api/test_devices.py

# Run tests matching pattern
pytest -k "test_create"
```

### Test Coverage

Current coverage: **48%** (continuously improving)

```
Name                                 Stmts   Miss  Cover
--------------------------------------------------------
src/api/routes/alerts.py              145     75    48%
src/api/routes/devices.py             198     98    51%
src/services/network_monitor.py       312    156    50%
src/repositories/device_repository.py  87     25    71%
--------------------------------------------------------
TOTAL                                3847   2001    48%
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | Backend API bind address |
| `API_PORT` | `8000` | Backend API port |
| `DEBUG` | `false` | Enable debug logging |
| `DATABASE_URL` | `sqlite+aiosqlite:///./data/bandwidth_monitor.db` | Async database connection URL |
| `SECRET_KEY` | **Required** | JWT secret key (use strong random string) |
| `ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT token expiration time |
| `NETWORK_INTERFACE` | `eth0` | Network interface to monitor (eth0, wlan0, etc.) |
| `PACKET_CAPTURE_FILTER` | `ip` | BPF filter for packet capture |
| `MONITORING_INTERVAL` | `5.0` | Packet capture interval in seconds |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL (optional) |
| `CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins (JSON array) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_FILE` | `./logs/app.log` | Log file path |

### Application Settings (src/core/config.py)

```python
class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/bandwidth_monitor.db"
    
    # Security
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Network Monitoring
    NETWORK_INTERFACE: str = "eth0"
    PACKET_CAPTURE_FILTER: str = "ip"
    MONITORING_INTERVAL: float = 5.0
    
    # Optional Services
    REDIS_URL: str | None = None
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### Finding Your Network Interface

```bash
# Linux
ip addr show
# or
ifconfig

# Look for your active interface (e.g., eth0, wlan0, enp0s3)
```

### Advanced Configuration

Edit `src/core/config.py` for fine-tuning:

### Advanced Configuration

Edit `src/core/config.py` for fine-tuning:

- **Packet capture filters**: Custom BPF syntax for specific traffic
- **Alert notification channels**: Configure SMTP, SMS gateway, webhook URLs
- **Bandwidth control strategies**: Choose between iptables, tc, or custom
- **Session timeout settings**: Adjust JWT expiration and refresh logic
- **Rate limiting policies**: API rate limits per endpoint
- **Database connection pool**: SQLite pragma settings for performance
- **WebSocket heartbeat**: Ping/pong interval and timeout
- **Logging configuration**: File rotation, format, retention policy

---

## 🐳 Docker Deployment

### Development Mode

```bash
# Start all services (API, Dashboard, Redis)
docker-compose up -d

# View logs in real-time
docker-compose logs -f api
docker-compose logs -f dashboard

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build
```

### Production Mode

```bash
# Use production compose file with optimized settings
docker-compose -f docker-compose.prod.yml up -d

# Scale backend instances for load balancing
docker-compose -f docker-compose.prod.yml up -d --scale api=3

# Check container health
docker-compose -f docker-compose.prod.yml ps

# View resource usage
docker stats
```

### Docker Services

| Service | Port | Purpose | Health Check |
|---------|------|---------|--------------|
| `api` | 8000 | FastAPI backend | `/api/v1/health` |
| `dashboard` | 5173 (dev) / 80 (prod) | React frontend | HTTP 200 on `/` |
| `redis` | 6379 | Caching & sessions | Redis PING |

### Docker Environment

The containers use these environment variables (set in `.env`):

```env
# Docker-specific settings
COMPOSE_PROJECT_NAME=smart-bandwidth
DOCKER_BUILDKIT=1

# Service URLs (internal Docker network)
API_URL=http://api:8000
REDIS_URL=redis://redis:6379/0
```

### Dockerfile Highlights

**Backend (Dockerfile):**

- Multi-stage build for smaller image size
- Python 3.13 slim base image
- Non-root user for security
- Health check endpoint monitoring
- Volume mounts for data persistence

**Frontend:**

- Node 20 Alpine for minimal size
- Nginx for production serving
- Built artifacts only (no source code)
- Gzip compression enabled

---

## 🛠️ Development

### Setting Up Development Environment

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/smart-bandwidth.git
cd smart-bandwidth

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies with development tools
pip install -e ".[dev]"
# or using uv (faster)
uv sync --all-extras

# 4. Set up pre-commit hooks (optional but recommended)
pre-commit install

# 5. Initialize database
alembic upgrade head

# 6. Create admin user
python scripts/create_admin.py

# 7. Run backend with auto-reload (requires sudo for packet capture)
sudo .venv/bin/uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 8. In new terminal: Run frontend dev server
cd dashboard-react
npm install
npm run dev
```

### Development Tools

**Backend:**

```bash
# Run with hot reload
uvicorn src.main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Format code
black src/

# Lint code
ruff check src/ --fix

# Type check
mypy src/

# Run all quality checks
pre-commit run --all-files
```

**Frontend:**

```bash
# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint TypeScript
npm run lint
```

### Code Style & Standards

**Python (Backend):**

- **Formatter**: Black (line length: 88)
- **Linter**: Ruff (replaces flake8, isort, pyupgrade)
- **Type Checker**: mypy with strict mode
- **Docstrings**: Google style
- **Imports**: Sorted automatically by Ruff

**TypeScript (Frontend):**

- **Style**: ESLint with React rules
- **Formatter**: Prettier (via ESLint)
- **Naming**: camelCase for variables, PascalCase for components
- **Components**: Functional components with hooks

### Repository Pattern Usage

When working with database models, always use repositories:

```python
# ✅ CORRECT - Pass model instance to create/update/delete
from src.models.device import Device
from src.repositories.device_repository import DeviceRepository

device = Device(ip_address="192.168.1.1", mac_address="AA:BB:CC:DD:EE:FF")
device = await device_repo.create(device)

# ❌ WRONG - Don't pass dicts or IDs directly
device_dict = {"ip_address": "192.168.1.1"}
await device_repo.create(device_dict)  # Will fail!

# ✅ CORRECT - Use get_by_id() not get()
device = await device_repo.get_by_id(device_id)

# ❌ WRONG
device = await device_repo.get(device_id)  # Method doesn't exist!
```

### Adding New Features

1. **Create Database Model** (`src/models/`)
   - Define SQLAlchemy ORM model
   - Add relationships and constraints

2. **Create Pydantic Schema** (`src/schemas/`)
   - Input validation schemas (Create, Update)
   - Output response schemas

3. **Create Repository** (`src/repositories/`)
   - Inherit from `BaseRepository[ModelType]`
   - Add custom query methods if needed

4. **Create Service** (`src/services/`)
   - Implement business logic
   - Keep thin, delegate to repositories

5. **Create API Route** (`src/api/routes/`)
   - Define FastAPI endpoint
   - Use dependency injection for DB and auth

6. **Write Tests** (`tests/`)
   - API endpoint tests
   - Service layer tests
   - Repository tests (if custom queries)

7. **Create Database Migration**

   ```bash
   alembic revision --autogenerate -m "Add feature X"
   alembic upgrade head
   ```

8. **Update Frontend** (`dashboard-react/src/`)
   - Add API calls in `lib/axios.ts`
   - Create/update page components
   - Add navigation links

### Git Workflow

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "feat: add bandwidth quota feature"

# Keep branch updated
git fetch origin
git rebase origin/main

# Push to your fork
git push origin feature/your-feature-name

# Open Pull Request on GitHub
```

**Commit Message Format:**

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test additions/changes
- `chore:` Maintenance tasks

### Contributing Workflow

1. **Create a feature branch**: `git checkout -b feature/your-feature`
2. **Make changes and test**: `pytest` (backend), `npm run lint` (frontend)
3. **Commit with descriptive message**: Follow commit format above
4. **Push to your fork**: `git push origin feature/your-feature`
5. **Open a Pull Request** with clear description and test results

---

## 🤝 Contributing

We welcome contributions! Whether it's bug reports, feature requests, or pull requests, your input helps make Smart Bandwidth Monitor better for everyone.

### How to Contribute

1. **Report Bugs**: Open an issue with detailed reproduction steps
2. **Suggest Features**: Describe your idea and use case
3. **Fix Issues**: Pick an issue labeled `good first issue`
4. **Improve Docs**: Fix typos, add examples, clarify explanations
5. **Write Tests**: Increase code coverage

### Contribution Guidelines

- Follow the existing code style
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and descriptive
- Be respectful and constructive

### Areas for Contribution

- 📊 Additional chart types and visualizations
- 🔔 New notification channels (Slack, Discord, Telegram)
- 🌍 Internationalization (i18n) support
- 🧪 Increase test coverage
- 📱 Mobile app (React Native)
- 🐳 Kubernetes deployment manifests
- 📖 Tutorial videos and blog posts

---

## 🗺️ Roadmap

### Version 2.0 (Q1 2026)

- [ ] Machine learning for anomaly detection
- [ ] Advanced traffic shaping (QoS priorities)
- [ ] Multi-tenant support for ISPs
- [ ] GraphQL API option
- [ ] Elasticsearch integration for analytics

### Version 2.1 (Q2 2026)

- [ ] Mobile applications (iOS & Android)
- [ ] Kubernetes Helm charts
- [ ] Plugin system for extensibility
- [ ] AI-powered bandwidth optimization
- [ ] Advanced security features (DPI, IDS)

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - For the incredible async web framework
- **React Team** - For the powerful UI library
- **Scapy** - For robust packet manipulation
- **Tailwind CSS** - For beautiful, responsive designs
- **Open Source Community** - For inspiration and support

---

## 📞 Support & Contact

### Get Help

- **GitHub Issues**: [Report bugs or request features](https://github.com/Paul-Aransiola/smart-bandwidth/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/Paul-Aransiola/smart-bandwidth/discussions)

### Stay Updated

- **GitHub**: [@Paul-Aransiola](https://github.com/Paul-Aransiola)
- **Project Repository**: [smart-bandwidth](https://github.com/Paul-Aransiola/smart-bandwidth)

---

## 🌟 Star History

If you find this project useful, please consider giving it a ⭐ on GitHub!

---

<div align="center">

**Made with ❤️ by [Paul Aransiola](https://github.com/Paul-Aransiola)**

[⬆ Back to Top](#-smart-bandwidth-monitor--control-system)

</div>
