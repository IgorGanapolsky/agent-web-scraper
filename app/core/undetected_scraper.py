"""
Undetected Chrome Scraper module.

This module provides the UndetectedChromeScraper class which uses
undetected_chromedriver to bypass anti-bot measures when scraping
websites.
"""
import os
import platform
import time
from typing import Any, List, Optional

import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from app.config.logging import get_logger

logger = get_logger(__name__)

# Set Chrome binary path based on OS
if platform.system() == "Darwin":  # macOS
    CHROME_BINARY_LOCATION = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
elif platform.system() == "Windows":
    CHROME_BINARY_LOCATION = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
else:  # Linux
    CHROME_BINARY_LOCATION = "/usr/bin/google-chrome"


class UndetectedChromeScraper:
    """A web scraper that uses undetected_chromedriver to bypass anti-bot measures"""

    def __init__(self, headless: bool = False, user_agent: Optional[str] = None):
        """
        Initialize the undetected Chrome scraper.

        Args:
            headless: Whether to run in headless mode
            user_agent: Custom user agent to use (optional)
        """
        self.headless = headless
        self.user_agent = user_agent
        self.driver = None
        self._setup_driver()

    def _setup_driver(self):
        """Set up the undetected Chrome WebDriver"""

        # Set Chrome binary location
        # This check can remain outside if CHROME_BINARY_LOCATION is static
        # and options.binary_location is set after options are created.

        try:
            options = uc.ChromeOptions()

            if self.headless:
                options.add_argument("--headless=new")

            if self.user_agent:
                options.add_argument(f"user-agent={self.user_agent}")

            # Add common options to avoid detection
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            if os.path.exists(CHROME_BINARY_LOCATION):
                options.binary_location = CHROME_BINARY_LOCATION

            self.driver = uc.Chrome(
                options=options,
                use_subprocess=True,
                driver_executable_path=ChromeDriverManager().install(),
            )

            # Execute CDP commands to help avoid detection
            self.driver.execute_cdp_cmd(
                "Network.setUserAgentOverride",
                {"userAgent": self.user_agent} if self.user_agent else {},
            )
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            logger.info("Undetected Chrome WebDriver initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize undetected Chrome: {str(e)}")
            raise

    def get_page(
        self, url: str, wait_for: Optional[str] = None, timeout: int = 30
    ) -> Optional[str]:
        """
        Get the page source after loading a URL.

        Args:
            url: URL to load
            wait_for: CSS selector to wait for (optional)
            timeout: Maximum time to wait in seconds

        Returns:
            str: Page source if successful, None otherwise
        """
        if not self.driver:
            try:
                self._setup_driver()
            except Exception as e:
                logger.error(f"Failed to setup driver in get_page: {str(e)}")
                return None  # Driver setup failed

        # Ensure driver was initialized
        if not self.driver:
            logger.error("Driver not initialized after setup attempt in get_page.")
            return None

        try:
            self.driver.get(url)

            if wait_for:
                WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, wait_for))
                )

            # Add a small delay to ensure all JavaScript has executed
            time.sleep(2)

            return self.driver.page_source

        except TimeoutException:
            logger.warning(f"Timed out waiting for element: {wait_for}")
            return self.driver.page_source if self.driver else None

        except Exception as e:
            logger.error(f"Error loading page {url}: {str(e)}")
            return None

    def find_elements(
        self, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
    ) -> list:
        """
        Find elements on the current page.

        Args:
            selector: CSS selector or other locator
            by: Locator strategy (default: By.CSS_SELECTOR)
            timeout: Maximum time to wait in seconds

        Returns:
            list: List of matching WebElements
        """
        if not self.driver:
            return []

        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, selector))
            )
            return self.driver.find_elements(by, selector)
        except Exception as e:
            logger.warning(f"Error finding elements {selector}: {str(e)}")
            return []

    def extract_text(
        self, selector: str, by: str = By.CSS_SELECTOR, timeout: int = 10
    ) -> List[str]:
        """
        Extract text content from elements matching the selector.

        Args:
            selector: CSS selector or other locator
            by: Locator strategy (default: By.CSS_SELECTOR)
            timeout: Maximum time to wait in seconds

        Returns:
            list: List of text contents
        """
        elements = self.find_elements(selector, by, timeout)
        return [elem.text.strip() for elem in elements if elem and elem.text.strip()]

    def extract_attributes(
        self,
        selector: str,
        attribute: str,
        by: str = By.CSS_SELECTOR,
        timeout: int = 10,
    ) -> List[str]:
        """
        Extract attribute values from elements matching the selector.

        Args:
            selector: CSS selector or other locator
            attribute: Name of the attribute to extract
            by: Locator strategy (default: By.CSS_SELECTOR)
            timeout: Maximum time to wait in seconds

        Returns:
            list: List of attribute values
        """
        elements = self.find_elements(selector, by, timeout)
        return [
            elem.get_attribute(attribute)
            for elem in elements
            if elem and elem.get_attribute(attribute)
        ]

    def execute_script(self, script: str, *args) -> Any:
        """
        Execute JavaScript in the browser context.

        Args:
            script: JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            The script's return value
        """
        if not self.driver:
            return None
        return self.driver.execute_script(script, *args)

    def close(self):
        """Close the browser and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
            finally:
                self.driver = None

    def quit(self):
        """Quit the WebDriver and close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Undetected Chrome WebDriver quit successfully")
            except Exception as e:
                logger.error(f"Error quitting WebDriver: {str(e)}")
            finally:
                self.driver = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure browser is closed"""
        self.close()


# Example usage
if __name__ == "__main__":
    # Initialize the scraper
    with UndetectedChromeScraper(headless=True) as scraper:
        # Get a page
        html = scraper.get_page("https://example.com", wait_for="body")
        if html:
            soup = BeautifulSoup(html, "html.parser")
            print(f"Page title: {soup.title.text if soup.title else 'No title'}")

            # Extract all links
            links = scraper.extract_attributes("a", "href")
            print(f"Found {len(links)} links on the page")
