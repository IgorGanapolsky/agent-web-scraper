#!/usr/bin/env python3
"""
Substack Publisher
Publishes daily reports to Substack via email-to-post feature
"""

import csv
import os
import re
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

import markdown
from dotenv import load_dotenv

load_dotenv()


class SubstackPublisher:
    def __init__(self):
        self.smtp_server = "smtp.zoho.com"
        self.smtp_port = 587
        self.sender_email = "support@saasgrowthdispatch.com"
        self.sender_password = os.getenv("ZOHO_APP_PASSWORD", "Rockland25&*")
        self.substack_email = os.getenv(
            "SUBSTACK_EMAIL", "your-substack-email@substack.com"
        )

        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.substack_log_file = self.logs_dir / "substack_posts.csv"

        if not self.sender_password:
            print("⚠️  ZOHO_APP_PASSWORD not found in environment, using default")

        if self.substack_email == "your-substack-email@substack.com":
            print("⚠️  SUBSTACK_EMAIL not configured, using placeholder")

    def find_latest_report(self) -> Optional[Path]:
        """Find the latest daily report file"""
        reports_dir = Path("reports")
        today = datetime.now().strftime("%Y-%m-%d")

        # Try today's report first
        todays_report = reports_dir / f"insight_daily_{today}.md"
        if todays_report.exists():
            print(f"📄 Found today's report: {todays_report}")
            return todays_report

        # Find the most recent daily report
        daily_reports = list(reports_dir.glob("insight_daily_*.md"))
        if daily_reports:
            daily_reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_report = daily_reports[0]
            print(f"📄 Found latest daily report: {latest_report}")
            return latest_report

        print("❌ No daily reports found")
        return None

    def extract_title_from_markdown(self, content: str) -> str:
        """Extract title from markdown content"""
        lines = content.split("\n")
        for line in lines:
            if line.startswith("# "):
                # Remove the # and clean up
                title = line[2:].strip()
                # Remove emojis and clean up for email subject
                title = re.sub(r"[^\w\s-]", "", title).strip()
                return title

        # Fallback title
        return "Daily SaaS Insights Report"

    def convert_markdown_to_html(self, content: str) -> str:
        """Convert markdown content to HTML for email"""
        try:
            # Convert markdown to HTML
            html = markdown.markdown(content, extensions=["extra", "codehilite"])

            # Add some basic styling
            styled_html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    h3 {{ color: #7f8c8d; }}
                    .emoji {{ font-size: 1.2em; }}
                    blockquote {{ border-left: 4px solid #3498db; padding-left: 20px; margin: 20px 0; background: #f8f9fa; }}
                    code {{ background: #f1f2f6; padding: 2px 4px; border-radius: 3px; }}
                    pre {{ background: #2f3542; color: #f1f2f6; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                    ul, ol {{ padding-left: 20px; }}
                    li {{ margin-bottom: 5px; }}
                    .cta-section {{ background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
                    .cta-button {{ background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }}
                </style>
            </head>
            <body>
                {html}
                {self.get_affiliate_cta()}
            </body>
            </html>
            """

            return styled_html

        except Exception as e:
            print(f"❌ Error converting markdown to HTML: {e}")
            # Fallback to plain text with basic formatting
            return f"<html><body><pre>{content}</pre>{self.get_affiliate_cta()}</body></html>"

    def get_affiliate_cta(self) -> str:
        """Generate affiliate CTA block with UTM tracking"""
        utm_params = "?utm_source=substack&utm_medium=email&utm_campaign=daily_insights"

        cta_html = f"""
        <div class="cta-section">
            <h3>🚀 Ready to Transform Your SaaS Strategy?</h3>
            <p>Get exclusive access to our <strong>SaaS Market Intelligence Platform</strong> and discover untapped opportunities before your competitors do.</p>

            <a href="https://saasgrowthdispatch.com/intelligence{utm_params}" class="cta-button">
                🔍 Start Free Analysis
            </a>

            <a href="https://saasgrowthdispatch.com/premium{utm_params}" class="cta-button">
                💎 Upgrade to Premium
            </a>

            <p><small>
                <a href="https://saasgrowthdispatch.com/case-studies{utm_params}">📊 View Success Stories</a> |
                <a href="https://saasgrowthdispatch.com/tools{utm_params}">🛠️ Free Tools</a> |
                <a href="https://saasgrowthdispatch.com/newsletter{utm_params}">📧 Daily Newsletter</a>
            </small></p>

            <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
            <p><em>What hidden opportunities have you discovered in your market? Reply and share your insights!</em></p>
        </div>
        """

        return cta_html

    def create_substack_email(self, report_path: Path) -> MIMEMultipart:
        """Create email message for Substack publishing"""

        # Read the markdown content
        try:
            with open(report_path, encoding="utf-8") as f:
                markdown_content = f.read()
        except Exception as e:
            raise Exception(f"Error reading report file: {e}")

        # Extract title and convert to HTML
        title = self.extract_title_from_markdown(markdown_content)
        html_content = self.convert_markdown_to_html(markdown_content)

        # Create email message
        today = datetime.now().strftime("%B %d, %Y")
        subject = f"{title} - SaaS Pain Point Report ({today})"

        msg = MIMEMultipart("alternative")
        msg["From"] = self.sender_email
        msg["To"] = self.substack_email
        msg["Subject"] = subject

        # Add HTML content
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        print(f"✅ Created Substack email with subject: {subject}")
        return msg

    def send_to_substack(self, msg: MIMEMultipart) -> bool:
        """Send email to Substack for publishing"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS
            server.login(self.sender_email, self.sender_password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully to Substack: {self.substack_email}")
            return True

        except Exception as e:
            print(f"❌ Error sending to Substack: {e}")
            return False

    def log_substack_result(
        self, report_path: Path, subject: str, success: bool, error_msg: str = ""
    ):
        """Log Substack publishing result to CSV"""

        # Create CSV header if file doesn't exist
        if not self.substack_log_file.exists():
            with open(self.substack_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "subject",
                        "substack_email",
                        "status",
                        "error_message",
                    ]
                )

        # Log the result
        with open(self.substack_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    subject,
                    self.substack_email,
                    "SUCCESS" if success else "FAILED",
                    error_msg,
                ]
            )

        print(f"📝 Substack result logged to {self.substack_log_file}")

    def run(self) -> bool:
        """Execute the complete Substack publishing pipeline"""
        print("🚀 Starting Substack publishing...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            self.log_substack_result(Path("none"), "", False, "No report file found")
            return False

        # Step 2: Create Substack email
        print("\n📝 Creating Substack email...")
        try:
            msg = self.create_substack_email(report_path)
            subject = msg["Subject"]
        except Exception as e:
            error_msg = f"Error creating email: {e}"
            print(f"❌ {error_msg}")
            self.log_substack_result(report_path, "", False, error_msg)
            return False

        # Step 3: Send to Substack
        print("\n📤 Publishing to Substack...")
        success = self.send_to_substack(msg)

        # Step 4: Log result
        print("\n📝 Logging result...")
        self.log_substack_result(
            report_path, subject, success, "" if success else "SMTP send failed"
        )

        if success:
            print("\n✅ Substack publishing complete!")
            print(f"📧 Check your Substack dashboard for the new post: {subject}")
            return True
        else:
            print("\n❌ Substack publishing failed")
            return False


def main():
    publisher = SubstackPublisher()
    success = publisher.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
