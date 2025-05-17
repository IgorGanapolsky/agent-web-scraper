# Web Scraper with Undetected Chrome

A powerful web application that scrapes data from websites using undetected_chromedriver with Selenium, designed to avoid bot detection mechanisms.

## 🏗️ Architecture Overview

### Project Structure
```
agent-web-scraper/
├── run.py                  # Main entry point
├── app/
│   ├── __init__.py
│   ├── api/                # FastAPI application
│   │   └── app.py         # API routes and setup
│   ├── web/                # Streamlit web interface
│   │   └── app.py         # Streamlit application
│   ├── core/               # Core functionality
│   │   ├── scraper.py     # Base scraper implementation
│   │   └── undetected_scraper.py  # Undetected Chrome scraper
│   ├── ui/                 # UI components
│   ├── utils/              # Utility functions
│   └── config/             # Configuration
│       ├── __init__.py
│       ├── safe_logger.py  # Safe logging configuration
│       └── settings.py     # Application settings
├── tests/                  # Test suite
└── requirements.txt        # Project dependencies
```

### Core Components
- **Scraping Engine**: Web scraping with undetected_chromedriver and Selenium
- **Anti-Detection**: Advanced techniques to avoid bot detection
- **Web Interface**: Streamlit-based UI for interactive use
- **REST API**: FastAPI for programmatic access
- **Logging**: Safe logging configuration to prevent common issues

### Technology Stack
- **Python 3.11+**: Core programming language
- **FastAPI**: Modern, fast web framework for building APIs
- **Streamlit**: Rapid web app development
- **undetected_chromedriver**: For browser automation that avoids detection
- **Selenium**: Web browser automation
- **Pydantic**: Data validation and settings management
- **Pytest**: Testing framework

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Chrome browser installed
- ChromeDriver (will be installed automatically)
- Environment variables set in `.env` file (copy `.env.example` if needed)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/agent-web-scraper.git
   cd agent-web-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install ChromeDriver:
   ```bash
   python -m pip install webdriver-manager
   ```

5. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration if needed
   ```

### Usage

#### Web Interface
Start the Streamlit web interface:
```bash
python run.py web
```

#### API Server
Start the FastAPI server:
```bash
python run.py api
```

Then open your browser to:
- Web Interface: http://localhost:8501
- API Docs: http://localhost:8000/docs

## 🚀 Features

- **Google Search Scraping** - Extract headers and content from search results
- **Undetected Scraper** - Bypass bot detection with headless Chrome
- **SerpAPI Integration** - Fallback to official API when needed
- **Cost Tracking** - Monitor your SerpAPI usage and costs
- **Asynchronous processing** for improved performance
- **Configurable search parameters** to fine-tune your scraping
- **Robust error handling** with automatic retries

## 🔍 Observability

The application includes comprehensive observability features:

### Logging
- Structured JSON logging to both console and file
- Automatic log rotation and retention
- Environment-specific log levels
- Contextual logging with request/operation IDs

### Error Tracking
- Integration with Sentry for error tracking
- Automatic capture of exceptions and stack traces
- Environment-aware error reporting

### Metrics
- Function execution time tracking
- Success/failure rates for operations
- Custom metrics for business logic

To enable Sentry error tracking, add your Sentry DSN to the `.env` file:
```bash
SENTRY_DSN=your_sentry_dsn_here
```

## 🛠️ Development Setup

### Prerequisites
- Python 3.9+
- Poetry (recommended) or pip
- Playwright browsers

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/agent-web-scraper.git
   cd agent-web-scraper
   ```

2. **Set up Python environment**
   Using Poetry (recommended):
   ```bash
   poetry install
   poetry shell
   ```
   
   Or using pip:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install Playwright browsers**
   ```bash
   playwright install
   ```

4. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

### Development Workflow

1. **Run tests**
   ```bash
   pytest
   ```

2. **Run linters**
   ```bash
   black .
   isort .
   flake8
   mypy .
   ```

3. **Run the CLI**
   ```bash
   python -m app.cli.main --help
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

### Code Style
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints
- Keep functions small and focused
- Write docstrings for public APIs

## 🧪 Testing

### Current Test Coverage

Our current test coverage is lower than desired. We're actively working to improve it to reach our goal of 80% coverage. Current coverage is around 24%.

### Running Tests

Run the full test suite with coverage report:
```bash
pytest --cov=app --cov-report=term-missing
```

### Running Specific Tests

Run a specific test file:
```bash
pytest tests/unit/test_scraper.py -v
```

Run tests with HTML coverage report:
```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report in browser
```

### Improving Test Coverage

We need to add more tests for:
- Core scraping functionality
- Error handling
- Edge cases
- Integration tests for the web interface and API

### SonarQube Integration

SonarQube is configured to enforce 80% test coverage. The current configuration can be found in `sonar-project.properties`.

## 📚 Documentation

### Architecture Decision Records (ADRs)

We use Architecture Decision Records (ADRs) to document important architectural decisions made throughout the project.

1. [0001-use-undetected-chromedriver.md](docs/adr/0001-use-undetected-chromedriver.md) - Decision to use undetected_chromedriver with Selenium for web scraping

Key decisions:
- Using undetected_chromedriver to avoid bot detection
- Selenium for browser automation
- Streamlit for the web interface
- FastAPI for the REST API

To create a new ADR:
```bash
python scripts/new_adr.py "Title of the decision"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
