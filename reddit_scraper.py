import os
import time

import gspread
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from oauth2client.service_account import ServiceAccountCredentials
from openai import OpenAI
from serpapi.google_search import GoogleSearch

from config import SERPAPI_KEY, SPREADSHEET_NAME

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": "Hi!"}]
)

print(response.choices[0].message.content)


def google_search(query):
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
    resp = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RedditScraper/1.0)"},
        timeout=30
    )
    soup = BeautifulSoup(resp.text, "html.parser")
    title = soup.find("title").text
    comments = soup.find_all("div", class_="md")[:3]
    comment_texts = [c.text.strip() for c in comments]
    return title, comment_texts


def summarize_pain_points(title, comments):
    prompt = (
        f"Extract the user pain point from this Reddit post:\n\n"
        f"Title: {title}\nComments:\n" + "\n".join(comments)
    )
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def connect_sheet():
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
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape Reddit for pain points')
    parser.add_argument('search_term', help='Search term for Reddit posts')
    args = parser.parse_args()
    run_scraper(args.search_term)
