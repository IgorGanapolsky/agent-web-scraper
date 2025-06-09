# 🤖 Agent Web Scraper

**AI-powered web scraping and automation platform for market intelligence**

[![CI](https://github.com/IgorGanapolsky/agent-web-scraper/workflows/CI/badge.svg)](https://github.com/IgorGanapolsky/agent-web-scraper/actions)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_agent-web-scraper&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_agent-web-scraper)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_agent-web-scraper&metric=coverage)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_agent-web-scraper)
[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=IgorGanapolsky_agent-web-scraper&metric=security_rating)](https://sonarcloud.io/summary/new_code?id=IgorGanapolsky_agent-web-scraper)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Development](https://img.shields.io/badge/status-active%20development-blue.svg)](README.md)

## 🎯 What This Does

An experimental platform for automated web scraping and AI-powered content analysis using modern agent-based architectures.

- **Automated web scraping** with multiple data sources (Reddit, GitHub)
- **AI-powered content analysis** using Claude and other LLMs
- **Multi-agent coordination** for complex workflows
- **Revenue tracking experiments** with Stripe integration
- **Modern development stack** with FastAPI, Docker, and CI/CD

## 🏗️ Modern Architecture (2025)

Experimental architecture exploring agent-based automation:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Agents     │───▶│  Web Scrapers   │───▶│ Data Processing │
│ Claude/OpenAI   │    │ Reddit/GitHub   │    │ Content Analysis│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  FastAPI Web    │    │ Stripe API      │    │ Docker Deploy   │
│  Dashboard      │    │ Payments (exp)  │    │ CI/CD Pipeline  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Key Technologies

| Component | Technology | Purpose | Status |
|-----------|------------|---------|---------|
| **AI Models** | Claude Sonnet, OpenAI GPT | Content analysis and processing | ✅ **Active** |
| **Web Scraping** | Reddit API, GitHub API | Data collection from multiple sources | ✅ **Active** |
| **Backend API** | FastAPI | Web application and API endpoints | ✅ **Active** |
| **Payment System** | Stripe API | Payment processing (experimental) | 🧪 **Testing** |
| **Database** | ChromaDB, PostgreSQL | Data storage and vector search | 🚧 **Partial** |
| **Workflow Engine** | n8n | Business process automation | 🚧 **Development** |
| **CI/CD Pipeline** | GitHub Actions, Dagger.io | Automated testing and deployment | ✅ **Active** |
| **Container Platform** | Docker | Application containerization | ✅ **Active** |
| **Frontend** | Streamlit | Analytics dashboard | 🧪 **Experimental** |

## ⚡ Quick Start

### 1. Installation
```bash
git clone https://github.com/IgorGanapolsky/agent-web-scraper.git
cd agent-web-scraper
pip install -e .
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Required API keys
export OPENAI_API_KEY="sk-..."
export STRIPE_API_KEY="sk_test_..."
```

### 3. Run the Platform
```bash
# Start the FastAPI backend
python -m app.web.app

# Run market intelligence collection
python scripts/test_agentic_rag.py
```

## 🔬 Development Status

### Current Features
- **Web Scraping**: Reddit and GitHub data collection
- **AI Processing**: Claude integration for content analysis
- **API Backend**: FastAPI with authentication and endpoints
- **Payment Integration**: Stripe API integration (experimental)
- **Automation**: Workflow orchestration experiments

### Technical Metrics
- **Data Sources**: Reddit API, GitHub API, web scraping
- **AI Models**: Claude Sonnet, OpenAI GPT (configurable)
- **Response Time**: Varies by data source and processing complexity
- **Deployment**: Docker containers with CI/CD automation
- **Testing**: Unit and integration test coverage

## 🛠️ Development

### Project Structure
```
agent-web-scraper/
├── app/                    # Core application
│   ├── web/               # FastAPI backend
│   ├── services/          # Business logic
│   ├── core/              # AI & data processing
│   └── config/            # Configuration
├── scripts/               # Automation & workflows
├── docs/                  # Documentation
│   ├── strategy/          # Business strategy
│   └── operations/        # Operational guides
└── tests/                 # Test suite
```

### Testing
```bash
# Run all tests
pytest tests/

# Test coverage
pytest --cov=app tests/

# Integration tests
pytest tests/integration/
```

## 🔗 Documentation

- **[Architecture Overview](docs/agentic-rag-architecture.md)** - Technical deep dive
- **[Business Model](docs/business-model.md)** - Revenue strategy
- **[API Reference](docs/api-reference.md)** - FastAPI endpoints
- **[Deployment Guide](docs/deployment-guide.md)** - Production setup

## 🚀 Deployment

### Production Stack
- **Cloud**: AWS/GCP with auto-scaling
- **Database**: PostgreSQL + ChromaDB
- **Monitoring**: Sentry AI integration
- **CI/CD**: Dagger.io + GitHub Actions + automated testing

### Quick Deploy
```bash
# Run Dagger CI/CD pipeline
dagger call full-ci-pipeline

# Quick health check
dagger call quick-health-check

# Deploy to production
make deploy
```

## 💡 Key Features

- 🤖 **Multi-Agent System** - Experimental agent coordination
- ✅ **Web Scraping Engine** - Reddit, GitHub, and web data collection  
- 🧪 **AI Content Analysis** - Claude integration for data processing
- 🧪 **Payment Processing** - Stripe API integration (experimental)
- 🚧 **Workflow Automation** - n8n integration (in development)
- ✅ **Modern DevOps** - Docker, CI/CD with GitHub Actions
- 🧪 **Analytics Dashboard** - Streamlit-based interface (experimental)

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

---

**Experimental AI automation platform**
*Exploring the future of agent-based web intelligence.*
