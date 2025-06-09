#!/usr/bin/env python3
"""
Automated GitHub Issues Creation Script
Creates the 16 roadmap issues from the manual guide
"""

import json

# Define all 16 issues with their details
ISSUES_DATA = [
    {
        "title": "Add Stripe integration for monetization",
        "labels": ["enhancement", "high-priority", "business"],
        "body": """Implement Stripe payment workflow for paid research packs to enable revenue generation from the platform.

**Acceptance Criteria:**
- Integrate Stripe checkout flow
- Create pricing tiers for research packs
- Implement payment success/failure handling
- Add subscription management
- Set up webhook handling for payment events

**Business Impact:** Direct revenue generation capability""",
    },
    {
        "title": "Set up weekly chart report automation",
        "labels": ["enhancement", "high-priority", "automation"],
        "body": """Implement automated weekly chart generation and reporting system.

**Acceptance Criteria:**
- Automate chart generation from CSV data
- Integrate dynamic charts into web UI
- Schedule weekly report generation
- Email delivery of visual reports
- Dashboard integration

**Business Impact:** Streamlined reporting process""",
    },
    {
        "title": "Complete Google Search integration",
        "labels": ["enhancement", "high-priority", "feature"],
        "body": """Finish implementing Google Search data source integration.

**Acceptance Criteria:**
- Complete SerpAPI integration
- Implement search result processing
- Add search query management
- Handle rate limiting and errors
- Test integration with existing pipeline

**Business Impact:** Expanded data sources for analysis""",
    },
    {
        "title": "Complete Pain Point Extractor module",
        "labels": ["enhancement", "high-priority", "ai"],
        "body": """Finish implementing the Pain Point Extractor processing pipeline.

**Acceptance Criteria:**
- Implement pain point classification
- Add sentiment analysis
- Create pain point ranking algorithm
- Integrate with existing summarizer
- Add output formatting

**Business Impact:** Better insight quality for customers""",
    },
    {
        "title": "Complete Email Digests functionality",
        "labels": ["enhancement", "high-priority", "feature"],
        "body": """Finish implementing automated email digest system.

**Acceptance Criteria:**
- Complete email template system
- Implement digest scheduling
- Add personalization features
- Test email deliverability
- Add unsubscribe functionality

**Business Impact:** Customer engagement and retention""",
    },
    {
        "title": "Complete Zoho SMTP Emailer",
        "labels": ["enhancement", "high-priority", "integration"],
        "body": """Finish implementing Zoho SMTP integration for email delivery.

**Acceptance Criteria:**
- Complete SMTP configuration
- Implement email templates
- Add error handling and retry logic
- Test email deliverability
- Add email tracking

**Business Impact:** Reliable email delivery system""",
    },
    {
        "title": "Implement Lead Generation tracking",
        "labels": ["enhancement", "high-priority", "analytics"],
        "body": """Track and analyze lead generation metrics from the platform.

**Acceptance Criteria:**
- Implement lead tracking system
- Add conversion analytics
- Create lead scoring mechanism
- Build reporting dashboard
- Integrate with CRM (future)

**Business Impact:** Measurable business outcomes""",
    },
    {
        "title": "Add Twitter Scraper",
        "labels": ["enhancement", "medium-priority", "feature"],
        "body": """Implement Twitter data scraping capabilities.

**Acceptance Criteria:**
- Integrate Twitter API or scraping solution
- Handle rate limiting
- Process tweet data
- Extract relevant insights
- Integrate with existing pipeline

**Business Impact:** Additional data source for market insights""",
    },
    {
        "title": "Implement Trend Analyzer",
        "labels": ["enhancement", "medium-priority", "ai"],
        "body": """Build trend analysis capabilities for market insights.

**Acceptance Criteria:**
- Implement trend detection algorithms
- Add time-series analysis
- Create trend visualization
- Generate trend reports
- Predict future trends

**Business Impact:** Proactive market insights""",
    },
    {
        "title": "Add Cold Outreach Emails",
        "labels": ["enhancement", "medium-priority", "feature"],
        "body": """Implement automated cold outreach email system.

**Acceptance Criteria:**
- Create email templates
- Implement personalization
- Add A/B testing
- Track open/click rates
- Manage email sequences

**Business Impact:** Automated lead generation""",
    },
    {
        "title": "Implement CRM Integration",
        "labels": ["enhancement", "medium-priority", "integration"],
        "body": """Integrate with popular CRM systems.

**Acceptance Criteria:**
- Support major CRM platforms (HubSpot, Salesforce, etc.)
- Sync lead data
- Track interactions
- Update lead status
- Generate CRM reports

**Business Impact:** Streamlined sales process""",
    },
    {
        "title": "Add Backup Logging (CSV/DB)",
        "labels": ["enhancement", "medium-priority", "infrastructure"],
        "body": """Implement backup logging system for data persistence.

**Acceptance Criteria:**
- Add CSV export functionality
- Implement database backup
- Create data recovery procedures
- Add data retention policies
- Monitor backup health

**Business Impact:** Data security and reliability""",
    },
    {
        "title": "Track Responses Received",
        "labels": ["enhancement", "low-priority", "analytics"],
        "body": """Implement response tracking for outreach campaigns.

**Acceptance Criteria:**
- Track email responses
- Categorize response types
- Measure response rates
- Generate response analytics
- Optimize outreach based on responses

**Business Impact:** Improved outreach effectiveness""",
    },
    {
        "title": "Track Appointments Booked",
        "labels": ["enhancement", "low-priority", "analytics"],
        "body": """Track appointment booking metrics.

**Acceptance Criteria:**
- Integrate with calendar systems
- Track booking rates
- Measure conversion from lead to appointment
- Generate booking analytics
- Optimize booking process

**Business Impact:** Sales conversion tracking""",
    },
    {
        "title": "Track Revenue Earned",
        "labels": ["enhancement", "low-priority", "analytics"],
        "body": """Implement comprehensive revenue tracking.

**Acceptance Criteria:**
- Track all revenue sources
- Calculate customer lifetime value
- Measure conversion rates
- Generate revenue reports
- Forecast future revenue

**Business Impact:** Business performance insights""",
    },
    {
        "title": "Offer API access to niche detection + pain point summarization",
        "labels": ["enhancement", "medium-priority", "api"],
        "body": """Create API endpoints for external access to core functionality.

**Acceptance Criteria:**
- Design RESTful API
- Implement authentication
- Create API documentation
- Add rate limiting
- Set up monitoring
- Create pricing tiers for API access

**Business Impact:** Additional revenue stream and platform expansion""",
    },
]


def create_issues_manually():
    """
    Displays all GitHub issues data for manual creation.
    """
    base_url = "https://github.com/IgorGanapolsky/agent-web-scraper/issues/new"

    print("🚀 GitHub Issues Creation Guide")
    print("📝 Copy the details below to manually create each issue.\n")

    print(
        "🏷️ FIRST: Create these labels at https://github.com/IgorGanapolsky/agent-web-scraper/labels"
    )
    labels_to_create = [
        ("high-priority", "#d73a4a", "Red"),
        ("medium-priority", "#fbca04", "Yellow"),
        ("low-priority", "#0075ca", "Blue"),
        ("ai", "#7057ff", "Purple"),
        ("automation", "#1d76db", "Blue"),
        ("business", "#d4c5f9", "Light Purple"),
        ("analytics", "#e99695", "Pink"),
        ("integration", "#bfd4f2", "Light Blue"),
        ("infrastructure", "#0e8a16", "Green"),
        ("api", "#5319e7", "Dark Purple"),
    ]

    for label, color, desc in labels_to_create:
        print(f"  - {label} ({desc}: {color})")

    print(f"\n📝 THEN: Create issues at {base_url}")
    print("=" * 80)

    for i, issue in enumerate(ISSUES_DATA, 1):
        priority = "HIGH" if i <= 7 else "MEDIUM" if i <= 12 else "LOW"
        print(f"\nISSUE #{i} [{priority} PRIORITY]: {issue['title']}")
        print("-" * 60)
        print(f"Labels: {', '.join(issue['labels'])}")
        print(f"\nTitle: {issue['title']}")
        print(f"\nBody:\n{issue['body']}")
        print("=" * 80)

    print(f"\n✅ All {len(ISSUES_DATA)} issues ready for creation.")
    print("\n📋 Creation checklist:")
    print("1. Create the labels first (if not already created)")
    print("2. Copy title and body for each issue")
    print("3. Add the specified labels to each issue")
    print("4. Create issues in priority order (HIGH → MEDIUM → LOW)")
    print(
        "5. Add issues to your project board: https://github.com/users/IgorGanapolsky/projects/2"
    )


def save_issues_json():
    """Save issues data to JSON for potential future automation"""
    with open("github_issues_roadmap.json", "w") as f:
        json.dump(ISSUES_DATA, f, indent=2)
    print("💾 Saved issues data to github_issues_roadmap.json")


if __name__ == "__main__":
    print("🎯 GitHub Issues Creation Assistant")
    print("This script will help you create the 16 roadmap issues manually.\n")

    # Automatically run both options
    choice = "3"

    if choice in ["1", "3"]:
        create_issues_manually()

    if choice in ["2", "3"]:
        save_issues_json()

    print("\n🎉 Process complete! Happy issue creation!")
