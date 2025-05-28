import os
import time

import gspread
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
from serpapi.google_search import GoogleSearch

from config import SERPAPI_KEY, SPREADSHEET_NAME
from security import safe_requests

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": "Hi!"}]
)

print(response.choices[0].message.content)


def google_search(query):
    """
    Performs a Google search for the given query and returns Reddit post URLs.
    
    Args:
        query: The search query string.
    
    Returns:
        A list of URLs from the organic search results that point to Reddit posts.
    """
    search = GoogleSearch(
        {"q": query, "location": "United States", "num": 10, "api_key": SERPAPI_KEY}
    )
    results = search.get_dict()
    return [
        r["link"]
        for r in results.get("organic_results", [])
        if "reddit.com/r/" in r["link"]
    ]


def scrape_reddit_post(url):
    """
    Fetches the title and up to three top comment texts from a Reddit post.
    
    Args:
        url: The URL of the Reddit post to scrape.
    
    Returns:
        A tuple containing the post title and a list of up to three comment texts.
    """
    resp = safe_requests.get(url, headers={"User-Agent": "Mozilla"}, timeout=60)
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("title").text
    comments = soup.find_all("div", class_="md")[:3]
    comment_texts = [c.text.strip() for c in comments]
    return title, comment_texts


def summarize_pain_points(title, comments):
    """
    Generates a summary of user pain points from a Reddit post using GPT-4.
    
    Args:
        title: The title of the Reddit post.
        comments: A list of comment texts from the post.
    
    Returns:
        A string summarizing the main user pain points extracted from the post.
    """
    prompt = (
        f"Extract the user pain point from this Reddit post:\n\n"
        f"Title: {title}\nComments:\n" + "\n".join(comments)
    )
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def connect_sheet():
    """
    Connects to the specified Google Spreadsheet and returns the first worksheet.
    
    Returns:
        The first worksheet of the target Google Spreadsheet as a gspread worksheet object.
    """
    print("Looking for:", SPREADSHEET_NAME)
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "secrets/service_account.json", scope
    )
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet


def run_scraper(search_term):
    """
    Searches for Reddit posts related to a search term, summarizes user pain points, and logs results to a Google Sheet.
    
    Performs a Google search for Reddit posts about the given search term and "pain point," scrapes each post for its title and comments, summarizes user pain points using GPT-4, and appends the results to a connected Google Spreadsheet. Skips posts without comments and continues processing even if individual posts fail.
     
    Args:
        search_term: The topic or keyword to search for in Reddit posts.
    """
    urls = google_search(f"site:reddit.com {search_term} pain point")
    sheet = connect_sheet()

    for url in urls:
        try:
            title, comments = scrape_reddit_post(url)
            if not comments:
                continue
            summary = summarize_pain_points(title, comments)
            sheet.append_row([title, url, comments[0], summary])
            print(f"✅ Logged: {title}")
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    run_scraper("ecommerce content marketing")
