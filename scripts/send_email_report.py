#!/usr/bin/env python3
"""
Email Report Sender
Sends daily Markdown reports and/or weekly PDFs via SMTP
"""

import csv
import os
import smtplib
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class EmailReportSender:
    def __init__(self):
        self.smtp_server = "smtp.zoho.com"
        self.smtp_port = 587
        self.sender_email = "support@saasgrowthdispatch.com"
        self.sender_password = os.getenv("ZOHO_APP_PASSWORD", "Rockland25&*")
        self.recipient_email = "support@saasgrowthdispatch.com"

        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)
        self.email_log_file = self.logs_dir / "email_log.csv"

        if not self.sender_password:
            print("⚠️  ZOHO_APP_PASSWORD not found in environment, using default")

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

        # Fallback to weekly PDF
        pdf_report = reports_dir / "SaaS_Pain_Point_Report_latest.pdf"
        if pdf_report.exists():
            print(f"📄 Fallback to PDF report: {pdf_report}")
            return pdf_report

        print("❌ No reports found")
        return None

    def extract_summary_from_markdown(
        self, report_path: Path, max_lines: int = 8
    ) -> str:
        """Extract executive summary from markdown report"""
        try:
            with open(report_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Find the summary section or use first few lines
            summary_lines = []
            in_summary = False

            for line in lines:
                # Look for summary section
                if "📊 Weekly Data Summary" in line or "## 📊" in line:
                    in_summary = True
                    continue
                elif in_summary and line.startswith("##"):
                    break
                elif in_summary and line.strip():
                    summary_lines.append(line.strip())
                    if len(summary_lines) >= max_lines:
                        break

            # If no summary section found, use first meaningful lines
            if not summary_lines:
                for line in lines:
                    if (
                        line.strip()
                        and not line.startswith("#")
                        and not line.startswith("*")
                    ):
                        summary_lines.append(line.strip())
                        if len(summary_lines) >= max_lines:
                            break

            return "\n".join(summary_lines[:max_lines])

        except Exception as e:
            print(f"❌ Error extracting summary: {e}")
            return "Latest SaaS market insights and pain point analysis."

    def create_email_message(self, report_path: Path) -> MIMEMultipart:
        """Create email message with report attachment"""
        today = datetime.now().strftime("%B %d, %Y")

        # Create multipart message
        msg = MIMEMultipart()
        msg["From"] = self.sender_email
        msg["To"] = self.recipient_email
        msg["Subject"] = f"📈 SaaS Insights Report - {today}"

        # Extract summary for email body
        if report_path.suffix == ".md":
            summary = self.extract_summary_from_markdown(report_path)
            file_type = "Daily Insights Report"
        else:
            summary = "Weekly comprehensive SaaS pain point analysis and market opportunities."
            file_type = "Weekly PDF Report"

        # Create email body
        body = f"""
📈 SaaS Growth Dispatch - {file_type}
{today}

---

EXECUTIVE SUMMARY:

{summary}

---

📊 Full report is attached for detailed analysis.

Best regards,
SaaS Growth Dispatch Team
support@saasgrowthdispatch.com

---
🤖 Automated daily delivery | Unsubscribe: support@saasgrowthdispatch.com
        """.strip()

        # Add body to email
        msg.attach(MIMEText(body, "plain"))

        # Attach the report file
        try:
            with open(report_path, "rb") as f:
                attachment = MIMEApplication(f.read())
                attachment.add_header(
                    "Content-Disposition", "attachment", filename=report_path.name
                )
                msg.attach(attachment)
            print(f"✅ Attached file: {report_path.name}")
        except Exception as e:
            print(f"❌ Error attaching file: {e}")

        return msg

    def send_email(self, msg: MIMEMultipart) -> bool:
        """Send email via SMTP"""
        try:
            # Create SMTP session
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # Enable TLS
            server.login(self.sender_email, self.sender_password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"✅ Email sent successfully to {self.recipient_email}")
            return True

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def log_email_result(self, report_path: Path, success: bool, error_msg: str = ""):
        """Log email sending result to CSV"""

        # Create CSV header if file doesn't exist
        if not self.email_log_file.exists():
            with open(self.email_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["timestamp", "report_file", "recipient", "status", "error_message"]
                )

        # Log the result
        with open(self.email_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    self.recipient_email,
                    "SUCCESS" if success else "FAILED",
                    error_msg,
                ]
            )

        print(f"📝 Email result logged to {self.email_log_file}")

    def run(self) -> bool:
        """Execute the complete email sending pipeline"""
        print("🚀 Starting email report delivery...")

        # Step 1: Find the latest report
        print("\n📊 Finding latest report...")
        report_path = self.find_latest_report()
        if not report_path:
            self.log_email_result(Path("none"), False, "No report file found")
            return False

        # Step 2: Create email message
        print("\n📧 Creating email message...")
        try:
            msg = self.create_email_message(report_path)
        except Exception as e:
            error_msg = f"Error creating email: {e}"
            print(f"❌ {error_msg}")
            self.log_email_result(report_path, False, error_msg)
            return False

        # Step 3: Send email
        print("\n📤 Sending email...")
        success = self.send_email(msg)

        # Step 4: Log result
        print("\n📝 Logging result...")
        self.log_email_result(
            report_path, success, "" if success else "SMTP send failed"
        )

        if success:
            print("\n✅ Email report delivery complete!")
            return True
        else:
            print("\n❌ Email delivery failed")
            return False


def main():
    sender = EmailReportSender()
    success = sender.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
