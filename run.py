from app.utils.query_rotation import get_daily_query
from reddit_scraper import main

if __name__ == "__main__":
    print(f"🔄 Today's search query: '{get_daily_query()}'")
    main()
