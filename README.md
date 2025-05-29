# 🤖 Agent Web Scraper

[![CI](https://github.com/IgorGanapolsky/agent-web-scraper/workflows/CI/badge.svg)](https://github.com/IgorGanapolsky/agent-web-scraper/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Checked with mypy](https://www.mypy.org/static/mypy_badge.svg)](https://mypy.org/)

> AI-powered market research agent for automated web scraping and analysis

## 🌟 Features

- **🎯 AI-Powered Analysis**: Uses GPT-4 to extract key insights and pain points from scraped content
- **📊 Multi-Source Scraping**: Reddit, Google Search, Twitter, and more
- **📈 Google Sheets Integration**: Automated logging and reporting
- **🔄 Processing Pipelines**: Summarization, trend analysis, and pain point extraction
- **📧 Automated Outreach**: Email digests and cold outreach capabilities
- **🏗️ Modern Architecture**: Built with 2025 best practices using Hatch, Ruff, and structured logging
- **📋 Visual Dashboard**: Real-time Kanban board tracking business outcomes

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/IgorGanapolsky/agent-web-scraper.git
   cd agent-web-scraper
   ```

2. **Set up the development environment:**
   ```bash
   python setup_dev.py
   ```

3. **Configure environment variables:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

4. **Run the application:**
   ```bash
   make dev
   ```

## 📋 Project Status

The project follows a Kanban methodology with clear stages:

### ✅ Completed
- Reddit Scraper
- Summarizer (GPT-4)
- Google Sheet Logs
- GitHub Actions Scheduler
- Secrets Management

### 🔄 In Progress
- Google Search integration
- Pain Point Extractor
- Email Digests
- Zoho SMTP Emailer
- Lead Generation

### 📝 Backlog
- Twitter Scraper
- Trend Analyzer
- Cold Outreach Emails
- CRM Integration
- Revenue Tracking

## 🛠️ Development

### Quick Commands

```bash
# Run all quality checks
make check

# Format code
make format

# Run tests with coverage
make test-cov

# Check application health
make health

# View project info
make info
```

### Using Hatch Directly

```bash
# Run tests
hatch run test

# Run linting
hatch run lint:all

# Format code
hatch run lint:fmt

# Activate shell
hatch shell
```

## 🏗️ Architecture

```
app/
├── cli/           # Command-line interface (Typer)
├── config/        # Configuration and settings (Pydantic)
├── core/          # Core business logic
├── observability/ # Logging, metrics, error tracking (Sentry)
├── utils/         # Utility functions
└── web/           # Web interface (Streamlit/FastAPI)
```

## 📊 Configuration

The application uses Pydantic Settings for configuration management:

```python
from app.config.settings import settings

# Access configuration
api_key = settings.openai_api_key
debug_mode = settings.debug
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERPAPI_KEY` | SerpAPI key for search | - |
| `OPENAI_API_KEY` | OpenAI API key | - |
| `SENTRY_DSN` | Sentry error tracking | - |
| `LOG_LEVEL` | Logging level | `INFO` |
| `ENVIRONMENT` | Environment name | `development` |

## 📈 Monitoring & Observability

### Structured Logging

The application uses structured logging with JSON output:

```python
from app.config.safe_logger import get_structured_logger

logger = get_structured_logger(__name__)
logger.info("Operation completed", duration_ms=123, success=True)
```

### Error Tracking

Sentry integration for production error tracking:

```bash
export SENTRY_DSN="your-sentry-dsn"
export ENVIRONMENT="production"
```

### Health Checks

```bash
# CLI health check
make health

# Programmatic health check
from app.observability import health_check
status = health_check()
```

## 🧪 Testing

```bash
# Run all tests
hatch run test

# Run with coverage
hatch run test-cov

# Run specific test file
hatch run test tests/test_scraper.py
```

## 📚 API Documentation

### Reddit Scraper

```python
from app.core.reddit_scraper import RedditScraper

scraper = RedditScraper("AI tools", max_results=10)
results = scraper.run()
```

### CLI Interface

```bash
# Get help
agent-scraper --help

# Check health
agent-scraper health

# Get project info
agent-scraper info
```

## 🚀 Deployment

### Using Docker (Coming Soon)

```bash
# Build image
docker build -t agent-web-scraper .

# Run container
docker run -p 8000:8000 agent-web-scraper
```

### Environment Setup

1. Set production environment variables
2. Configure Sentry for error tracking
3. Set up Google Sheets service account
4. Configure SMTP for email functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run quality checks: `make check`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

### Code Style

- We use [Black](https://black.readthedocs.io/) for code formatting
- [Ruff](https://beta.ruff.rs/) for linting
- [mypy](https://mypy.readthedocs.io/) for type checking
- Pre-commit hooks ensure code quality

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Hatch](https://hatch.pypa.io/) for modern Python project management
- [Ruff](https://beta.ruff.rs/) for fast Python linting
- [Structlog](https://www.structlog.org/) for structured logging
- [Typer](https://typer.tiangolo.com/) for CLI interface
- [Pydantic](https://pydantic.dev/) for data validation

## 📞 Support

- 📧 Email: your.email@example.com
- 🐛 Issues: [GitHub Issues](https://github.com/IgorGanapolsky/agent-web-scraper/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/IgorGanapolsky/agent-web-scraper/discussions)

---

Built with ❤️ for modern Python development and AI-powered automation.
