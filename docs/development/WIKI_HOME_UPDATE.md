# Complete Wiki Home Page Content

Copy and paste this content into your GitHub Wiki Home page:

---

# SaaS Growth Dispatch — Project Wiki

Welcome to the official wiki for `agent-web-scraper`, the engine behind SaaS Growth Dispatch.

## 🎯 Vision

To help SaaS founders discover underserved niches and automation opportunities from real Reddit conversations — turning market frustration into validated product ideas.

## 🧠 Architecture Diagram

![AI-Powered Pain Discovery Pipeline](https://raw.githubusercontent.com/IgorGanapolsky/agent-web-scraper/main/docs/assets/architecture-2025.png)

### Core Pipeline:

1. 📡 **Reddit Search** → via SerpAPI + scheduled scraping
2. 🧠 **Summarization** → GPT-4
3. 🟣 **Pain Point Extraction** → Gemini Pro
4. 📊 **Structuring & Charting** → JSON → LaTeX (PDFs) + CSV
5. 📧 **Delivery** → Email via Zoho SMTP + Formspree for inbound leads
6. 🌐 **Publishing** → GitHub Pages + Reports + Google Sheet log

## 📋 Roadmap

### ✅ Completed
- Reddit Scraper
- Summarizer (GPT-4)
- Google Sheet Logs
- GitHub Actions Scheduler
- Secrets Management
- Q2 2025 Lead Magnet Report
- GitHub Pages Landing Site

### 🔄 In Progress
- Google Search integration
- Pain Point Extractor
- Email Digests
- Zoho SMTP Emailer
- Lead Generation tracking

### 📝 Backlog
- Twitter Scraper
- Trend Analyzer
- Cold Outreach Emails
- CRM Integration
- Revenue Tracking
- Stripe Payment Integration
- API Access for niche detection

## 🏗️ Repo Directory Overview

```
agent-web-scraper/
├── app/
│   ├── cli/           # Command-line interface (Typer)
│   ├── config/        # Configuration and settings (Pydantic)
│   ├── core/          # Core business logic
│   ├── observability/ # Logging, metrics, error tracking (Sentry)
│   └── utils/         # Utility functions
├── docs/              # GitHub Pages site + assets
├── reports/           # Generated lead magnets
└── tests/             # Test suite
```

## 🛠️ Technologies Used

- **Language:** Python 3.10+
- **AI/LLM:** OpenAI GPT-4, Google Gemini Pro
- **Data Sources:** Reddit API, SerpAPI, Google Search
- **Infrastructure:** GitHub Actions, Zoho SMTP, Formspree
- **Analytics:** Google Sheets API, CSV exports
- **Publishing:** GitHub Pages, LaTeX PDF generation
- **Monetization:** Stripe (planned), lead capture forms

---

## Quick Links

- 📊 [Live Analytics Dashboard](https://docs.google.com/spreadsheets/d/1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY/edit)
- 🌐 [SaaS Growth Dispatch Landing Page](https://igorganapolsky.github.io/agent-web-scraper/)
- 📄 [Latest Q2 2025 Report](https://github.com/IgorGanapolsky/agent-web-scraper/blob/main/reports/Q2_2025_SaaS_Pain_Point_Report.md)
- 🔧 [Repository](https://github.com/IgorGanapolsky/agent-web-scraper)
