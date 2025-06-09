# SaaS Growth Dispatch – Documentation

## 🔧 Architecture Overview
> End-to-end system for extracting Reddit pain points, clustering insights with LLMs, and generating monetizable lead magnets.

### Core Components:
- 🔍 `reddit_scraper.py`: Scrapes Reddit posts and comments
- 💡 `llm_client.py`: Uses GPT-4 and Gemini to summarize and cluster pain points
- 📊 `weekly_analytics.py`: Aggregates weekly themes and prepares JSON output
- 🧾 `pdf_generator.py`: Renders professional PDF lead magnets
- ✉️ `email_utils.py`: Sends daily and weekly emails via Zoho SMTP
- 🧠 `generate_lead_magnet.py`: Entry point for `make lead-magnet`
- ✅ Automated by GitHub Actions

## 📁 Output
- `reports/weekly_report_latest.json`
- `reports/SaaS_Pain_Point_Report_latest.pdf`

## 📄 Sub-Docs
- [Web Scraping Decision ADR](0001-web-scraping-solution-selection.md)
- [Undetected Chrome Scraper Manual](manuals/undetected_scraper_usage.md)
