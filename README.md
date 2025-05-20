# Agent Web Scraper

A powerful web scraping application built with Python and Streamlit that allows you to search and scrape web content efficiently.

## Features

- 🔍 Search web content using SerpAPI
- 🌐 Scrape headers and metadata from web pages
- 📊 Present results in a structured format
- 📥 Export results to Excel
- 🚫 Built-in protection against anti-bot measures
- ⚡ Real-time progress updates

## Architecture

```
app/
├── config/              # Configuration files
│   ├── __init__.py
│   ├── logging.py      # Logging configuration
│   └── settings.py     # Application settings
├── core/               # Core functionality
│   ├── __init__.py
│   └── undetected_scraper.py  # Web scraping engine
├── utils/              # Utility functions
│   ├── __init__.py
│   └── env_utils.py    # Environment utilities
└── web/                # Web interface
    ├── __init__.py
    └── app.py          # Streamlit application
```

## Dependencies

- Python 3.9+
- beautifulsoup4: Web scraping
- requests: HTTP client
- python-dotenv: Environment management
- pydantic: Data validation
- streamlit: Web interface
- google-search-results: SerpAPI client
- pandas: Data processing

## Setup

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
python -m pip install -r requirements.txt
```

4. Create a `.env` file and add your SerpAPI key:
```
SERPAPI_KEY=your_serpapi_key_here
```

## Usage

1. Start the application:
```bash
streamlit run app/web/app.py
```

2. Enter a search term in the web interface
3. Configure advanced options if needed
4. Click "Search and Scrape" to begin
5. Monitor progress in real-time
6. Export results to Excel when complete

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see LICENSE file for details