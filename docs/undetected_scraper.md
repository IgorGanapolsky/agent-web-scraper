# Undetected Scraper

The `undetected_scraper` is a powerful tool designed to handle websites with advanced bot detection mechanisms. It uses `undetected_chromedriver` to bypass anti-bot measures.

## Features

- **Bypasses Anti-Bot Detection**: Uses real Chrome browser with various techniques to avoid detection
- **Automatic Retry Logic**: Handles timeouts and temporary failures
- **Header Extraction**: Extracts structured header information from HTML
- **Error Handling**: Comprehensive error reporting and graceful fallbacks

## When to Use

- When standard HTTP requests are blocked by the target website
- For JavaScript-heavy websites that require rendering
- When working with sites that implement Cloudflare or similar protections

## Installation

1. Ensure you have Python 3.8+ installed
2. Install the required dependencies:

```bash
python3 -m pip install undetected-chromedriver selenium beautifulsoup4
```

## Usage

### Basic Usage

```python
from app.ui.undetected_scraper import UndetectedChromeScraper

# Initialize the scraper
scraper = UndetectedChromeScraper(headless=True)

try:
    # Scrape a URL
    result = scraper.scrape("https://example.com")
    
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Successfully retrieved {len(result['html'])} characters of HTML")
        
        # Extract headers
        headers = scraper.extract_headers(
            result["html"], 
            ["h1", "h2", "h3"], 
            "https://example.com"
        )
        
        # Process results
        for header in headers:
            print(f"{header['tag']}: {header['text']}")
            
finally:
    # Clean up
    scraper.quit()
```

### Configuration Options

The `UndetectedChromeScraper` class accepts the following parameters:

- `headless`: Run browser in headless mode (default: `True`)
- `timeout`: Page load timeout in seconds (default: `30`)

### Error Handling

The scraper includes comprehensive error handling for:
- Page load timeouts
- Network errors
- Browser initialization failures
- HTML parsing errors

All methods return a dictionary with an `error` key if an error occurs.

## Logging

The scraper uses the application's logging configuration. See the [Logging Configuration](#logging-configuration) section for details.

## Testing

Run the unit tests with:

```bash
python -m pytest tests/unit/test_undetected_scraper.py -v
```

## Logging Configuration

The application uses structured JSON logging with the following features:

- **Rotating Log Files**: Prevents log files from growing too large
- **Separate Error Logs**: Errors are logged to a dedicated file
- **Performance Logging**: Performance metrics are logged separately
- **Test URL Filtering**: Test URLs (like test.com) are automatically filtered out

### Log Files

- `logs/scraper/scraper.log`: Main application log
- `logs/scraper/errors/errors.log`: Error log
- `logs/scraper/performance/performance.log`: Performance metrics

## Cleanup

To clean up log files and remove test entries:

```bash
python scripts/cleanup_logs.py
```

This will:
1. Create a backup of the current log file
2. Remove entries containing test URLs
3. Save the cleaned log file

## Troubleshooting

### Common Issues

1. **ChromeDriver Version Mismatch**
   - Ensure you have the latest version of Chrome installed
   - The undetected-chromedriver should automatically download the correct ChromeDriver version

2. **Headless Mode Issues**
   - Some websites can detect headless browsers
   - Try running with `headless=False` for debugging

3. **Performance**
   - The scraper is slower than simple HTTP requests due to browser overhead
   - Consider using standard HTTP requests when possible

## License

[Your License Here]
