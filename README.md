# Smart Bandwidth Monitor & Control API

A comprehensive backend system built with FastAPI that provides real-time network monitoring, bandwidth control, alerts, and user authentication for managing shared Wi-Fi networks.

## 🎯 Project Overview

This system provides a practical solution for shared Wi-Fi environments (hostels, cafés, small offices) where bandwidth management is crucial but enterprise-grade tools are too complex or expensive.

### Key Features

#### Core Features
- **Real-time Network Monitoring**: Track bandwidth usage per device (IP/MAC address)
- **WebSocket Support**: Live updates for bandwidth statistics and alerts
- **Device Management**: Identify and manage connected devices
- **Bandwidth Control**: Throttle or block high-usage devices
- **RESTful API**: Clean, well-documented endpoints for automation

#### Advanced Features
- **User Authentication**: JWT-based authentication with role-based access control (Admin/User)
- **Alert System**: Configurable rules for bandwidth thresholds with multi-channel notifications
- **Advanced Reporting**: Usage reports, trends, top consumers with CSV/JSON export
- **Optional Dashboard**: Web-based visualization of network usage
- **Database Migrations**: Alembic for schema versioning

#### Technical Features
- **Lightweight**: SQLite database with async support
- **Clean Architecture**: SOLID principles with repository pattern
- **Comprehensive Testing**: 44 tests with 48% coverage
- **Docker Ready**: Containerized deployment support

## 🏗️ Architecture

The project follows SOLID principles and clean architecture:

```
src/
├── api/
│   ├── routes/          # FastAPI endpoints (auth, devices, alerts, reports, etc.)
│   └── dependencies/    # Auth dependencies (JWT validation)
├── core/
│   ├── config.py        # Settings management
│   ├── database.py      # Database configuration
│   ├── security.py      # Password hashing & JWT tokens
│   └── exceptions.py    # Custom exceptions
├── models/              # SQLAlchemy models (User, Device, Alert, etc.)
├── schemas/             # Pydantic schemas for validation
├── services/            # Business logic layer
├── repositories/        # Data access layer
└── utils/              # Utilities (logging, config)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- pip or uv (Python package manager)
- Docker & Docker Compose (optional)
- Linux OS (for iptables/tc bandwidth control)

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/Paul-Aransiola/smart-bandwidth-monitor.git
cd smart-bandwidth-monitor
```

#### 2. Install Dependencies

```bash
# Using pip
pip install -e .

# Or using uv
uv sync
```

#### 3. Set Up Database

```bash
# Run database migrations
alembic upgrade head

# Create admin user
python scripts/create_admin.py
# Follow prompts to create your admin account
```

#### 4. Configure Environment (Optional)

Create a `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
DATABASE_URL=sqlite+aiosqlite:///./bandwidth_monitor.db

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-secret-key-here-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

#### 5. Run the Application

```bash
# Development mode
uvicorn src.main:app --reload

# Production mode
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Access the API:
- API: `http://localhost:8000`
- Interactive Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8000/dashboard.html`

### Installation with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run migrations and create admin user
docker-compose exec api alembic upgrade head
docker-compose exec api python scripts/create_admin.py
```

## 🔐 Authentication

The API uses JWT (JSON Web Tokens) for authentication.

### 1. Register a User (Admin Only)

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "securepassword123",
    "full_name": "John Doe"
  }'
```

### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "expires_in": 1800
  }
}
```

### 3. Use the Token

Include the token in the Authorization header:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## 📚 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user | Admin |
| POST | `/api/v1/auth/login` | Login and get token | No |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| PUT | `/api/v1/auth/me` | Update user profile | Yes |
| POST | `/api/v1/auth/change-password` | Change password | Yes |
| GET | `/api/v1/auth/users` | List all users | Admin |
| PUT | `/api/v1/auth/users/{id}/activate` | Activate user | Admin |
| PUT | `/api/v1/auth/users/{id}/deactivate` | Deactivate user | Admin |
| PUT | `/api/v1/auth/users/{id}/promote` | Promote to admin | Admin |

### Device Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/devices` | List all devices |
| POST | `/api/v1/devices/scan` | Trigger network scan |
| GET | `/api/v1/devices/{device_id}` | Get device details |
| PUT | `/api/v1/devices/{device_id}` | Update device info |
| DELETE | `/api/v1/devices/{device_id}` | Remove device |

### Bandwidth Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/control/block` | Block a device |
| POST | `/api/v1/control/unblock` | Unblock a device |
| POST | `/api/v1/control/throttle` | Limit bandwidth |
| POST | `/api/v1/control/unthrottle` | Remove limit |
| GET | `/api/v1/control/status/{ip}` | Get control status |

### Statistics & Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/stats/current` | Current bandwidth stats |
| GET | `/api/v1/stats/history` | Historical data |
| GET | `/api/v1/reports/usage` | Usage report |
| GET | `/api/v1/reports/trends` | Usage trends |
| GET | `/api/v1/reports/top-consumers` | Top bandwidth users |
| GET | `/api/v1/reports/export` | Export data (CSV/JSON) |

### Alert Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/alerts/rules` | Create alert rule |
| GET | `/api/v1/alerts/rules` | List alert rules |
| PUT | `/api/v1/alerts/rules/{id}` | Update rule |
| DELETE | `/api/v1/alerts/rules/{id}` | Delete rule |
| GET | `/api/v1/alerts/history` | Alert history |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/api/v1/alerts/{id}/resolve` | Resolve alert |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| WS `/ws` | Real-time bandwidth updates |

Example:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Bandwidth update:', data);
};
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_auth_service.py -v

# View coverage report
open htmlcov/index.html
```

Current test status:
- ✅ 44 tests passing
- 📊 48% code coverage
- 🎯 Target: 60%+ coverage

## 🛠️ Development

### Code Formatting

```bash
# Format code with black
black src/ tests/

# Sort imports
isort src/ tests/

# Lint with ruff
ruff check src/ tests/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

### Adding New Features

1. Create feature branch: `git checkout -b feature/feature-name`
2. Implement changes following the architecture
3. Add tests (aim for 80%+ coverage)
4. Update documentation
5. Submit pull request

## 📋 System Requirements

### Software
- **Python**: 3.11 or higher
- **Database**: SQLite (default) or PostgreSQL
- **OS**: Linux (for bandwidth control features)

### Python Libraries
- FastAPI, Uvicorn - Web framework
- SQLAlchemy, Alembic - ORM and migrations
- Pydantic - Data validation
- python-jose - JWT tokens
- passlib, bcrypt - Password hashing
- Scapy, psutil - Network monitoring
- aiohttp - Async HTTP client

### System Permissions
- Root/sudo access for:
  - Packet capture (Scapy)
  - iptables (blocking devices)
  - tc (traffic control)

## 🔒 Security Best Practices

### Production Deployment

1. **Change Default Credentials**
   ```bash
   # Don't use default admin/admin123 in production!
   python scripts/create_admin.py
   ```

2. **Set Strong Secret Key**
   ```env
   SECRET_KEY=$(openssl rand -hex 32)
   ```

3. **Enable HTTPS**
   - Use reverse proxy (nginx/traefik)
   - Configure SSL certificates

4. **Environment Variables**
   - Never commit `.env` files
   - Use secrets management in production

5. **Rate Limiting**
   - Configure rate limits for auth endpoints
   - Protect against brute force attacks

6. **CORS Configuration**
   ```env
   CORS_ORIGINS=["https://yourdomain.com"]
   ```

### Security Features

- ✅ Password hashing with bcrypt
- ✅ JWT token authentication
- ✅ Role-based access control (RBAC)
- ✅ Token expiration (30 minutes default)
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ Input validation (Pydantic)

## 🐳 Docker Deployment

### Production Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/bandwidth_monitor.db
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - api
    restart: unless-stopped
```

## 🔧 Troubleshooting

### Common Issues

1. **bcrypt compatibility error**
   ```bash
   pip install bcrypt==4.2.1
   ```

2. **Database locked errors**
   - Use connection pooling
   - Consider PostgreSQL for high concurrency

3. **Permission denied (packet capture)**
   ```bash
   sudo setcap cap_net_raw,cap_net_admin=eip $(which python)
   ```

4. **Token validation fails**
   - Check SECRET_KEY matches across restarts
   - Verify token hasn't expired

## 📊 Monitoring & Logs

Logs are stored in `logs/` directory:

```bash
# View application logs
tail -f logs/app.log

# View error logs
tail -f logs/error.log
```

## 🗺️ Roadmap

### Completed Features
- ✅ WebSocket real-time monitoring
- ✅ Advanced reporting and analytics
- ✅ Alert system with notifications
- ✅ User authentication & authorization
- ✅ Database migrations with Alembic

### Upcoming Features
- 🔄 Network topology visualization
- 🔄 Token refresh mechanism
- 🔄 Email notifications for alerts
- 🔄 Webhook integrations
- 🔄 PostgreSQL support
- 🔄 Docker production setup
- 🔄 Grafana dashboard integration

## 📄 License

MIT License - see LICENSE file for details

## 👥 Author

**Paul Aransiola**

- GitHub: [@Paul-Aransiola](https://github.com/Paul-Aransiola)
- Email: <paularansiola60@gmail.com>

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 🙏 Acknowledgments

This project addresses a real-world problem in environments with limited and expensive bandwidth, helping students and small businesses manage their networks fairly and efficiently.

---

**⭐ If you find this project useful, please consider giving it a star!**
