import datetime
import logging
import os
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.parse import unquote, urlparse

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Add the project root to the Python path
project_root = str(Path(__file__).parent.parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Search API - fix import
from serpapi.google_search import GoogleSearch

# Constants
HTML_PARSER = "html.parser"
DEFAULT_TITLE = "No title found"
META_DESCRIPTION = "Meta Description"
STOP_SCRAPING_TEXT = "⏹️ Stop Scraping"
ALL_ATTEMPTS_FAILED_MSG = (
    "All attempts with BeautifulSoup failed, falling back to UndetectedChromeScraper"
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the observability module
from app.observability import log_exceptions


# Import the UndetectedChromeScraper with improved error handling
@log_exceptions
def get_undetected_scraper_class():
    """Get the UndetectedChromeScraper class with proper error handling"""
    try:
        # First try direct import (works when running as module)
        from app.core.undetected_scraper import UndetectedChromeScraper as Scraper

        logging.info(
            "Successfully imported UndetectedChromeScraper using absolute import"
        )
        return Scraper
    except ImportError:
        logging.warning("Absolute import failed, trying relative import", exc_info=True)
        try:
            # Fall back to relative import (works when running the script directly)
            from .undetected_scraper import UndetectedChromeScraper as Scraper

            logging.info(
                "Successfully imported UndetectedChromeScraper using relative import"
            )
            return Scraper
        except ImportError:
            logging.error(
                "Failed to import UndetectedChromeScraper. Make sure the module is in the correct location.",
                exc_info=True,
            )

            # Return a mock class to allow the app to start
            class MockUndetectedChromeScraper:
                def __init__(self, *args, **kwargs):
                    raise ImportError(
                        "Failed to import UndetectedChromeScraper. Check logs for details."
                    )

            return MockUndetectedChromeScraper


# Get the scraper class
UndetectedScraper = get_undetected_scraper_class()

# API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Constants
ALL_TAG_OPTIONS = ["h1", "h2", "h3", "h4", "h5", "h6", "title"]
DEFAULT_TAGS = ["h1", "h2", "h3", "title"]
DEFAULT_MAX_RESULTS = 10  # Maximum number of URLs to scrape
DEFAULT_EXAMPLES = [
    "best affiliate marketing coaching programs in 2025",
    "top SEO services for small business",
    "digital marketing agency near me",
    "online business strategy consultant",
]
debug_mode = False  # Set to True to see API responses

# Domains that are known to block scraping
FIRECRAWL_BLOCKLIST = [
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "tiktok.com",
    "pinterest.com",
    "reddit.com",
    "quora.com",
    "medium.com",
    "forbes.com",
    "nytimes.com",
    "wsj.com",
    "bloomberg.com",
    "cnbc.com",
    "businessinsider.com",
    "washingtonpost.com",
    "theguardian.com",
    "bbc.com",
    "cnn.com",
    "foxnews.com",
    "nbcnews.com",
    "cbsnews.com",
    "abcnews.go.com",
    "reuters.com",
    "apnews.com",
    "economist.com",
    "ft.com",
    "marketwatch.com",
    "investopedia.com",
    "seekingalpha.com",
]


def is_blocked_url(url):
    """Check if URL domain is in the blocklist."""
    try:
        domain = urlparse(url).netloc.lower()
        return any(bad in domain for bad in FIRECRAWL_BLOCKLIST)
    except Exception:
        return False


def _make_request_with_retry(url, headers, attempt, max_attempts):
    """Make an HTTP request with retry logic."""
    if attempt > 0:
        time.sleep(1)  # Add delay between retries

    logging.info(f"Making request to {url} (attempt {attempt + 1}/{max_attempts})")
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code in (403, 429) and attempt < max_attempts - 1:
        raise requests.exceptions.RequestException(
            f"Access denied ({response.status_code}), will retry with different user agent"
        )

    response.raise_for_status()
    return response


def _extract_headers_from_soup(soup, tags_to_analyze):
    """Extract headers and metadata from a BeautifulSoup object."""
    results = {}

    # Extract title
    if soup.title and soup.title.string:
        results["Title"] = soup.title.string.strip()
        logging.info(f"Found Title: {results['Title']}")
    else:
        results["Title"] = "No Title Found"
        logging.info(f"{DEFAULT_TITLE}")

    # Extract meta description if requested
    if META_DESCRIPTION in tags_to_analyze:
        meta_desc = soup.find("meta", attrs={"name": "description"}) or soup.find(
            "meta", attrs={"property": "og:description"}
        )
        if meta_desc and meta_desc.get("content"):
            results[META_DESCRIPTION] = meta_desc.get("content").strip()
            logging.info(
                f"Found {META_DESCRIPTION}: {results[META_DESCRIPTION][:50]}..."
            )
        else:
            results[META_DESCRIPTION] = f"No {META_DESCRIPTION} Found"
            logging.info("No meta description found")

    # Extract header tags (h1, h2, etc.)
    for tag_type in set(tags_to_analyze) - set(results.keys()):
        if tag_type.startswith("H") and len(tag_type) == 2:
            header_num = tag_type[1]
            headers_found = soup.find_all(f"h{header_num}")

            if headers_found:
                headers_text = [header.get_text().strip() for header in headers_found]
                results[tag_type] = " | ".join(headers_text)
                logging.info(f"Found {len(headers_text)} {tag_type} headers")
            else:
                results[tag_type] = f"No {tag_type} Found"
                logging.info(f"No {tag_type} headers found")

    return results


def extract_headers_with_soup(
    url, tags_to_analyze, retry_count=2, use_undetected_fallback=True
):
    """Extract HTML headers and metadata from a web page using BeautifulSoup.

    Args:
        url (str): The URL to scrape
        tags_to_analyze (list): List of HTML elements to extract (e.g., ['h1', 'h2', 'h3'])
        retry_count (int, optional): Number of retry attempts. Defaults to 2.
        use_undetected_fallback (bool, optional): Whether to try alternative methods if this one fails.
                                                Defaults to True.

    Returns:
        dict: Dictionary containing the extracted content by element type
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    ]

    for attempt in range(retry_count + 1):
        try:
            headers = {
                "User-Agent": user_agents[attempt % len(user_agents)],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }

            response = _make_request_with_retry(url, headers, attempt, retry_count + 1)
            soup = BeautifulSoup(response.text, "html.parser")
            return _extract_headers_from_soup(soup, tags_to_analyze)

        except requests.exceptions.RequestException as e:
            logging.warning(
                f"Request error in extract_headers_with_soup for {url}: {str(e)}"
            )
            if attempt == retry_count:  # Last attempt failed
                if use_undetected_fallback:
                    logging.info(ALL_ATTEMPTS_FAILED_MSG)
                    return extract_headers_with_undetected_chrome(url, tags_to_analyze)
                return {tag: f"Error: {str(e)[:100]}" for tag in tags_to_analyze}
        except Exception as e:
            logging.error(
                f"Unexpected error in extract_headers_with_soup for {url}: {str(e)}"
            )
            if attempt == retry_count:  # Last attempt failed
                if use_undetected_fallback:
                    logging.info(ALL_ATTEMPTS_FAILED_MSG)
                    return extract_headers_with_undetected_chrome(url, tags_to_analyze)
                return {tag: f"Error: {str(e)[:100]}" for tag in tags_to_analyze}

    # If we get here, all retries failed
    if use_undetected_fallback:
        logging.info(ALL_ATTEMPTS_FAILED_MSG)
        return extract_headers_with_undetected_chrome(url, tags_to_analyze)
    return {
        tag: "Error: Failed to fetch data after multiple attempts"
        for tag in tags_to_analyze
    }


def _parse_scraper_result(result):
    """Parse the result from the scraper into HTML content."""
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        if "error" in result:
            raise ValueError(f"Scraping failed: {result['error']}")
        if "html" not in result:
            raise ValueError("No HTML content in response")
        return result["html"]
    raise TypeError(f"Unexpected result type: {type(result)}")


def _extract_meta_description(soup):
    """Extract meta description from soup object."""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if not meta_desc or not meta_desc.get("content"):
        meta_desc = soup.find("meta", attrs={"property": "og:description"})
    return meta_desc.get("content", "") if meta_desc else ""


def _extract_headers_from_soup_undetected(
    soup: BeautifulSoup, tags_to_analyze: List[str]
) -> Dict[str, str]:
    """Extract headers from soup object for undetected chrome."""
    results: Dict[str, str] = {}

    # Extract title if requested
    if "Title" in tags_to_analyze and soup.title:
        results["Title"] = soup.title.get_text(strip=True)

    # Extract meta description if requested
    if META_DESCRIPTION in tags_to_analyze:
        meta_desc = _extract_meta_description(soup)
        if meta_desc:
            results[META_DESCRIPTION] = meta_desc

    # Extract other headers (h1, h2, etc.)
    for tag in (t for t in tags_to_analyze if t not in ("Title", META_DESCRIPTION)):
        elements = soup.find_all(tag.lower())
        if elements:
            results[tag] = " | ".join(
                e.get_text(strip=True) for e in elements if e.get_text(strip=True)
            )

    return results


@log_exceptions
def extract_headers_with_undetected_chrome(
    url: str, tags_to_analyze: List[str], max_retries: int = 3
) -> Dict[str, str]:
    """
    Use UndetectedChromeScraper to extract headers from a URL.
    This is used as a fallback when the standard BeautifulSoup approach fails.

    Args:
        url (str): The URL to scrape
        tags_to_analyze (list): List of HTML tags to extract (e.g., ['h1', 'h2', 'h3'])
        max_retries (int): Maximum number of retry attempts

    Returns:
        dict: Dictionary of headers by tag type
    """
    logging.info("Trying to extract headers from %s using advanced method", url)
    headless = os.environ.get("CHROME_HEADLESS", "true").lower() == "true"
    scraper = None

    for attempt in range(max_retries):
        try:
            # Initialize the scraper
            scraper = UndetectedScraper(headless=headless)

            # Scrape the URL with explicit timeout
            result = scraper.scrape(url=url, timeout=30)
            html_content = _parse_scraper_result(result)

            # Parse and extract content
            soup = BeautifulSoup(html_content, HTML_PARSER)
            results = _extract_headers_from_soup_undetected(soup, tags_to_analyze)

            logging.info(
                "Successfully extracted %d items with advanced method", len(results)
            )
            return results

        except Exception as e:
            attempt_num = attempt + 1
            logging.warning("Attempt %d failed with error: %s", attempt_num, str(e))
            if attempt_num >= max_retries:
                logging.error("All %d attempts failed for %s", max_retries, url)
                return {
                    tag: f"Error: Failed to fetch data after {max_retries} attempts"
                    for tag in tags_to_analyze
                }
            time.sleep(2**attempt_num)  # Exponential backoff

        finally:
            if scraper:
                try:
                    scraper.quit()
                    logging.info("Scraper closed successfully")
                except Exception as e:
                    logging.error("Error closing scraper: %s", str(e), exc_info=True)

    return {
        tag: "Error: Failed to fetch data after multiple attempts"
        for tag in tags_to_analyze
    }


def _create_error_result(url: str, max_retries: int, error: Optional[str] = None) -> dict:
    """Create an error result dictionary."""
    return {
        "Title": f"Error: Failed to fetch data after {max_retries} attempts",
        "URL": url,
        "Snippet": f"Error: {error or 'Unknown error'}",
        "Status": "Error",
    }


def _create_success_result(url: str, soup: BeautifulSoup) -> dict:
    """Create a success result dictionary from BeautifulSoup object."""
    # Get the page title
    title = soup.title.string if soup.title else DEFAULT_TITLE

    # Extract snippet - get the most relevant content
    paragraphs = soup.find_all("p")
    snippet = paragraphs[0].text if paragraphs else "No content found"

    # Clean up the text
    snippet = " ".join(snippet.split())
    if len(snippet) > 150:
        snippet = snippet[:147] + "..."

    return {
        "Title": title.strip() if title else DEFAULT_TITLE,
        "URL": url,
        "Snippet": snippet,
        "Status": "Success",
    }


def _make_http_request(url: str) -> Tuple[Optional[requests.Response], Optional[str]]:
    """Make an HTTP request and return response and error tuple."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, timeout=15, headers=headers)
        if response.status_code == 200:
            return response, None
        return None, f"HTTP Status: {response.status_code}"
    except Exception as e:
        return None, str(e)


def fetch_data(url: str, max_retries: int = 3) -> dict:
    """Fetch data from a URL with retry logic and better error handling.

    Args:
        url: The URL to fetch data from
        max_retries: Maximum number of retry attempts

    Returns:
        dict: Dictionary containing the fetched data or error information
    """
    last_error = None

    for retry in range(max_retries):
        response, error = _make_http_request(url)

        if error is None and response is not None:
            try:
                soup = BeautifulSoup(response.text, HTML_PARSER)
                return _create_success_result(url, soup)
            except Exception as e:
                error = str(e)
                logging.error(f"Error parsing response from {url}: {error}")

        # If we get here, there was an error
        last_error = error
        retry_num = retry + 1

        if error:
            log_msg = f"Failed to fetch {url}. {error}. Retry {retry_num}/{max_retries}"
            logging.warning(log_msg)

        if retry_num < max_retries:
            time.sleep(1)  # Add a small delay between retries

    # All retries failed
    return _create_error_result(url, max_retries, last_error)


def update_results():
    """Update the results display with current progress"""
    if "results_list" not in st.session_state:
        return

    # Create DataFrame from results
    df = pd.DataFrame(st.session_state["results_list"])

    # Ensure required columns exist
    required_cols = ["Title", "URL", "Snippet", "Status"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""

    # Store updated DataFrame
    st.session_state["results_df"] = df
    return df


def _process_search_results(search_term, num_results):
    """Helper function to process search results"""
    # Request more results than needed to ensure we get enough valid ones
    # The API sometimes returns fewer results than requested
    params = {
        "q": search_term,
        "api_key": SERPAPI_KEY,
        "num": num_results * 2,  # Request double the results
        "google_domain": "google.com",
        "gl": "us",  # Set location to US for more consistent results
        "hl": "en",  # Set language to English
    }
    search = GoogleSearch(params)
    return search.get_dict()


def _extract_urls(search_results, max_results=10):
    """Helper function to extract URLs from search results, limited to max_results"""
    urls = []
    if "organic_results" in search_results:
        for result in search_results["organic_results"]:
            if "link" in result and not is_blocked_url(result["link"]):
                urls.append(result["link"])
                # Stop when we reach the requested number of results
                if len(urls) >= max_results:
                    break
    return urls


def _process_single_url(
    url, progress, results, current_url_info=None, progress_details=None
):
    """Process a single URL and update progress with detailed information in main window"""
    try:
        # Update the current URL being processed in the main window
        if current_url_info:
            current_url_info.info(f"Currently scraping: **{url}**")

        # Fetch the data
        result = fetch_data(url)
        if result:
            results.append(result)
            # Show success message in the main window
            if progress_details:
                if result.get("Status", "").startswith("✅"):
                    progress_details.success(
                        f"Successfully scraped: {result.get('Title', 'Unknown')}"
                    )
                else:
                    progress_details.warning(
                        f"Issue with: {url} - {result.get('Status', 'Unknown')}"
                    )

        # Add a small delay to prevent overwhelming the server
        time.sleep(0.5)
    except Exception as e:
        error_msg = f"Error processing {url}: {str(e)}"
        st.error(error_msg)
        if progress_details:
            progress_details.error(error_msg)

        results.append(
            {
                "Title": f"Error: {str(e)[:50]}...",
                "URL": url,
                "Snippet": "Error occurred while scraping this page.",
                "Status": "❌ Error",
            }
        )
    # Update progress in session state
    st.session_state["progress"] = progress * 100


def _process_final_results(results):
    """Process and return final results as DataFrame"""
    if not results:
        return pd.DataFrame()

    df = pd.DataFrame(results)
    # Remove any empty columns and reorder
    df = df.dropna(axis=1, how="all")
    column_order = ["Title", "URL", "Snippet", "Status"]
    return df[[col for col in column_order if col in df.columns]]


def search_and_scrape():
    """Main function to perform search and scraping with progress updates"""
    if not st.session_state.get("search_term"):
        st.warning("Please enter a search term.")
        return

    # Check if we already have results for this search term
    if "results_df" in st.session_state and not st.session_state["results_df"].empty:
        return st.session_state["results_df"]

    # Set processing state
    st.session_state["is_processing"] = True
    st.session_state["should_stop"] = False

    try:
        with st.spinner("Searching and scraping..."):
            # Get search results
            search_results = _process_search_results(
                st.session_state["search_term"], st.session_state.get("num_results", 10)
            )

            if "error" in search_results:
                st.error(f"Error from search API: {search_results['error']}")
                st.session_state["is_processing"] = False
                return

            # Extract URLs from search results - limit to user's requested num_results
            user_requested_results = st.session_state.get("num_results", 10)
            urls = _extract_urls(search_results, max_results=user_requested_results)
            if not urls:
                st.warning("No valid URLs found in search results.")
                st.session_state["is_processing"] = False
                return

            # Process each URL
            total_results = len(urls)
            results = []

            # Create a detailed progress display in main window
            # Main area for detailed progress tracking
            main_container = st.container()
            with main_container:
                st.subheader("Scraping Progress")
                st.write(f"Searching for: **{st.session_state['search_term']}**")
                current_url_info = st.empty()
                progress_details = st.empty()

            # Create a progress bar and stop button container
            progress_col, stop_col = st.columns([4, 1])
            with progress_col:
                progress_bar = st.progress(
                    0, text=f"Scraping 0 of {total_results} pages..."
                )

            # Stop button handler
            if stop_col.button(STOP_SCRAPING_TEXT, key="stop_button"):
                st.session_state["should_stop"] = True
                st.session_state["is_processing"] = False
                st.rerun()

            for i, url in enumerate(urls, 1):
                # Check if user wants to stop
                if st.session_state.get("should_stop", False):
                    st.warning("Scraping was stopped by user.")
                    st.session_state["should_stop"] = False
                    break

                progress = i / total_results
                progress_bar.progress(
                    progress, text=f"Scraping {i} of {total_results} pages..."
                )
                # Pass the progress placeholders to show real-time updates in main window
                _process_single_url(
                    url, progress, results, current_url_info, progress_details
                )

            # Process and save final results
            if results:
                st.session_state["results_df"] = _process_final_results(results)

            # Cleanup
            progress_bar.empty()
            st.session_state["is_processing"] = False
            st.rerun()

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state["is_processing"] = False

        # Only try to generate Excel if we have results
        if (
            "results_df" in st.session_state
            and not st.session_state["results_df"].empty
        ):
            try:
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    st.session_state["results_df"].to_excel(
                        writer, sheet_name="Results", index=False
                    )
                buffer.seek(0)

                st.download_button(
                    label="📥 Download Results (Excel)",
                    data=buffer,
                    file_name=f"scraped_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            except Exception as excel_error:
                st.error(f"Failed to generate Excel file: {str(excel_error)}")


def show_export_options():
    """Show export options for the scraped data"""
    st.subheader("Export Options")

    # Excel export only - no CSV option as requested
    if "results_df" in st.session_state and not st.session_state["results_df"].empty:
        try:
            from datetime import datetime
            from io import BytesIO

            import pandas as pd

            # Create Excel file in memory
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                st.session_state["results_df"].to_excel(
                    writer, index=False, sheet_name="Scraped Data"
                )
                # Get the worksheet object to set column widths
                worksheet = writer.sheets["Scraped Data"]

                # Auto-fit columns
                for i, col in enumerate(st.session_state["results_df"].columns):
                    max_len = max(
                        st.session_state["results_df"][col]
                        .astype(str)
                        .apply(len)
                        .max(),
                        len(col),
                    )
                    worksheet.set_column(i, i, max_len + 2)

            # Provide Excel download button only (no CSV)
            st.download_button(
                label="📥 Download Results as Excel",
                data=buffer.getvalue(),
                file_name=f"scraped_results_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as excel_error:
            st.error(f"Failed to generate Excel file: {str(excel_error)}")


def initialize_session_state():
    if "search_suggestions" not in st.session_state:
        st.session_state["search_suggestions"] = [
            "best affiliate marketing coaching programs in 2025",
            "top SEO services for small business",
            "digital marketing agency near me",
            "online business strategy consultant",
        ]
    if "search_term" not in st.session_state:
        st.session_state["search_term"] = ""
    if "num_results" not in st.session_state:
        st.session_state["num_results"] = 10
    if "selected_headers" not in st.session_state:
        st.session_state["selected_headers"] = ["Title", "H1", "H2"]
    if "additional_headers" not in st.session_state:
        st.session_state["additional_headers"] = ""
    if "results_df" not in st.session_state:
        st.session_state["results_df"] = pd.DataFrame()
    if "is_processing" not in st.session_state:
        st.session_state["is_processing"] = False
    if "should_stop" not in st.session_state:
        st.session_state["should_stop"] = False


def main():
    st.set_page_config(
        page_title="Enhanced Web Scraper",
        page_icon="🔍",
        layout="wide",  # Use wide layout for better table visibility
        initial_sidebar_state="expanded",
    )

    # Initialize processing state if not set
    if "is_processing" not in st.session_state:
        st.session_state["is_processing"] = False

    # Apply custom CSS
    st.markdown(
        """
    <style>
        .main .block-container {padding-top: 2rem;}
        div[data-testid="stDecoration"] {background-image: linear-gradient(90deg, #4f8bf9, #a37bf7);}
        button {border-radius: 5px;}
        #search-scrape-button {width: 100%;}
        .block-container {
            max-width: 1200px;
            padding-top: 1rem;
            padding-bottom: 0;
        }
        h1, h2, h3 {
            color: #4f8bf9;
        }
        /* Hide duplicate summaries */
        .stMarkdown:nth-of-type(3) ul {
            display: none;
        }
        /* Debug styles */
        pre {
            background-color: #1e1e1e;
            color: #d4d4d4;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 10px;
            font-size: 0.8em;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    initialize_session_state()

    # Configure and lay out the sidebar
    with st.sidebar:
        st.image(
            "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
            width=150,
        )
        st.subheader("Web Scraper Parameters")

        # Modern 2025 UI/UX Pattern: Only show one set of controls based on app state
        # Add CSS to ensure a clean, modern appearance
        st.markdown(
            """
        <style>
        div[data-testid="InputInstructions"],
        .stTextInput div[data-testid="stInputLabel"] + div,
        .stTextInput div[data-testid="stFormSubmitContent"] {
            display: none !important;
        }
        </style>
        <script>
        // Disable browser autocomplete for all text inputs
        document.addEventListener('DOMContentLoaded', function() {
            const allInputs = document.querySelectorAll('input[type="text"]');
            allInputs.forEach(input => {
                input.setAttribute('autocomplete', 'off');
                input.setAttribute('autocorrect', 'off');
                input.setAttribute('autocapitalize', 'off');
                input.setAttribute('spellcheck', 'false');
            });
        });
        </script>
        """,
            unsafe_allow_html=True,
        )

        # STATE-BASED UI: Either show the form OR the scraping controls, never both
        if st.session_state.get("is_processing", False):
            # SCRAPING STATE: When scraping is running, only show progress UI and stop button
            st.info("Scraping in progress... Please wait.")
            # Call the search and scrape function
            search_and_scrape()

            # Only show the stop button (no other controls)
            if st.button(
                STOP_SCRAPING_TEXT,
                type="primary",
                use_container_width=True,
                key="stop_button",
            ):
                st.session_state.should_stop = True
                st.session_state.is_processing = False
                st.rerun()
        else:
            # FORM STATE: When not scraping, show the form with settings
            with st.form(key="search_form"):
                st.markdown(
                    "<h5 style='margin-top:0.5rem;'>Search term:</h5>",
                    unsafe_allow_html=True,
                )
                search_term = st.text_input(
                    "",
                    value=st.session_state.get("search_term", ""),
                    key="search_term_input",
                    help="Enter your search term and press Enter to search",
                    placeholder="Enter search term...",
                )
                st.session_state["search_term"] = search_term

                st.markdown(
                    "<h5 style='margin-top:1.5rem;'>Number of results to scrape:</h5>",
                    unsafe_allow_html=True,
                )
                num_results = st.number_input(
                    "",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.get("num_results", 10),
                    step=1,
                    help="Number of search results to process",
                )
                st.session_state["num_results"] = num_results

                st.markdown(
                    "<h5 style='margin-top:1.5rem;'>Headers to extract</h5>",
                    unsafe_allow_html=True,
                )
                col1, col2 = st.columns(2)
                headers_to_extract = []
                with col1:
                    if st.checkbox(
                        "Title",
                        value=(
                            "Title"
                            in st.session_state.get(
                                "selected_headers", ["Title", "H1", "H2"]
                            )
                        ),
                    ):
                        headers_to_extract.append("Title")
                    if st.checkbox(
                        "H1",
                        value=(
                            "H1"
                            in st.session_state.get(
                                "selected_headers", ["Title", "H1", "H2"]
                            )
                        ),
                    ):
                        headers_to_extract.append("H1")
                    if st.checkbox(
                        "H2",
                        value=(
                            "H2"
                            in st.session_state.get(
                                "selected_headers", ["Title", "H1", "H2"]
                            )
                        ),
                    ):
                        headers_to_extract.append("H2")
                    if st.checkbox(
                        "H3",
                        value=("H3" in st.session_state.get("selected_headers", [])),
                    ):
                        headers_to_extract.append("H3")
                with col2:
                    if st.checkbox(
                        "H4",
                        value=("H4" in st.session_state.get("selected_headers", [])),
                    ):
                        headers_to_extract.append("H4")
                    if st.checkbox(
                        "H5",
                        value=("H5" in st.session_state.get("selected_headers", [])),
                    ):
                        headers_to_extract.append("H5")
                    if st.checkbox(
                        "H6",
                        value=("H6" in st.session_state.get("selected_headers", [])),
                    ):
                        headers_to_extract.append("H6")
                    if st.checkbox(
                        META_DESCRIPTION,
                        value=(
                            META_DESCRIPTION
                            in st.session_state.get("selected_headers", [])
                        ),
                    ):
                        headers_to_extract.append(META_DESCRIPTION)
                st.session_state["selected_headers"] = headers_to_extract

                st.markdown(
                    "<h5 style='margin-top:1.5rem;'>Additional headers (comma separated):</h5>",
                    unsafe_allow_html=True,
                )
                st.session_state["additional_headers"] = st.text_input(
                    "",
                    value=st.session_state.get("additional_headers", ""),
                    key="additional_headers_input",
                )

                # Single primary action button - check if it was clicked
                submit_clicked = st.form_submit_button(
                    "🔍 Start Scraping", use_container_width=True, type="primary"
                )

                # If the submit button was clicked, update the session state to start processing
                if submit_clicked:
                    st.session_state.is_processing = True
                    st.session_state.should_stop = False
                    st.rerun()

            # Add JavaScript for better form handling
            st.markdown(
                """
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const form = document.querySelector('form[data-testid="stForm"]');
                if (form) {
                    form.addEventListener('submit', function(e) {
                        const isProcessing = %s;
                        if (isProcessing) {
                            e.preventDefault();
                            return false;
                        }
                        
                        // Disable all form inputs
                        const inputs = form.querySelectorAll('input, button, [role="button"]');
                        inputs.forEach(input => {
                            if (!input.closest('.stButton')) {  // Don't disable the stop button
                                input.disabled = true;
                                input.style.opacity = '0.7';
                                input.style.cursor = 'not-allowed';
                            }
                        });
                        
                        // Show loading state on button
                        const submitButton = form.querySelector('button[type="submit"]');
                        if (submitButton) {
                            submitButton.innerHTML = '⏳ Processing...';
                            submitButton.disabled = true;
                        }
                        
                        return true;
                    });
                }
            });
            </script>
            """
                % ("true" if st.session_state.get("is_processing", False) else "false"),
                unsafe_allow_html=True,
            )
            st.markdown("</div>", unsafe_allow_html=True)

    # Main content area
    st.title("Enhanced Web Scraper")
    st.markdown(
        """
    This app uses enhanced browser technology to extract headers from web pages.
    Enter a search term in the sidebar, select which headers you want to extract, and click '🔍 Start Scraping'.
    """
    )

    # Display results if available
    if "results_df" in st.session_state and not st.session_state["results_df"].empty:
        df = st.session_state["results_df"].copy()

        # Calculate summary counts from the DataFrame
        success_count = len(
            df[
                df["Status"].astype(str).str.contains("Success|✅")
                & ~df["Title"].astype(str).str.startswith("Error")
            ]
        )
        error_count = len(
            df[
                df["Status"].astype(str).str.contains("Error|❌")
                | df["Title"].astype(str).str.startswith("Error")
            ]
        )
        skipped_count = len(df[df["Status"].astype(str).str.contains("Skipped|⏩")])
        total_count = len(df)

        # Show summary
        st.success(
            f"""
        ### Summary
        - {success_count} pages scraped successfully
        - {error_count} pages had errors
        - {skipped_count} pages were skipped (blocked)
        - {total_count} total results
        """
        )

        # Export options
        show_export_options()

        # Add some spacing
        st.markdown("---")

        # Display results in a clean, modern table
        if not df.empty:
            st.markdown(
                """
            <style>
                /* Modern table styling */
                .stDataFrame {
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    font-size: 14px;
                }
                .stDataFrame th {
                    background-color: #f8f9fa !important;
                    font-weight: 600 !important;
                    padding: 12px !important;
                    position: sticky;
                    top: 0;
                    z-index: 1;
                }
                .stDataFrame td {
                    vertical-align: top !important;
                    padding: 12px !important;
                    line-height: 1.4 !important;
                }
                .stDataFrame tr:hover {
                    background-color: #f8f9fa !important;
                }
                .stDataFrame tr:nth-child(even) {
                    background-color: #fcfcfc;
                }
                /* Make URLs look like links */
                .stDataFrame a {
                    color: #1a73e8 !important;
                    text-decoration: none;
                    word-break: break-all;
                }
                .stDataFrame a:hover {
                    text-decoration: underline;
                }
                /* Status column styling */
                .stDataFrame td:last-child {
                    text-align: center;
                    font-weight: 500;
                }
                .stDataFrame .status-success {
                    color: #0a7a42;
                }
                .stDataFrame .status-error {
                    color: #d32f2f;
                }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Format the DataFrame for better display
            display_df = df.copy()
            display_df["Status"] = display_df["Status"].apply(
                lambda x: f'<span class="status-{"success" if "✅" in str(x) else "error"}">{x}</span>'
            )

            # Display the table
            st.markdown(
                display_df.to_html(escape=False, index=False), unsafe_allow_html=True
            )

            # No CSV download button as requested

    # Listen for "Enter" key in search input
    st.markdown(
        """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && doc.activeElement.id.endsWith('search_term')) {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const scrapeButton = buttons.find(button => button.innerText === 'Search and Scrape');
            if (scrapeButton) {
                scrapeButton.click();
            }
        }
    });
    </script>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        filename="scraper.log",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Load environment variables from .env file
    load_dotenv()

    # Start the Streamlit app
    main()
