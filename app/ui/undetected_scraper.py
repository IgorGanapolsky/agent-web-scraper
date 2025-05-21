import logging
import os
import time

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Configure logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class UndetectedChromeScraper:
    """A web scraper that uses undetected_chromedriver to bypass anti-bot measures"""

    def __init__(self, headless=True):
        """Initialize the Chrome scraper

        Args:
            headless (bool): Whether to run Chrome in headless mode
        """
        self.headless = headless
        self.driver = None
        self.is_initialized = False

    def initialize(self):
        """Initialize the Chrome driver

        Returns:
            bool: True if initialization successful, False otherwise
        """
        if not self.is_initialized:
            try:
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument("--headless")

                # Add additional options to better mimic real users
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--window-size=1920,1080")

                # Add user agent
                options.add_argument(
                    "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )

                # Initialize the undetected Chrome driver
                self.driver = uc.Chrome(options=options)
                self.is_initialized = True
                logging.info("Undetected Chrome driver initialized successfully")
                return True
            except Exception as e:
                logging.error(
                    f"Failed to initialize undetected Chrome driver: {str(e)}"
                )
                return False
        return True

    def scrape(self, url, timeout=30):
        """Scrape a URL using undetected Chrome

        Args:
            url (str): The URL to scrape
            timeout (int): Timeout in seconds

        Returns:
            dict: Result containing HTML content or error
        """
        if not self.is_initialized and not self.initialize():
            return {
                "html": "<html><body><p>Failed to initialize Chrome driver</p></body></html>",
                "error": "Chrome initialization failed",
            }

        try:
            logging.info(f"Navigating to {url} with undetected Chrome")
            self.driver.get(url)

            # Wait for the page to load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            # Add a small delay to allow JavaScript to execute
            time.sleep(2)

            # Get the page source
            html = self.driver.page_source

            return {"html": html}
        except TimeoutException:
            logging.error(f"Timeout while loading {url}")
            return {
                "html": "<html><body><p>Timeout while loading page</p></body></html>",
                "error": "Page load timeout",
            }
        except WebDriverException as e:
            logging.error(f"WebDriver error for {url}: {str(e)}")
            return {
                "html": "<html><body><p>WebDriver error</p></body></html>",
                "error": str(e),
            }
        except Exception as e:
            logging.error(f"Error scraping {url} with undetected Chrome: {str(e)}")
            return {
                "html": "<html><body><p>Error scraping page</p></body></html>",
                "error": str(e),
            }

    def extract_headers(self, html, tags_to_analyze, url):
        """Extract headers from HTML

        Args:
            html (str): HTML content
            tags_to_analyze (list): List of tags to extract (e.g. ["h1", "h2"])
            url (str): URL of the page (for reference)

        Returns:
            list: Extracted headers
        """
        headers = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            for tag in tags_to_analyze:
                for header in soup.find_all(tag):
                    header_text = header.get_text().strip()
                    if header_text:  # Only add non-empty headers
                        header_dict = {"url": url, "tag": tag, "text": header_text}
                        headers.append(header_dict)

            return headers
        except Exception as e:
            logging.error(f"Error extracting headers: {str(e)}")
            return []

    def quit(self):
        """Close the Chrome driver and release resources"""
        if self.is_initialized and self.driver:
            try:
                self.driver.quit()
                self.is_initialized = False
                logging.info("Undetected Chrome driver closed")
            except Exception as e:
                logging.error(f"Error closing Chrome driver: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Initialize the scraper
    scraper = UndetectedChromeScraper(headless=True)

    # Scrape a URL
    result = scraper.scrape("https://www.google.com")

    # Extract headers
    headers = scraper.extract_headers(
        result["html"], ["h1", "h2", "h3"], "https://www.google.com"
    )

    # Print results
    print(f"Found {len(headers)} headers")
    for header in headers:
        print(f"{header['tag']}: {header['text']}")

    # Close the scraper
    scraper.quit()
