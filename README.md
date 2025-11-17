# Smart Bandwidth Monitor & Control API

A lightweight backend system built with FastAPI that tracks internet usage per device and allows administrators to limit or block devices consuming excessive bandwidth.

## 🎯 Project Overview

This system provides a practical solution for shared Wi-Fi environments (hostels, cafés, small offices) where bandwidth management is crucial but enterprise-grade tools are too complex or expensive.

### Key Features

- **Real-time Network Monitoring**: Track bandwidth usage per device (IP/MAC address)
- **Device Management**: Identify and manage connected devices
- **Bandwidth Control**: Throttle or block high-usage devices
- **RESTful API**: Clean, well-documented endpoints for automation
- **Lightweight**: Runs on minimal resources with SQLite database
- **Optional Dashboard**: Web-based visualization of network usage

## 🏗️ Architecture

The project follows SOLID principles and clean architecture:

```
src/
├── api/           # FastAPI routes and endpoints
├── core/          # Core business logic and interfaces
├── models/        # Database models (SQLAlchemy)
├── services/      # Business services (monitoring, control)
├── repositories/  # Data access layer
└── utils/         # Utilities (logging, config)
```

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- uv (Python package manager)
- Docker & Docker Compose (optional)
- Linux OS (for iptables/tc support)

### Installation with uv

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/Paul-Aransiola/smart-bandwidth-monitor.git
cd smart-bandwidth-monitor

# Install dependencies
uv sync

# Run the application
uv run uvicorn src.main:app --reload
```

### Installation with Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access API at http://localhost:8000
# Access docs at http://localhost:8000/docs
```

## 📚 API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

- `GET /devices` - List all connected devices
- `GET /stats` - Get bandwidth statistics
- `POST /block/{ip}` - Block a device by IP
- `POST /unblock/{ip}` - Unblock a device
- `POST /throttle` - Limit device bandwidth

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## 🛠️ Development

```bash
# Run in development mode
uv run uvicorn src.main:app --reload --log-level debug

# Format code
uv run black src/
uv run isort src/

# Lint
uv run ruff check src/
```

## 📋 Requirements

- **Python Libraries**: FastAPI, Scapy, psutil, SQLAlchemy, uvicorn
- **System**: Linux with iptables/tc for bandwidth control
- **Permissions**: Root/sudo access for packet capture and traffic control

## 🔒 Security & Ethics

- Only use in controlled environments with proper authorization
- No personal data collection
- Designed for network administrators only
- Follow local laws and regulations

## 📄 License

MIT License - see LICENSE file for details

## 👥 Author

**Paul Aransiola**
- GitHub: [@Paul-Aransiola](https://github.com/Paul-Aransiola)
- Email: paularansiola60@gmail.com

## 🙏 Acknowledgments

This project addresses a real-world problem in African countries where bandwidth is limited and expensive, helping students and small businesses manage their networks fairly.
