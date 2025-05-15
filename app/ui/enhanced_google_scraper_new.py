import os
import streamlit as st
from serpapi import GoogleSearch
import pandas as pd
import time
from dotenv import load_dotenv
import logging
from datetime import datetime
import json
import requests
import re
import urllib.parse
from bs4 import BeautifulSoup
import io
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)

# API Keys
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY", "")

# Constants
ALL_TAG_OPTIONS = ["h1", "h2", "h3", "h4", "h5", "h6", "title"]
DEFAULT_TAGS = ["h1", "h2", "h3", "title"]
max_results = 10  # Maximum number of URLs to scrape
debug_mode = False  # Set to True to see API responses

# Domains that are known to block scraping
FIRECRAWL_BLOCKLIST = [
    "linkedin.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "tiktok.com", "pinterest.com", "reddit.com", "quora.com", "medium.com",
    "forbes.com", "nytimes.com", "wsj.com", "bloomberg.com", "cnbc.com",
    "businessinsider.com", "washingtonpost.com", "theguardian.com",
    "bbc.com", "cnn.com", "foxnews.com", "nbcnews.com", "cbsnews.com",
    "abcnews.go.com", "reuters.com", "apnews.com", "economist.com",
    "ft.com", "marketwatch.com", "investopedia.com", "seekingalpha.com"
]

def is_blocked_url(url):
    """Check if URL domain is in the blocklist."""
    try:
        domain = urllib.parse.urlparse(url).netloc.lower()
        return any(bad in domain for bad in FIRECRAWL_BLOCKLIST)
    except Exception:
        return False

def extract_headers_with_soup(url, tags_to_analyze):
    """Fallback scraper using requests + BeautifulSoup for simple sites."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        results = []

        for tag in tags_to_analyze:
            headers = soup.find_all(tag)
            for header in headers:
                header_text = header.get_text().strip()
                if header_text:  # Skip empty headers
                    results.append({
                        "tag": tag,
                        "content": header_text,
                        "url": url
                    })

        return results
    except Exception as e:
        raise Exception(f"Simple scraper failed: {str(e)}")

# --- Dark/Light mode CSS ---
def set_theme(dark_mode=True):
    if dark_mode:
        st.markdown("""
            <style>
            .stApp {background-color: #1E1E2F; color: #FFFFFF;}
            .stButton>button {background-color: #4CAF50; color: white; border-radius: 5px;}
            .stTextInput>div>div>input {background-color: #2D2D44; color: #FFFFFF; border-radius: 5px;}
            .stSlider>div>div>div {background-color: #444; color: #FFF;}
            .stSlider .css-1aumxhk {background: #444 !important; color: #FFF !important;}
            .stMultiSelect>div>div>div {background: #222; color: #FFF;}
            .stMultiSelect>div>div>div>div>div>div {border: 1px solid #444 !important;}
            .stDataFrame {background: #222; color: #FFF;}
            </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <style>
            .stApp {background-color: #F5F5F5; color: #222;}
            .stButton>button {background-color: #4CAF50; color: white; border-radius: 5px;}
            .stTextInput>div>div>input {background-color: #FFF; color: #222; border-radius: 5px;}
            .stSlider>div>div>div {background-color: #DDD; color: #222;}
            .stSlider .css-1aumxhk {background: #DDD !important; color: #222 !important;}
            .stMultiSelect>div>div>div {background: #FFF; color: #222;}
            .stMultiSelect>div>div>div>div>div>div {border: 1px solid #CCC !important;}
            .stDataFrame {background: #FFF; color: #222;}
            </style>
        """, unsafe_allow_html=True)

def main():
    # Set page config
    st.set_page_config(
        page_title="Enhanced Google Scraper",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Set dark mode
    set_theme(dark_mode=True)

    # Initialize session state
    if 'search_term' not in st.session_state:
        st.session_state['search_term'] = ""
    if 'tags_to_analyze' not in st.session_state:
        st.session_state['tags_to_analyze'] = DEFAULT_TAGS
    if 'is_scraping' not in st.session_state:
        st.session_state['is_scraping'] = False
    if 'cancel_scrape' not in st.session_state:
        st.session_state['cancel_scrape'] = False
    if 'download_clicked' not in st.session_state:
        st.session_state['download_clicked'] = False
    if 'download_type' not in st.session_state:
        st.session_state['download_type'] = None

    # Title and description
    st.title("🔍 Enhanced Google Scraper")
    st.markdown("""
    This dashboard extracts and analyzes headers from top Google search results for any query.
    It uses SerpApi to get search results and Firecrawl to extract content from websites.
    """)

    # Sidebar
    st.sidebar.title("API Status")
    serpapi_status = st.sidebar.empty()
    firecrawl_status = st.sidebar.empty()
    serpapi_usage = st.sidebar.empty()
    firecrawl_usage = st.sidebar.empty()

    # Check API keys
    if not SERPAPI_KEY:
        serpapi_status.error("⚠️ SerpApi key not found. Please add it to your .env file.")
    else:
        serpapi_status.success("✅ SerpApi key configured")

    if not FIRECRAWL_KEY:
        firecrawl_status.error("⚠️ Firecrawl key not found. Please add it to your .env file.")
    else:
        firecrawl_status.success("✅ Firecrawl key configured")

    # Search form
    if not st.session_state.get('is_scraping', False):
        search_form = st.form(key="search_form")
        tags_to_analyze = search_form.multiselect(
            "Tags to Analyze",
            ALL_TAG_OPTIONS,
            default=st.session_state['tags_to_analyze'],
            key="tags_to_analyze_box",
            help="Which HTML heading tags to extract from each page."
        )
        if len(tags_to_analyze) == len(ALL_TAG_OPTIONS):
            search_form.caption(":information_source: All available tags selected.")
        search_term_input = search_form.text_input(
            "Enter a search term",
            value=st.session_state['search_term'],
            placeholder="best affiliate marketing coaching programs in 2023",
            key="search_term_box"
        )
        search_submitted = search_form.form_submit_button("Scrape")
        if search_submitted:
            st.session_state['search_term'] = search_term_input
            st.session_state['tags_to_analyze'] = tags_to_analyze
            st.session_state['is_scraping'] = True
    else:
        tags_to_analyze = st.session_state['tags_to_analyze']
        st.multiselect("Tags to Analyze", ALL_TAG_OPTIONS, default=tags_to_analyze, disabled=True)
        st.text_input("Enter a search term", value=st.session_state['search_term'], disabled=True)
        if st.button("Cancel Scraping"):
            st.session_state['cancel_scrape'] = True
            st.warning("Cancelling scrape operation...")

    # --- SCRAPING LOGIC ---
    if st.session_state.get('is_scraping', False) and not st.session_state.get('cancel_scrape', False):
        search_term = st.session_state['search_term']
        try:
            # Step 1: SerpApi - Extract Top URLs
            params = {
                "q": search_term,
                "engine": "google",
                "google_domain": "google.com",
                "gl": "us",
                "hl": "en",
                "num": max_results,  # Number of results per page
                "api_key": SERPAPI_KEY
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            if debug_mode:
                st.write("SerpApi Response Keys:", list(results.keys()))
                st.write("SerpApi Full Response:", results)
            if 'error' in results:
                st.error(f"SerpApi error: {results['error']}")
                st.stop()

            def extract_url(item):
                return item.get('link')

            top_urls = []
            if 'organic_results' in results and isinstance(results['organic_results'], list):
                for item in results['organic_results']:
                    url = extract_url(item)
                    if url and url not in top_urls:
                        top_urls.append(url)
            top_urls = top_urls[:max_results]

            def log_scrape_event(status, search_term, extracted_urls, serpapi_response, page_results=None, error_message=None):
                log_entry = {
                    "status": status,
                    "search_term": search_term,
                    "urls": extracted_urls,
                    "serpapi_response": serpapi_response,
                }
                if page_results:
                    log_entry["page_results"] = page_results
                if error_message:
                    log_entry["error"] = error_message
                with open("scraper.log", "a") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False, indent=2) + "\n")

            if not top_urls:
                log_scrape_event(
                    status="failure",
                    search_term=search_term,
                    extracted_urls=[],
                    serpapi_response=results,
                    error_message="No search results found. Check your SerpApi key, quota, or try a different term."
                )
                st.error("No search results found. Check your SerpApi key, quota, or try a different term.")
                st.stop()
            else:
                log_scrape_event(
                    status="success",
                    search_term=search_term,
                    extracted_urls=top_urls,
                    serpapi_response=results
                )

            search_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success(f"Found {len(top_urls)} URLs:")
            st.write('Extracted URLs:', top_urls)

            # Update SerpApi usage
            serpapi_usage.text(f"SerpApi Searches Used: 1")  # Update dynamically if tracking API

            headers_data = []
            firecrawl_errors = []
            progress = st.progress(0)
            successful_scrapes = 0
            search_keywords = set(re.findall(r"\w+", search_term.lower()))

            # Add explanatory message about scraping limitations
            st.info("⚠️ Some websites use anti-scraping technology and cannot be accessed automatically. The dashboard will try multiple methods to extract content.")

            for i, url in enumerate(top_urls):
                if st.session_state.get('cancel_scrape', False):
                    st.warning("Scraping cancelled by user.")
                    break
                
                progress.progress((i + 1) / len(top_urls))
                
                # Display current URL being processed
                status_msg = st.empty()
                status_msg.info(f"Processing {i+1}/{len(top_urls)}: {url}")
                
                scraped = False
                error_msg = ""
                
                # Method 1: Check if URL is on blocklist
                if is_blocked_url(url):
                    error_msg = f"URL {url} is likely protected against scraping (domain in blocklist)"
                    
                    # Try Method 2: Simple BeautifulSoup scraper
                    try:
                        soup_results = extract_headers_with_soup(url, tags_to_analyze)
                        if soup_results:
                            for item in soup_results:
                                item["source"] = "beautifulsoup"
                                item["url"] = url  # Ensure URL is set correctly
                            headers_data.extend(soup_results)
                            successful_scrapes += 1
                            scraped = True
                            status_msg.success(f"Successfully scraped {url} using fallback method")
                        else:
                            raise Exception("No headers found with BeautifulSoup")
                    except Exception as e:
                        error_msg = f"Both scraping methods failed for {url}: {str(e)}"
                else:
                    # Method 1: Try Firecrawl first for non-blocked URLs
                    try:
                        # Firecrawl HTTP API integration
                        firecrawl_api_url = "https://api.firecrawl.dev/v1/scrape"
                        firecrawl_headers = {"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"}
                        firecrawl_payload = {
                            "url": url,
                            "extract": {
                                "prompt": f"Extract all {', '.join(tags_to_analyze)} tags",
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "object", "properties": {
                                        "tag": {"type": "string"},
                                        "content": {"type": "string"},
                                        "url": {"type": "string"}
                                    }}
                                }
                            },
                            "screenshot": True,
                            "pageOptions": {"render_js": True}
                        }
                        
                        response = requests.post(firecrawl_api_url, headers=firecrawl_headers, json=firecrawl_payload, timeout=40)
                        response.raise_for_status()
                        result = response.json()
                        
                        if result and result.get("extract"):
                            for item in result["extract"]:
                                item["screenshot"] = result.get("screenshot", "")
                                item["source"] = "firecrawl"
                                item["url"] = url  # Ensure URL is set correctly
                            headers_data.extend(result["extract"])
                            successful_scrapes += 1
                            scraped = True
                            status_msg.success(f"Successfully scraped {url} using Firecrawl")
                        else:
                            # If Firecrawl returns empty results, try the simple scraper
                            raise Exception("Firecrawl returned empty results")
                            
                    except Exception as e:
                        error_msg = f"Firecrawl failed for {url}: {str(e)}"
                        
                        # Try Method 2: Simple BeautifulSoup scraper as fallback
                        try:
                            soup_results = extract_headers_with_soup(url, tags_to_analyze)
                            if soup_results:
                                for item in soup_results:
                                    item["source"] = "beautifulsoup"
                                    item["url"] = url  # Ensure URL is set correctly
                                headers_data.extend(soup_results)
                                successful_scrapes += 1
                                scraped = True
                                status_msg.success(f"Successfully scraped {url} using fallback method")
                            else:
                                raise Exception("No headers found with BeautifulSoup")
                        except Exception as soup_error:
                            error_msg += f" | Simple scraper failed: {str(soup_error)}"
                
                # Record errors if both methods failed
                if not scraped:
                    firecrawl_errors.append({"url": url, "error": error_msg})
                    status_msg.warning(f"Failed to scrape {url}")

            # Clear status message
            status_msg.empty()

            # Decide scrape status
            if successful_scrapes == 0:
                scrape_status = "failure"
            elif successful_scrapes < len(top_urls):
                scrape_status = "partial"
            else:
                scrape_status = "success"

            # Display scrape status summary
            if scrape_status == "success":
                st.success(f"Successfully scraped all {len(top_urls)} URLs!")
            elif scrape_status == "partial":
                st.warning(f"Partially successful: scraped {successful_scrapes} out of {len(top_urls)} URLs.")
            else:
                st.error("Failed to scrape any content. Try different search terms or check your API keys.")

            firecrawl_usage.text(f"Firecrawl Credits Used: {len(top_urls)}")

            # --- Results processing ---
            # Only process if we have data
            if headers_data:
                page_results = []
                for item in headers_data:
                    header_words = set(re.findall(r"\w+", item["content"].lower()))
                    matched_keywords = list(search_keywords & header_words)
                    page_results.append({
                        "url": item["url"],
                        "source": item.get("source", "unknown"),
                        "tag": item.get("tag", ""),
                        "header": item["content"],
                        "matched_keywords": matched_keywords
                    })

                st.subheader(f"Found {len(headers_data)} headers from {successful_scrapes} pages:")

                # Create a nicer dataframe with all relevant information
                df = pd.DataFrame([
                    {
                        "URL": page["url"],
                        "Tag": page.get("tag", ""),
                        "Header": page["header"],
                        "Matched Keywords": ', '.join(page["matched_keywords"]) if page["matched_keywords"] else 'None',
                        "Source": page.get("source", "blocked site fallback") if page.get("source") == "unknown" else page.get("source", "unknown")
                    }
                    for page in page_results
                ])

                # Display the dataframe with proper styling
                st.dataframe(df, use_container_width=True)

                # Create PDF report function
                def create_pdf(df):
                    buffer = BytesIO()
                    doc = SimpleDocTemplate(buffer, pagesize=letter)
                    elements = []

                    # Add title
                    styles = getSampleStyleSheet()
                    elements.append(Paragraph(f"Search Results for: {search_term}", styles['Title']))
                    elements.append(Spacer(1, 12))

                    # Add timestamp
                    elements.append(Paragraph(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                    elements.append(Spacer(1, 12))

                    # Convert DataFrame to a list of lists for the table
                    data = [df.columns.tolist()]  # Headers
                    for i, row in df.iterrows():
                        data.append(row.tolist())

                    # Create the table
                    table = Table(data)

                    # Add style
                    style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ])

                    # Add alternating row colors
                    for i in range(1, len(data)):
                        if i % 2 == 0:
                            style.add('BACKGROUND', (0, i), (-1, i), colors.lightgrey)

                    table.setStyle(style)
                    elements.append(table)

                    # Build the PDF
                    doc.build(elements)
                    buffer.seek(0)
                    return buffer

                # Provide download options
                csv = df.to_csv(index=False)
                excel_buffer = io.BytesIO()
                df.to_excel(excel_buffer, index=False, engine='openpyxl')
                excel_buffer.seek(0)

                # Create PDF report
                pdf_buffer = create_pdf(df)

                # Create download buttons with callbacks to set the download flag
                col1, col2, col3 = st.columns(3)
                with col1:
                    download_csv = st.download_button(
                        "Download CSV",
                        csv,
                        "scrape_results.csv",
                        "text/csv",
                        on_click=lambda: st.session_state.update({'download_clicked': True, 'download_type': 'CSV'})
                    )
                with col2:
                    download_excel = st.download_button(
                        "Download Excel",
                        excel_buffer,
                        "scrape_results.xlsx",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        on_click=lambda: st.session_state.update({'download_clicked': True, 'download_type': 'Excel'})
                    )
                with col3:
                    download_pdf = st.download_button(
                        "Download PDF",
                        pdf_buffer,
                        "scrape_results.pdf",
                        "application/pdf",
                        on_click=lambda: st.session_state.update({'download_clicked': True, 'download_type': 'PDF'})
                    )
            else:
                st.error("No headers found. Try different search terms or tags.")

            # Update logging with comprehensive information
            log_scrape_event(
                status=scrape_status,
                search_term=search_term,
                extracted_urls=top_urls,
                serpapi_response=results,
                page_results=headers_data,
                error_message=firecrawl_errors if firecrawl_errors else None
            )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            logging.error(f"Scraper error: {str(e)}")
        finally:
            # Reset scraping state
            st.session_state['is_scraping'] = False
            st.session_state['cancel_scrape'] = False

main()

# Footer
st.markdown("---")
st.markdown("Built with ❤️ by Igor Ganapolsky | Max Smith KDP LLC | 2025")
