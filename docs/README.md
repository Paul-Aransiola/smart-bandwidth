# Smart Bandwidth Monitor & Control API - Project Documentation

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Requirements](#system-requirements)
3. [Installation Guide](#installation-guide)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Development Guide](#development-guide)
7. [Testing](#testing)
8. [Deployment](#deployment)
9. [Troubleshooting](#troubleshooting)

## Architecture Overview

The project follows clean architecture principles with clear separation of concerns:

```
src/
├── api/              # FastAPI routes and endpoints
│   ├── routes/       # API route handlers
│   └── dependencies/ # Dependency injection
├── core/             # Core business logic
│   ├── config.py     # Configuration management
│   ├── database.py   # Database setup
│   └── exceptions.py # Custom exceptions
├── models/           # SQLAlchemy database models
├── repositories/     # Data access layer (Repository pattern)
├── schemas/          # Pydantic schemas for validation
├── services/         # Business logic services
└── utils/            # Utility functions
```

### Key Design Patterns

- **Repository Pattern**: Abstracts data access logic
- **Dependency Injection**: FastAPI's built-in DI for loose coupling
- **Factory Pattern**: For creating service instances
- **Singleton Pattern**: Configuration management
- **Strategy Pattern**: For different bandwidth control strategies

## System Requirements

### Software Requirements

- Python 3.11 or higher
- Linux OS (for iptables/tc support)
- Root/sudo privileges for packet capture
- Docker & Docker Compose (optional)

### Python Dependencies

See `pyproject.toml` for full list. Key dependencies:

- FastAPI 0.115.0+
- SQLAlchemy 2.0.35+
- Scapy 2.5.0+
- psutil 6.1.0+
- uvicorn 0.32.0+

## Installation Guide

### Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth-monitor.git
cd smart-bandwidth-monitor

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env

# Edit .env with your configuration
nano .env

# Run application
sudo uv run python src/main.py
```

### Using Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f
```

## Configuration

All configuration is managed through environment variables defined in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# Network Monitoring
NETWORK_INTERFACE=eth0  # Change to your interface
MONITOR_INTERVAL=5
PACKET_CAPTURE_TIMEOUT=10

# Bandwidth Control
MAX_BANDWIDTH_MBPS=100
DEFAULT_THROTTLE_MBPS=10
ENABLE_BLOCKING=true
ENABLE_THROTTLING=true
```

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### Health Check

```http
GET /api/v1/health
```

Returns API health status.

#### List Devices

```http
GET /api/v1/devices?skip=0&limit=100
```

Returns list of all monitored devices.

#### Get Device Statistics

```http
GET /api/v1/stats
```

Returns overall network statistics.

#### Block Device

```http
POST /api/v1/control/block/{ip_address}
{
  "reason": "Excessive bandwidth usage"
}
```

### Full API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## Development Guide

### Setting Up Development Environment

```bash
# Install development dependencies
uv sync --all-extras

# Install pre-commit hooks
pre-commit install

# Run linters
uv run black src/
uv run isort src/
uv run ruff check src/
```

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all public functions/classes
- Maximum line length: 100 characters

### Adding New Features

1. Create feature branch: `git checkout -b feature/your-feature`
2. Implement with tests
3. Run tests: `uv run pytest`
4. Commit changes
5. Push and create PR

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_device_repository.py

# Run with verbose output
uv run pytest -v
```

## Deployment

### Production Deployment

1. Set `ENV=production` in `.env`
2. Generate secure `SECRET_KEY`
3. Configure firewall rules
4. Set up SSL/TLS with nginx
5. Use process manager (systemd, supervisor)
6. Configure log rotation
7. Set up monitoring

### Systemd Service

Create `/etc/systemd/system/bandwidth-monitor.service`:

```ini
[Unit]
Description=Smart Bandwidth Monitor API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/bandwidth-monitor
ExecStart=/usr/local/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Common Issues

#### Permission Denied for Packet Capture

**Solution**: Run with sudo or configure capabilities:

```bash
sudo setcap cap_net_raw,cap_net_admin=eip $(which python)
```

#### iptables Rules Not Applied

**Solution**: Ensure you have root privileges and iptables is installed:

```bash
sudo iptables -L -n -v
```

#### Database Locked Error

**Solution**: Use connection pooling or switch to PostgreSQL for production.

### Logging

Logs are stored in `logs/app.log`. Check logs for detailed error information:

```bash
tail -f logs/app.log
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

## License

MIT License - See LICENSE file

## Author

Paul Aransiola (<paularansiola60@gmail.com>)
