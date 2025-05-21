import logging
import os
import urllib.parse
from io import BytesIO

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from serpapi import GoogleSearch

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename="scraper.log",
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    # Use append mode by default, but we'll clear it when running search_and_scrape
    filemode="a",
)

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

# Define constants for UI elements
GOOGLE_LOGO_URL = (
    "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
)


def is_blocked_url(url):
    """Check if URL domain is in the blocklist."""
    try:
        domain = urllib.parse.urlparse(url).netloc.lower()
        return any(bad in domain for bad in FIRECRAWL_BLOCKLIST)
    except Exception:
        return False


def extract_headers_with_soup(url, tags_to_analyze):
    """
    Fallback scraper using BeautifulSoup for simple sites
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    try:
        logging.info(f"Using BeautifulSoup fallback scraper for {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        logging.info(f"Successfully fetched content from {url}")
        soup = BeautifulSoup(response.text, "html.parser")

        results = {}

        # Always grab the page title
        if soup.title and soup.title.string:
            results["Title"] = soup.title.string.strip()
            logging.info(f"Found Title: {results['Title']}")
        else:
            results["Title"] = "No Title Found"
            logging.info("No title found")

        # Find meta description if requested
        if "Meta Description" in tags_to_analyze:
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc and meta_desc.get("content"):
                results["Meta Description"] = meta_desc.get("content").strip()
                logging.info(
                    f"Found Meta Description: {results['Meta Description'][:50]}..."
                )
            else:
                results["Meta Description"] = "No Meta Description Found"
                logging.info("No meta description found")

        # Extract headers based on requested tag types
        for tag_type in tags_to_analyze:
            if tag_type not in results:  # Skip if already handled
                if tag_type.startswith("H") and len(tag_type) == 2:
                    # For H1, H2, H3, etc.
                    header_num = tag_type[1]
                    headers_found = soup.find_all(f"h{header_num}")

                    if headers_found:
                        headers_text = [
                            header.get_text().strip() for header in headers_found
                        ]
                        results[tag_type] = headers_text
                        logging.info(f"Found {len(headers_text)} {tag_type} headers")
                    else:
                        results[tag_type] = [f"No {tag_type} Found"]
                        logging.info(f"No {tag_type} headers found")
                else:
                    # For custom headers like 'affiliate', 'coaching', etc.
                    # Look for the word in the page content
                    body_text = soup.get_text().lower()
                    if tag_type.lower() in body_text:
                        # Count occurrences
                        count = body_text.count(tag_type.lower())
                        results[tag_type] = [f"Found {count} occurrences"]
                        logging.info(f"Found {count} occurrences of '{tag_type}'")
                    else:
                        results[tag_type] = [f"No occurrences of '{tag_type}' found"]
                        logging.info(f"No occurrences of '{tag_type}' found")

        logging.info(f"BeautifulSoup extraction completed for {url}")
        return results

    except requests.RequestException as e:
        logging.error(f"Request error in extract_headers_with_soup for {url}: {str(e)}")
        return {tag: [f"Error: {str(e)}"] for tag in tags_to_analyze}

    except Exception as e:
        logging.error(
            f"Unexpected error in extract_headers_with_soup for {url}: {str(e)}"
        )
        return {tag: [f"Error: {str(e)}"] for tag in tags_to_analyze}


def search_and_scrape():
    """Perform a search and scrape the results"""
    if not st.session_state["search_term"]:
        st.error("Please enter a search term")
        return

    # Initialize variables to track the results
    all_headers = []
    scrape_status = {}

    # Clear the scraper.log file
    try:
        with open("scraper.log", "w") as f:
            search_val = st.session_state["search_term"]
            f.write(f"Starting new scraping session for: {search_val}\n")
        logging.info(f"Starting new scraping session for: {search_val}")
    except Exception as e:
        logging.error(f"Failed to clear log file: {str(e)}")

    # Create a placeholder for status messages
    status_container = st.empty()

    try:
        # Get the selected headers to extract
        selected_headers = list(
            st.session_state["selected_headers"]
        )  # Convert set to list if needed

        # Add any additional headers
        if st.session_state["additional_headers"]:
            additional = [
                h.strip() for h in st.session_state["additional_headers"].split(",")
            ]
            selected_headers.extend(additional)

        logging.info(f"Selected headers: {selected_headers}")

        # Configure search parameters
        search_params = {
            "q": st.session_state["search_term"],
            "api_key": os.getenv("SERPAPI_KEY"),
            "num": st.session_state["num_results"] + 5,
            # Request more results to ensure we get at least the number requested
            "gl": "us",
        }

        status_container.info("Searching Google for results...")

        try:
            # Perform the search
            search = GoogleSearch(search_params)
            results = search.get_dict()

            # Extract organic results
            if "organic_results" in results and results["organic_results"]:
                urls_to_scrape = [
                    result["link"]
                    for result in results["organic_results"]
                    if "link" in result
                ]

                # Make sure we get the number requested by the user
                if len(urls_to_scrape) < st.session_state["num_results"]:
                    num_found = len(urls_to_scrape)
                    num_requested = st.session_state["num_results"]
                    logging.warning(
                        f"Only found {num_found} results, "
                        f"but {num_requested} were requested"
                    )

                # Limit to the number requested (or get all available if fewer)
                urls_to_scrape = urls_to_scrape[: st.session_state["num_results"]]

                num_urls = len(urls_to_scrape)
                status_container.info(
                    f"Found {num_urls} URLs to scrape. Starting scraping process..."
                )
                logging.info(f"URLs to scrape: {urls_to_scrape}")
            else:
                status_container.warning(
                    "No search results found. Please try a different search term."
                )
                return
        except Exception as e:
            status_container.error(f"Error performing search: {str(e)}")
            logging.error(f"Search error: {str(e)}")
            return

        # Process each URL
        for i, url in enumerate(urls_to_scrape):
            status_container.info(f"Scraping URL {i + 1}/{len(urls_to_scrape)}: {url}")
            logging.info(f"Scraping URL: {url}")

            try:
                # Check if the URL is in a blocklist
                if is_blocked_url(url):
                    logging.warning(f"Skipping blocked URL: {url}")
                    error_dict = {"URL": url}
                    for header_type in selected_headers:
                        error_dict[header_type] = "Blocked URL"
                    all_headers.append(error_dict)
                    scrape_status[url] = False
                    continue

                # Initialize an empty dictionary for this URL's headers
                headers_dict = {"URL": url}

                # Use BeautifulSoup for all scraping
                logging.info(f"Using BeautifulSoup scraper for {url}")
                extracted_data = extract_headers_with_soup(url, selected_headers)

                # Process the extracted data
                if extracted_data:
                    for header_type, values in extracted_data.items():
                        if isinstance(values, list):
                            headers_dict[header_type] = " | ".join(values)
                        else:
                            headers_dict[header_type] = values

                # Make sure we have a value for each selected header
                for header_type in selected_headers:
                    if header_type not in headers_dict:
                        headers_dict[header_type] = f"No {header_type} found"

                # Add to collection of all headers
                all_headers.append(headers_dict)
                scrape_status[url] = True

            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                # Add error entry
                error_dict = {"URL": url}
                for header_type in selected_headers:
                    error_dict[header_type] = f"Error: {str(e)}"
                all_headers.append(error_dict)
                scrape_status[url] = False

        # Convert results to dataframe
        if all_headers:
            # Create a 1-indexed DataFrame by setting custom index that starts at 1
            final_df = pd.DataFrame(all_headers, index=range(1, len(all_headers) + 1))

            # Put URL column first if it exists
            if "URL" in final_df.columns:
                cols = ["URL"] + [col for col in final_df.columns if col != "URL"]
                final_df = final_df[cols]

            st.session_state["results_df"] = final_df

            # Count successful scrapes
            successful = sum(1 for status in scrape_status.values() if status)
            failed = sum(1 for status in scrape_status.values() if not status)

            status_message = f"Completed scraping {len(scrape_status)} URLs. "
            if failed > 0:
                status_message += f"Successfully scraped {successful} URLs, "
                status_message += f"failed to scrape {failed} URLs."
            else:
                status_message += "All URLs were successfully scraped."

            status_container.success(status_message)
        else:
            status_container.error("Failed to extract any data from the URLs")

    except Exception as e:
        logging.error(f"Unexpected error in search_and_scrape: {str(e)}")
        status_container.error(f"An unexpected error occurred: {str(e)}")


def initialize_session_state():
    """Initialize the session state variables if they don't exist"""
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


def handle_enter_key():
    if st.session_state.search_term_input:
        # Trigger the search and scrape when Enter is pressed with a value
        search_and_scrape()


def main():
    st.set_page_config(
        page_title="Enhanced Web Scraper",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Force sidebar expansion using custom CSS
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"][aria-expanded="false"] {
            width: 500px !important;
        }
        [data-testid="stSidebar"][aria-expanded="true"] {
            width: 500px !important;
        }
        .stTextInput input {
            min-height: 50px;
        }
        .css-1l269bu {
            max-width: 500px !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    initialize_session_state()

    # Configure and lay out the sidebar
    with st.sidebar:
        st.image(
            GOOGLE_LOGO_URL,
            width=150,
        )
        st.subheader("Web Scraper Parameters")

        # Get the search term
        search_term = st.text_input(
            "Enter search term:",
            value=st.session_state.get("search_term", ""),
            key="search_term_input",
            on_change=handle_enter_key,
        )
        st.session_state["search_term"] = search_term

        st.session_state["num_results"] = st.slider(
            "Number of results to scrape:",
            min_value=1,
            max_value=50,
            value=st.session_state.get("num_results", 10),
        )

        st.subheader("Headers to extract")

        # Create individual checkboxes for headers for better control
        col1, col2 = st.columns(2)

        headers_to_extract = []
        with col1:
            if st.checkbox(
                "Title",
                value=(
                    "Title"
                    in st.session_state.get("selected_headers", ["Title", "H1", "H2"])
                ),
            ):
                headers_to_extract.append("Title")
            if st.checkbox(
                "H1",
                value=(
                    "H1"
                    in st.session_state.get("selected_headers", ["Title", "H1", "H2"])
                ),
            ):
                headers_to_extract.append("H1")
            if st.checkbox(
                "H2",
                value=(
                    "H2"
                    in st.session_state.get("selected_headers", ["Title", "H1", "H2"])
                ),
            ):
                headers_to_extract.append("H2")
            if st.checkbox(
                "H3", value=("H3" in st.session_state.get("selected_headers", []))
            ):
                headers_to_extract.append("H3")

        with col2:
            if st.checkbox(
                "H4", value=("H4" in st.session_state.get("selected_headers", []))
            ):
                headers_to_extract.append("H4")
            if st.checkbox(
                "H5", value=("H5" in st.session_state.get("selected_headers", []))
            ):
                headers_to_extract.append("H5")
            if st.checkbox(
                "H6", value=("H6" in st.session_state.get("selected_headers", []))
            ):
                headers_to_extract.append("H6")
            if st.checkbox(
                "Meta Description",
                value=(
                    "Meta Description" in st.session_state.get("selected_headers", [])
                ),
            ):
                headers_to_extract.append("Meta Description")

        # Update session state with selected headers
        st.session_state["selected_headers"] = headers_to_extract

        # Additional custom headers input
        st.session_state["additional_headers"] = st.text_input(
            "Additional headers (comma separated):",
            value=st.session_state.get("additional_headers", ""),
        )

        # Button to start the scraping process
        if st.button("Search and Scrape"):
            search_and_scrape()

    # Main content area
    st.title("Enhanced Web Scraper")
    st.markdown(
        """
    This app uses enhanced browser technology to extract headers from web pages.
    Enter a search term in the sidebar, select which headers you want to extract,
    and click 'Search and Scrape'.
    """
    )

    # Display results if available
    if "results_df" in st.session_state and not st.session_state["results_df"].empty:
        st.subheader("Results")
        # Display DataFrame without the index
        st.dataframe(
            st.session_state["results_df"], use_container_width=True, hide_index=True
        )

        # Add export options
        st.subheader("Export Options")

        # Export to CSV
        csv = st.session_state["results_df"].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="scraped_results.csv",
            mime="text/csv",
        )

        # Try to export to Excel if xlsxwriter is available
        try:
            import xlsxwriter  # noqa: F401

            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                st.session_state["results_df"].to_excel(
                    writer, sheet_name="Results", index=False
                )
                # Close the writer to save the content to the buffer
                writer.close()

            excel_data = buffer.getvalue()
            excel_mime_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.download_button(
                label="Download Excel",
                data=excel_data,
                file_name="scraped_results.xlsx",
                mime=excel_mime_type,
            )
        except ImportError:
            st.warning("Excel export not available. 'xlsxwriter' package not found.")

        # Export to PDF
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []

            # Add a title
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Scraped Results", styles["Title"]))
            elements.append(Spacer(1, 12))

            # Prepare data for the table
            df = st.session_state["results_df"]
            data = [df.columns.tolist()] + df.values.tolist()

            # Create and style the table
            table = Table(data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            elements.append(table)
            doc.build(elements)

            # Get the value of the BytesIO buffer
            pdf_data = buffer.getvalue()
            buffer.close()

            # Provide a download button for the PDF
            st.download_button(
                label="Download PDF",
                data=pdf_data,
                file_name="scraped_results.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"Error creating PDF: {str(e)}")
            logging.error(f"Error creating PDF: {str(e)}")

    # Listen for "Enter" key in search input
    st.markdown(
        """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && doc.activeElement.id.endsWith('search_term')) {
            const buttons = Array.from(doc.querySelectorAll('button'));
            const isScrapeButton = button => button.innerText === 'Search and Scrape';
            const scrapeButton = buttons.find(isScrapeButton);
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
