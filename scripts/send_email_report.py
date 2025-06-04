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
        """Find the latest daily report file with improved date detection"""
        reports_dir = Path("reports")

        if not reports_dir.exists():
            print("❌ Reports directory does not exist")
            return None

        today = datetime.now().strftime("%Y-%m-%d")
        print(f"🔍 Looking for reports for date: {today}")

        # Try today's report first
        todays_report = reports_dir / f"insight_daily_{today}.md"
        if todays_report.exists():
            print(f"📄 Found today's report: {todays_report}")
            return todays_report

        # Try yesterday's report (in case today's hasn't been generated yet)
        from datetime import timedelta

        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterdays_report = reports_dir / f"insight_daily_{yesterday}.md"
        if yesterdays_report.exists():
            print(f"📄 Found yesterday's report: {yesterdays_report}")
            return yesterdays_report

        # Find the most recent daily report by modification time
        daily_reports = list(reports_dir.glob("insight_daily_*.md"))
        if daily_reports:
            # Sort by modification time (most recent first)
            daily_reports.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_report = daily_reports[0]
            print(f"📄 Found latest daily report by mtime: {latest_report}")
            return latest_report

        # Fallback to weekly digest PDFs
        weekly_pdfs = list(reports_dir.glob("weekly_digest_*.pdf"))
        if weekly_pdfs:
            weekly_pdfs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_pdf = weekly_pdfs[0]
            print(f"📄 Fallback to latest weekly PDF: {latest_pdf}")
            return latest_pdf

        # Final fallback to any PDF report
        pdf_report = reports_dir / "SaaS_Pain_Point_Report_latest.pdf"
        if pdf_report.exists():
            print(f"📄 Fallback to static PDF report: {pdf_report}")
            return pdf_report

        print("❌ No reports found in any format")
        return None

    def extract_summary_from_markdown(
        self, report_path: Path, max_lines: int = 8
    ) -> str:
        """Extract executive summary from markdown report with enhanced parsing"""
        try:
            with open(report_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Extract report metadata
            report_date = "Unknown"

            for line in lines[:10]:  # Check first 10 lines for metadata
                if "**Data Period:**" in line:
                    report_date = line.split("**Data Period:**")[1].strip()

            # Find key insights from multiple sections
            summary_lines = []
            key_themes = []
            pain_points = []

            # Look for Weekly Data Summary section
            in_summary = False
            in_themes = False
            in_pain_points = False

            for line in lines:
                line = line.strip()

                # Weekly Data Summary section
                if "📊 Weekly Data Summary" in line or "## 📊" in line:
                    in_summary = True
                    continue
                elif "🎯 Key Themes Analysis" in line or "## 🎯" in line:
                    in_summary = False
                    in_themes = True
                    continue
                elif "💡 Underserved SaaS Niches" in line or "## 💡" in line:
                    in_themes = False
                    continue
                elif line.startswith("##"):
                    in_summary = False
                    in_themes = False
                    in_pain_points = False

                # Extract pain points from summary
                if in_summary and "**Recent Pain Points Identified:**" in line:
                    in_pain_points = True
                    continue
                elif in_pain_points and line.startswith("- **"):
                    # Extract pain point
                    if "|" in line:
                        pain_point = line.split("|")[1].strip()
                        pain_points.append(pain_point)
                    if len(pain_points) >= 3:
                        in_pain_points = False

                # Extract key themes
                elif in_themes and line.startswith("### "):
                    theme_name = (
                        line.replace("### ", "")
                        .replace("1. ", "")
                        .replace("2. ", "")
                        .replace("3. ", "")
                        .replace("4. ", "")
                    )
                    if theme_name and len(key_themes) < 3:
                        key_themes.append(theme_name)

                # Extract trending queries
                elif "**Trending Queries:**" in line:
                    trending = line.split("**Trending Queries:**")[1].strip()
                    if trending and trending != "N/A":
                        summary_lines.append(f"Trending: {trending[:100]}...")

            # Build comprehensive summary
            summary_parts = []

            if report_date != "Unknown":
                summary_parts.append(f"📅 Report Period: {report_date}")

            if pain_points:
                summary_parts.append(
                    f"🔥 Key Pain Points: {', '.join(pain_points[:3])}"
                )

            if key_themes:
                summary_parts.append(f"🎯 Major Themes: {', '.join(key_themes[:2])}")

            # Add trending queries if found
            for line in summary_lines:
                if "Trending:" in line:
                    summary_parts.append(line)
                    break

            # If we have good summary parts, use them
            if summary_parts:
                final_summary = "\n".join(summary_parts[:max_lines])
            else:
                # Fallback: extract first meaningful content
                meaningful_lines = []
                for line in lines:
                    line = line.strip()
                    if (
                        line
                        and not line.startswith("#")
                        and not line.startswith("*")
                        and not line.startswith("**Generated:**")
                        and not line.startswith("---")
                        and len(line) > 20
                    ):
                        meaningful_lines.append(line)
                        if len(meaningful_lines) >= max_lines:
                            break
                final_summary = "\n".join(meaningful_lines[:max_lines])

            return (
                final_summary
                if final_summary
                else "Latest SaaS market insights and pain point analysis."
            )

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

    def log_email_result(
        self,
        report_path: Path,
        success: bool,
        error_msg: str = "",
        summary_length: int = 0,
    ):
        """Log email sending result to CSV with enhanced details"""

        # Create CSV header if file doesn't exist
        if not self.email_log_file.exists():
            with open(self.email_log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "report_file",
                        "report_date",
                        "recipient",
                        "status",
                        "summary_length",
                        "file_size_kb",
                        "error_message",
                    ]
                )

        # Extract date from filename
        report_date = "unknown"
        if "insight_daily_" in report_path.name:
            try:
                date_part = report_path.name.replace("insight_daily_", "").replace(
                    ".md", ""
                )
                # Validate date format
                datetime.strptime(date_part, "%Y-%m-%d")
                report_date = date_part
            except ValueError:
                report_date = "invalid_format"
        elif "weekly_digest_" in report_path.name:
            try:
                date_part = report_path.name.replace("weekly_digest_", "").replace(
                    ".pdf", ""
                )
                datetime.strptime(date_part, "%Y-%m-%d")
                report_date = date_part
            except ValueError:
                report_date = "weekly_unknown"

        # Get file size
        file_size_kb = 0
        try:
            if report_path.exists():
                file_size_kb = round(report_path.stat().st_size / 1024, 2)
        except OSError:
            pass

        # Log the result
        with open(self.email_log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    report_path.name,
                    report_date,
                    self.recipient_email,
                    "SUCCESS" if success else "FAILED",
                    summary_length,
                    file_size_kb,
                    error_msg,
                ]
            )

        print(
            f"📝 Email result logged to {self.email_log_file} (Date: {report_date}, Size: {file_size_kb}KB)"
        )

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
        summary_length = (
            len(self.extract_summary_from_markdown(report_path))
            if report_path.suffix == ".md"
            else 0
        )
        self.log_email_result(
            report_path, success, "" if success else "SMTP send failed", summary_length
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
