# Enhanced Web Scraper

A powerful web application that scrapes Google search results and extracts headers from web pages, helping users analyze content structure across multiple websites.

## Architecture Overview

- **Frontend & Application Logic:**
  - **Streamlit**: Powers our interactive UI, providing a responsive dashboard interface that's easy to use and maintain.
  - Single-file application design for simplicity and easier deployment.

- **Web Scraping Stack:**
  - **SerpAPI**: Used to fetch Google search results without facing rate limiting or CAPTCHAs.
  - **BeautifulSoup**: Handles HTML parsing and header extraction with high accuracy and performance.

- **Data Processing:**
  - **Pandas**: Manages data manipulation, formatting, and export capabilities.
  - In-memory data storage and processing for lightweight operation.

## Technology Choices

### Why Streamlit?
- **Rapid Development**: Allows creation of data apps in hours instead of weeks
- **Python Native**: No frontend experience required, perfect for data scientists
- **Interactive Elements**: Built-in widgets for inputs, sliders, and visualizations
- **Deployment Simplicity**: Easy to deploy as a standalone app or within existing platforms

### Why BeautifulSoup?
- **HTML Parsing Specialist**: Optimized for extracting data from HTML documents
- **Low Overhead**: Lightweight library with minimal dependencies
- **Robust Error Handling**: Gracefully handles malformed HTML common on the web
- **Widely Supported**: Mature library with extensive documentation and community support

### Why SerpAPI for Search Results?
- **Google Search Results**: Reliable access to real Google search results
- **Avoids Blocks**: Prevents IP blocking that direct scraping would encounter
- **Structured Data**: Returns well-formatted JSON for easy processing

## How It Works

1. **User Input:**  
   The user enters a search term and selects which headers to extract (H1, H2, etc.) via the Streamlit interface.
   
2. **Search Process:**  
   - SerpAPI fetches the top Google search results for the query
   - Each URL is processed to extract the specified header tags
   
3. **Header Extraction:**  
   - BeautifulSoup parses the HTML content of each page
   - Headers are intelligently extracted, including title tags
   - Results are compiled into a structured dataset
   
4. **Results Display & Export:**  
   - Interactive data table shows all extracted headers
   - Export options for CSV and PDF formats
   - Clear success/error messages provide feedback on the process

## Environment Setup

1. Copy `.env.template` to `.env`:
   ```sh
   cp .env.template .env
   ```
2. Edit `.env` and fill in your actual API keys and secrets. **Never commit `.env` to source control!**

- `.env.template` provides example variable names and usage (e.g., `SERPAPI_KEY=your_serpapi_key_here`).

## Running Locally

```bash
pip install -r requirements.txt
streamlit run app/ui/enhanced_google_scraper.py
```

## Notes

- This application is for educational and research purposes only
- Respect website terms of service and implement appropriate rate limiting
- The application includes logging to help with debugging and troubleshooting
