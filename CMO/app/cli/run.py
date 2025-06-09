from reddit_scraper import main

from app.utils.query_rotation import get_daily_query

if __name__ == "__main__":
    print(f"🔄 Today's search query: '{get_daily_query()}'")
    main()
