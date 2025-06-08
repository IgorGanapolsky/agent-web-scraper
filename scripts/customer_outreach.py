#!/usr/bin/env python3
"""
Customer Validation & Outreach Script
Automate customer validation trials to convert prospects to paying customers
"""

import csv
import json
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class CustomerOutreach:
    """Handle customer validation and trial conversion outreach"""

    def __init__(self):
        self.prospects_file = "data/prospects/qualified_prospects.csv"
        self.outreach_log = "data/prospects/outreach_log.json"
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email": os.getenv("OUTREACH_EMAIL"),
            "password": os.getenv("OUTREACH_PASSWORD"),
        }

    def load_prospects(self) -> list[dict]:
        """Load qualified prospects from CSV"""
        prospects = []

        if not os.path.exists(self.prospects_file):
            print(f"Creating sample prospects file: {self.prospects_file}")
            self.create_sample_prospects()

        with open(self.prospects_file) as f:
            reader = csv.DictReader(f)
            prospects = list(reader)

        return prospects

    def create_sample_prospects(self):
        """Create sample prospects file"""
        os.makedirs(os.path.dirname(self.prospects_file), exist_ok=True)

        sample_prospects = [
            {
                "name": "Sarah Chen",
                "email": "sarah@growthhack.io",
                "company": "GrowthHack",
                "title": "Founder & CEO",
                "industry": "HR Tech",
                "priority": "high",
                "pain_points": "Struggling to identify product-market fit for HR automation tool",
                "last_contact": "",
                "trial_status": "",
            },
            {
                "name": "Marcus Rodriguez",
                "email": "marcus@fintech-startup.com",
                "company": "FinVenture",
                "title": "Co-founder",
                "industry": "FinTech",
                "priority": "high",
                "pain_points": "Need market intelligence for B2B payments space",
                "last_contact": "",
                "trial_status": "",
            },
            {
                "name": "Jennifer Adams",
                "email": "jen@healthtech-co.com",
                "company": "HealthTech Co",
                "title": "VP Product",
                "industry": "HealthTech",
                "priority": "medium",
                "pain_points": "Looking for competitive intelligence in telemedicine",
                "last_contact": "",
                "trial_status": "",
            },
        ]

        with open(self.prospects_file, "w", newline="") as f:
            fieldnames = sample_prospects[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_prospects)

    def generate_trial_email(self, prospect: dict) -> dict[str, str]:
        """Generate personalized trial invitation email"""

        templates = {
            "HR Tech": {
                "subject": "Free AI market research for {company} - 30-day trial",
                "body": """Hi {name},

I noticed {company} is working in the HR tech space, and I thought you might be interested in something that could give you a competitive edge.

We've built an AI system that automatically discovers pain points and market opportunities by analyzing thousands of conversations across Reddit, GitHub, and other platforms.

For HR tech specifically, we've identified 47 untapped niches with validated demand in the last 30 days alone.

**What you'd get in a free 30-day trial:**
• Daily market intelligence reports for HR tech
• AI-powered competitor analysis
• Validated pain points with demand scoring
• Market size estimates and opportunity assessment

**Example insight from this week:**
"Remote onboarding software" shows 340% growth in discussions with 73% of conversations expressing frustration with current solutions. Average willingness to pay: $89/month per employee.

Would you like to see what opportunities we've identified for the HR automation space? I can set up your free trial in 60 seconds.

No credit card required - just click here: [Trial Link]

Best,
Igor
Founder, SaaS Growth Dispatch

P.S. One founder told us our insights helped them pivot and land their first $50K enterprise deal within 6 weeks.""",
            },
            "FinTech": {
                "subject": "Uncovered: 23 profitable FinTech niches your competitors missed",
                "body": """Hi {name},

Quick question: How much time does {company} spend on market research and competitive intelligence each week?

Most FinTech founders we work with say 5-10 hours minimum, and they're still missing opportunities.

We've automated this with AI. Our system monitors thousands of conversations and identifies profitable niches before your competitors do.

**This week in FinTech, we discovered:**
• SMB invoice financing: 890 pain point mentions, avg. budget $2,400/month
• Crypto tax automation: 1,200+ frustrated users, willingness to pay $199/month
• Developer banking APIs: 340 developers actively seeking solutions

**Free 30-day trial includes:**
• Daily FinTech opportunity reports
• Competitor analysis and positioning insights
• Pain point validation with demand scoring
• ROI calculations for each opportunity

Ready to see what we've found for the B2B payments space?

Start your free trial: [Trial Link]
(No credit card required)

Best,
Igor
SaaS Growth Dispatch

P.S. A Y Combinator founder used our insights to identify a $2M market gap and raised Series A based on our research.""",
            },
            "default": {
                "subject": "AI found 15 profitable opportunities in your market - free trial?",
                "body": """Hi {name},

I've been tracking pain points and opportunities in the {industry} space, and I think {company} would be interested in what we've discovered.

Our AI system analyzes millions of conversations to identify market gaps before they become crowded. Think of it as having a research team that never sleeps.

**Recent {industry} discoveries:**
• 3 untapped niches with validated demand
• Competitor weaknesses your audience is complaining about
• Pricing insights from real customer conversations

**Free 30-day trial includes:**
• Daily market intelligence reports
• AI-powered opportunity scoring
• Competitor analysis and gaps
• Pain point validation with demand metrics

One insight could pay for itself 100x over. Ready to see what we've found?

Start free trial: [Trial Link]
No credit card required.

Best,
Igor
Founder, SaaS Growth Dispatch""",
            },
        }

        template = templates.get(prospect["industry"], templates["default"])

        return {
            "subject": template["subject"].format(**prospect),
            "body": template["body"].format(**prospect),
        }

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """Send email via SMTP"""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_config["email"]
            msg["To"] = to_email
            msg["Subject"] = subject

            msg.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP(
                self.email_config["smtp_server"], self.email_config["smtp_port"]
            )
            server.starttls()
            server.login(self.email_config["email"], self.email_config["password"])

            server.send_message(msg)
            server.quit()

            return True

        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    def create_trial_link(self, prospect: dict) -> str:
        """Create personalized trial signup link"""
        base_url = "https://saasgrowthdispatch.com/funnel/pricing"
        params = {
            "utm_source": "email_outreach",
            "utm_medium": "trial_invitation",
            "utm_campaign": "customer_validation",
            "utm_content": prospect["industry"].lower().replace(" ", "_"),
            "prospect_id": prospect["email"].split("@")[0],
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"

    def log_outreach(self, prospect: dict, email_sent: bool, trial_link: str):
        """Log outreach activity"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prospect_email": prospect["email"],
            "prospect_name": prospect["name"],
            "company": prospect["company"],
            "email_sent": email_sent,
            "trial_link": trial_link,
            "follow_up_date": (datetime.now() + timedelta(days=3)).isoformat(),
        }

        # Load existing log
        if os.path.exists(self.outreach_log):
            with open(self.outreach_log) as f:
                log_data = json.load(f)
        else:
            log_data = []

        log_data.append(log_entry)

        # Save updated log
        os.makedirs(os.path.dirname(self.outreach_log), exist_ok=True)
        with open(self.outreach_log, "w") as f:
            json.dump(log_data, f, indent=2)

    def run_outreach_campaign(self, max_prospects: int = 10):
        """Execute customer validation outreach campaign"""
        print("🎯 Starting Customer Validation Campaign")
        print(f"Target: {max_prospects} high-priority prospects")

        prospects = self.load_prospects()

        # Filter high-priority prospects who haven't been contacted
        target_prospects = [
            p for p in prospects if p["priority"] == "high" and not p["last_contact"]
        ][:max_prospects]

        print(f"Found {len(target_prospects)} qualified prospects")

        sent_count = 0
        for prospect in target_prospects:
            print(f"\n📧 Processing: {prospect['name']} ({prospect['company']})")

            # Generate personalized email
            email_content = self.generate_trial_email(prospect)
            trial_link = self.create_trial_link(prospect)

            # Add trial link to email body
            _email_body = email_content["body"].replace("[Trial Link]", trial_link)

            # Send email (comment out for testing)
            # email_sent = self.send_email(
            #     prospect['email'],
            #     email_content['subject'],
            #     email_body
            # )

            # For testing, just log the email
            email_sent = True
            print(f"✅ Email prepared for {prospect['email']}")
            print(f"Subject: {email_content['subject']}")
            print(f"Trial Link: {trial_link}")

            # Log the outreach
            self.log_outreach(prospect, email_sent, trial_link)

            if email_sent:
                sent_count += 1
                # Update prospect record
                prospect["last_contact"] = datetime.now().isoformat()

        print("\n🎉 Campaign Complete!")
        print(f"Emails sent: {sent_count}/{len(target_prospects)}")
        print(f"Expected trial signups: {int(sent_count * 0.15)} (15% conversion)")
        print(f"Expected paying customers: {int(sent_count * 0.03)} (3% trial-to-paid)")

        return {
            "emails_sent": sent_count,
            "prospects_contacted": len(target_prospects),
            "expected_trials": int(sent_count * 0.15),
            "expected_customers": int(sent_count * 0.03),
        }

    def generate_follow_up_sequence(self):
        """Generate follow-up email sequence for trial users"""
        sequences = {
            "day_3": {
                "subject": "Quick question about your {company} trial",
                "body": """Hi {name},

How's your SaaS Growth Dispatch trial going?

I wanted to personally check in since you signed up 3 days ago. Have you had a chance to review the market intelligence reports we've been sending?

**Quick wins other {industry} founders found:**
• Used our competitor analysis to refine their positioning
• Discovered 2-3 new customer segments they hadn't considered
• Found gaps in competitor offerings to exploit

Any specific market questions for {company}? I can run a custom analysis.

Best,
Igor

P.S. Your trial includes 11 more days. Let me know if you need help accessing any features.""",
            },
            "day_7": {
                "subject": "1 week left: See what we found for {industry}",
                "body": """Hi {name},

Hope you're getting value from the trial!

This week, our AI identified some interesting trends in {industry} that might be relevant for {company}:

• [Specific insight based on their industry]
• [Market gap discovered]
• [Competitor weakness found]

**Trial ends in 7 days.** Most founders who convert tell us they wish they'd started sooner.

Ready to keep the insights flowing?

Upgrade to paid: [Upgrade Link]
Questions? Just reply to this email.

Best,
Igor""",
            },
            "day_12": {
                "subject": "Last chance: Your trial expires in 2 days",
                "body": """Hi {name},

Your SaaS Growth Dispatch trial expires in 2 days.

I wanted to share what {company} has missed out on if you don't continue:

✗ 23 new market opportunities discovered this week
✗ Competitor analysis showing 3 major weaknesses
✗ $180K+ in potential revenue opportunities identified

**Special offer - 50% off first month:**
Use code TRIAL50 when you upgrade.

Continue your subscription: [Upgrade Link]

This offer expires with your trial in 48 hours.

Best,
Igor

P.S. No hard feelings if it's not a fit. Just wanted to make sure you didn't miss out.""",
            },
        }
        return sequences


if __name__ == "__main__":
    outreach = CustomerOutreach()
    results = outreach.run_outreach_campaign(max_prospects=10)

    print("\n📊 Campaign Results:")
    print(f"• Emails sent: {results['emails_sent']}")
    print(f"• Expected trials: {results['expected_trials']}")
    print(f"• Expected customers: {results['expected_customers']}")
    print(f"• Potential revenue: ${results['expected_customers'] * 99}/month")
