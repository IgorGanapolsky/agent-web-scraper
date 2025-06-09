#!/usr/bin/env python3
"""
Weekly Report Summarizer
Generates comprehensive weekly digest PDF from daily insight reports
"""

import argparse
import csv
import os
import smtplib
from datetime import datetime, timedelta
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

load_dotenv()


class WeeklyReportSummarizer:
    def __init__(self, week_ending_date: Optional[str] = None):
        """
        Initialize weekly report summarizer

        Args:
            week_ending_date: Date in YYYY-MM-DD format (defaults to current Sunday)
        """
        if week_ending_date:
            self.week_ending = datetime.strptime(week_ending_date, "%Y-%m-%d")
        else:
            # Default to most recent Sunday
            today = datetime.now()
            days_since_sunday = today.weekday() + 1  # Monday = 0, Sunday = 6
            if days_since_sunday == 7:  # Today is Sunday
                self.week_ending = today
            else:
                self.week_ending = today - timedelta(days=days_since_sunday)

        # Calculate week start (Monday)
        self.week_start = self.week_ending - timedelta(days=6)

        # Setup paths
        self.weekly_buffer_dir = Path("weekly_buffer")
        self.weekly_buffer_dir.mkdir(exist_ok=True)

        self.reports_dir = Path("reports")
        self.logs_dir = Path("logs")
        self.logs_dir.mkdir(exist_ok=True)

        # Email configuration
        self.smtp_server = "smtp.zoho.com"
        self.smtp_port = 587
        self.sender_email = "support@saasgrowthdispatch.com"
        self.sender_password = os.getenv("ZOHO_APP_PASSWORD", "Rockland25&*")
        self.recipient_email = "support@saasgrowthdispatch.com"

        # Output files
        week_str = self.week_ending.strftime("%Y-%m-%d")
        self.pdf_filename = f"weekly_digest_{week_str}.pdf"
        self.pdf_path = self.reports_dir / self.pdf_filename

        print(
            f"📅 Processing week: {self.week_start.strftime('%Y-%m-%d')} to {self.week_ending.strftime('%Y-%m-%d')}"
        )

    def copy_daily_reports_to_buffer(self) -> list[Path]:
        """Copy this week's daily reports to weekly buffer folder"""
        copied_files = []

        # Generate list of dates for this week
        current_date = self.week_start
        while current_date <= self.week_ending:
            date_str = current_date.strftime("%Y-%m-%d")
            source_file = self.reports_dir / f"insight_daily_{date_str}.md"
            target_file = self.weekly_buffer_dir / f"insight_daily_{date_str}.md"

            if source_file.exists():
                # Copy file to buffer
                import shutil

                shutil.copy2(source_file, target_file)
                copied_files.append(target_file)
                print(f"📄 Copied: {source_file.name} → {target_file.name}")
            else:
                print(f"⚠️  Missing: {source_file.name}")

            current_date += timedelta(days=1)

        print(f"✅ Copied {len(copied_files)} daily reports to buffer")
        return copied_files

    def parse_daily_reports(self, report_files: list[Path]) -> dict:
        """Parse daily reports and extract key information"""
        weekly_data = {
            "dates": [],
            "pain_points": [],
            "themes": [],
            "niches": [],
            "niche_opportunities": [],
            "lead_magnets": [],
            "trending_queries": [],
        }

        for report_file in sorted(report_files):
            try:
                with open(report_file, encoding="utf-8") as f:
                    content = f.read()

                # Extract date from filename
                date_str = report_file.stem.replace("insight_daily_", "")
                weekly_data["dates"].append(date_str)

                lines = content.split("\n")

                # Extract pain points
                daily_pain_points = []
                for i, line in enumerate(lines):
                    if "**Recent Pain Points Identified:**" in line:
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("**"):
                            if lines[j].startswith("- **") and ":**" in lines[j]:
                                pain_point = (
                                    lines[j].split(":**")[1].strip()
                                    if ":**" in lines[j]
                                    else lines[j].strip()
                                )
                                daily_pain_points.append(pain_point)
                            j += 1
                        break

                weekly_data["pain_points"].extend(daily_pain_points)

                # Extract themes
                for i, line in enumerate(lines):
                    if "## 🎯 Key Themes Analysis" in line:
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("##"):
                            if lines[j].startswith("### "):
                                theme_name = (
                                    lines[j]
                                    .replace("### ", "")
                                    .replace("1. ", "")
                                    .replace("2. ", "")
                                    .replace("3. ", "")
                                    .replace("4. ", "")
                                )
                                if j + 1 < len(lines) and lines[j + 1].strip():
                                    theme_desc = lines[j + 1].strip()
                                    weekly_data["themes"].append(
                                        {
                                            "name": theme_name,
                                            "description": theme_desc,
                                            "date": date_str,
                                        }
                                    )
                            j += 1
                        break

                # Extract niche opportunities
                for i, line in enumerate(lines):
                    if "🔍 Niche Saturation Check" in line:
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith("##"):
                            if "🎯" in line and j < len(lines) - 2:
                                keyword = (
                                    lines[j].replace("### 🎯 ", "").replace('"', "")
                                )
                                if (
                                    j + 1 < len(lines)
                                    and "Niche Opportunity Score" in lines[j + 1]
                                ):
                                    score_line = lines[j + 1]
                                    weekly_data["niche_opportunities"].append(
                                        {
                                            "keyword": keyword,
                                            "score_line": score_line,
                                            "date": date_str,
                                        }
                                    )
                            j += 1
                        break

                # Extract trending queries
                for line in lines:
                    if "**Trending Queries:**" in line:
                        queries = line.split("**Trending Queries:**")[1].strip()
                        if queries:
                            weekly_data["trending_queries"].extend(
                                [q.strip() for q in queries.split(",")]
                            )

            except Exception as e:
                print(f"❌ Error parsing {report_file}: {e}")

        # Remove duplicates and clean data
        weekly_data["pain_points"] = list(
            {p for p in weekly_data["pain_points"] if p and p != "N/A"}
        )
        weekly_data["trending_queries"] = list(
            {q for q in weekly_data["trending_queries"] if q and q != "N/A"}
        )

        print(
            f"📊 Parsed data: {len(weekly_data['themes'])} themes, {len(weekly_data['pain_points'])} pain points"
        )
        return weekly_data

    def generate_executive_summary(self, weekly_data: dict) -> str:
        """Generate executive summary from weekly data"""
        total_days = len(weekly_data["dates"])
        total_themes = len(weekly_data["themes"])
        total_pain_points = len(weekly_data["pain_points"])

        # Top themes by frequency
        theme_names = [theme["name"] for theme in weekly_data["themes"]]
        from collections import Counter

        top_themes = Counter(theme_names).most_common(3)

        # High opportunity niches
        high_opportunity_niches = [
            niche
            for niche in weekly_data["niche_opportunities"]
            if "🔥 High" in niche["score_line"]
        ]

        summary = f"""
**EXECUTIVE SUMMARY**

This week's AI-powered market analysis covered {total_days} days of SaaS intelligence, identifying {total_themes} key market themes and {total_pain_points} distinct pain points across the ecosystem.

**KEY FINDINGS:**
• {len(high_opportunity_niches)} HIGH opportunity niches discovered with minimal competition
• {len(top_themes)} dominant themes emerged across multiple days of analysis
• {len(weekly_data["trending_queries"])} trending search queries indicating market demand

**TOP MARKET THEMES:**
"""

        for i, (theme, count) in enumerate(top_themes, 1):
            summary += f"{i}. {theme} (appeared {count}x this week)\n"

        if high_opportunity_niches:
            summary += "\n**HIGHEST OPPORTUNITY NICHES:**\n"
            for niche in high_opportunity_niches[:3]:
                summary += f"• {niche['keyword']} ({niche['date']})\n"

        summary += """
**MARKET INTELLIGENCE IMPACT:**
Our analysis shows clear patterns in SaaS pain points, with integration challenges and AI adoption barriers representing the most consistent themes. These insights provide actionable direction for product development and market entry strategies.
        """

        return summary.strip()

    def create_weekly_pdf(self, weekly_data: dict) -> Path:
        """Create comprehensive weekly digest PDF"""
        doc = SimpleDocTemplate(str(self.pdf_path), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Title"],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor("#2c3e50"),
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading1"],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.HexColor("#34495e"),
        )

        subheading_style = ParagraphStyle(
            "CustomSubHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.HexColor("#7f8c8d"),
        )

        # Title Page
        week_range = f"{self.week_start.strftime('%B %d')} - {self.week_ending.strftime('%B %d, %Y')}"
        story.append(Paragraph("🚀 SaaS Growth Dispatch", title_style))
        story.append(Paragraph("Weekly Market Intelligence Digest", styles["Heading2"]))
        story.append(Paragraph(f"Week of {week_range}", styles["Heading3"]))
        story.append(Spacer(1, 0.5 * inch))

        # Executive Summary
        summary = self.generate_executive_summary(weekly_data)
        story.append(Paragraph("Executive Summary", heading_style))
        story.append(Paragraph(summary.replace("\n", "<br/>"), styles["Normal"]))
        story.append(PageBreak())

        # Daily Analysis Overview
        story.append(Paragraph("📊 Daily Analysis Overview", heading_style))

        # Create daily summary table
        daily_data = [["Date", "Key Pain Points", "Top Opportunity"]]

        for date in weekly_data["dates"]:
            # Find pain points for this date
            date_pain_points = [
                theme["description"]
                for theme in weekly_data["themes"]
                if theme["date"] == date
            ]
            pain_point_text = (
                date_pain_points[0][:50] + "..." if date_pain_points else "N/A"
            )

            # Find top opportunity for this date
            date_opportunities = [
                niche
                for niche in weekly_data["niche_opportunities"]
                if niche["date"] == date
            ]
            opportunity_text = (
                date_opportunities[0]["keyword"] if date_opportunities else "N/A"
            )

            daily_data.append(
                [
                    datetime.strptime(date, "%Y-%m-%d").strftime("%m/%d"),
                    pain_point_text,
                    opportunity_text,
                ]
            )

        daily_table = Table(daily_data, colWidths=[1 * inch, 3 * inch, 2 * inch])
        daily_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8f9fa")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#ddd")),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )

        story.append(daily_table)
        story.append(Spacer(1, 0.3 * inch))

        # Market Themes Analysis
        story.append(Paragraph("🎯 Recurring Market Themes", heading_style))

        from collections import Counter

        theme_names = [theme["name"] for theme in weekly_data["themes"]]
        theme_counts = Counter(theme_names)

        for theme_name, count in theme_counts.most_common(5):
            story.append(Paragraph(f"{theme_name}", subheading_style))

            # Get description from first occurrence
            theme_desc = next(
                (
                    theme["description"]
                    for theme in weekly_data["themes"]
                    if theme["name"] == theme_name
                ),
                "No description available",
            )

            story.append(
                Paragraph(f"Appeared {count} time(s) this week", styles["Normal"])
            )
            story.append(Paragraph(theme_desc, styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        # Niche Opportunities Section
        story.append(PageBreak())
        story.append(Paragraph("💡 Niche Opportunity Analysis", heading_style))

        # Group opportunities by score
        high_opps = [
            n
            for n in weekly_data["niche_opportunities"]
            if "🔥 High" in n["score_line"]
        ]
        moderate_opps = [
            n
            for n in weekly_data["niche_opportunities"]
            if "⚠️ Moderate" in n["score_line"]
        ]

        if high_opps:
            story.append(Paragraph("🔥 High Opportunity Niches", subheading_style))
            for opp in high_opps:
                story.append(
                    Paragraph(
                        f"• <b>{opp['keyword']}</b> (discovered {opp['date']})",
                        styles["Normal"],
                    )
                )
            story.append(Spacer(1, 0.2 * inch))

        if moderate_opps:
            story.append(Paragraph("⚠️ Moderate Opportunity Niches", subheading_style))
            for opp in moderate_opps[:5]:  # Limit to top 5
                story.append(
                    Paragraph(
                        f"• <b>{opp['keyword']}</b> (discovered {opp['date']})",
                        styles["Normal"],
                    )
                )
            story.append(Spacer(1, 0.2 * inch))

        # Pain Points Section
        story.append(Paragraph("🔍 Pain Point Trends", heading_style))

        pain_point_counter = Counter(weekly_data["pain_points"])
        top_pain_points = pain_point_counter.most_common(10)

        pain_data = [["Pain Point", "Frequency"]]
        for pain_point, count in top_pain_points:
            pain_data.append(
                [
                    pain_point[:60] + "..." if len(pain_point) > 60 else pain_point,
                    str(count),
                ]
            )

        pain_table = Table(pain_data, colWidths=[4 * inch, 1 * inch])
        pain_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e74c3c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fdf2f2")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#ddd")),
                    ("FONTSIZE", (0, 1), (-1, -1), 10),
                ]
            )
        )

        story.append(pain_table)

        # Footer
        story.append(PageBreak())
        story.append(Paragraph("📈 Weekly Intelligence Summary", heading_style))
        story.append(
            Paragraph(
                f"""
This weekly digest represents {len(weekly_data['dates'])} days of comprehensive SaaS market analysis,
powered by AI-driven insights and real-time market intelligence. Our analysis identified
{len(weekly_data['niche_opportunities'])} distinct market opportunities and tracked
{len(weekly_data['pain_points'])} unique pain points across the SaaS ecosystem.
        """,
                styles["Normal"],
            )
        )

        story.append(Spacer(1, 0.3 * inch))
        story.append(
            Paragraph(
                "🤖 Generated by SaaS Growth Dispatch Intelligence Platform",
                styles["Normal"],
            )
        )
        story.append(
            Paragraph(
                f"Report Date: {datetime.now().strftime('%B %d, %Y')}", styles["Normal"]
            )
        )

        # Build PDF
        doc.build(story)
        print(f"📄 Weekly digest PDF created: {self.pdf_path}")
        return self.pdf_path

    def email_weekly_digest(self, pdf_path: Path) -> bool:
        """Email the weekly digest PDF"""
        try:
            # Create email message
            week_range = f"{self.week_start.strftime('%B %d')} - {self.week_ending.strftime('%B %d, %Y')}"

            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Subject"] = f"📈 Weekly SaaS Intelligence Digest - {week_range}"

            # Email body
            body = f"""
📈 SaaS Growth Dispatch - Weekly Intelligence Digest
{week_range}

---

EXECUTIVE SUMMARY:

This week's comprehensive market analysis is attached as a PDF digest. Our AI-powered intelligence platform identified key trends, market opportunities, and pain points across the SaaS ecosystem.

KEY HIGHLIGHTS:
• Market opportunity analysis with niche scoring
• Pain point trend identification and frequency analysis
• Competitive landscape insights
• Actionable intelligence for strategic decision-making

📊 Full weekly digest is attached for detailed analysis.

Best regards,
SaaS Growth Dispatch Intelligence Team
support@saasgrowthdispatch.com

---
🤖 Automated weekly delivery | Weekly Intelligence Platform
            """.strip()

            # Add body to email
            msg.attach(MIMEText(body, "plain"))

            # Attach PDF
            with open(pdf_path, "rb") as f:
                pdf_attachment = MIMEApplication(f.read(), _subtype="pdf")
                pdf_attachment.add_header(
                    "Content-Disposition", "attachment", filename=pdf_path.name
                )
                msg.attach(pdf_attachment)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.send_message(msg)
            server.quit()

            print(f"✅ Weekly digest emailed successfully to {self.recipient_email}")
            return True

        except Exception as e:
            print(f"❌ Error sending weekly digest email: {e}")
            return False

    def log_weekly_digest(self, success: bool, pdf_path: Optional[Path] = None):
        """Log weekly digest generation results"""
        log_file = self.logs_dir / "weekly_digests.csv"

        # Create CSV header if file doesn't exist
        if not log_file.exists():
            with open(log_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        "timestamp",
                        "week_start",
                        "week_end",
                        "pdf_filename",
                        "reports_processed",
                        "email_sent",
                        "status",
                    ]
                )

        # Log the result
        with open(log_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    datetime.now().isoformat(),
                    self.week_start.strftime("%Y-%m-%d"),
                    self.week_ending.strftime("%Y-%m-%d"),
                    pdf_path.name if pdf_path else "N/A",
                    len(list(self.weekly_buffer_dir.glob("*.md"))),
                    success,
                    "SUCCESS" if success else "FAILED",
                ]
            )

        print(f"📝 Weekly digest logged to {log_file}")

    def run(self) -> bool:
        """Execute the complete weekly digest pipeline"""
        print("🚀 Starting weekly digest generation...")

        try:
            # Step 1: Copy daily reports to buffer
            print("\n📁 Copying daily reports to weekly buffer...")
            report_files = self.copy_daily_reports_to_buffer()

            if not report_files:
                print("❌ No daily reports found for this week")
                self.log_weekly_digest(False)
                return False

            # Step 2: Parse daily reports
            print("\n📊 Parsing daily reports...")
            weekly_data = self.parse_daily_reports(report_files)

            # Step 3: Generate PDF digest
            print("\n📄 Generating weekly PDF digest...")
            pdf_path = self.create_weekly_pdf(weekly_data)

            # Step 4: Email digest
            print("\n📧 Emailing weekly digest...")
            email_success = self.email_weekly_digest(pdf_path)

            # Step 5: Log results
            print("\n📝 Logging results...")
            self.log_weekly_digest(email_success, pdf_path)

            if email_success:
                print("\n✅ Weekly digest generation complete!")
                print(f"📄 PDF: {pdf_path}")
                print(f"📧 Emailed to: {self.recipient_email}")
                return True
            else:
                print("\n⚠️  PDF generated but email failed")
                return False

        except Exception as e:
            print(f"\n❌ Weekly digest generation failed: {e}")
            self.log_weekly_digest(False)
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate weekly SaaS intelligence digest"
    )
    parser.add_argument(
        "--week-ending",
        help="Week ending date in YYYY-MM-DD format (defaults to most recent Sunday)",
    )

    args = parser.parse_args()

    summarizer = WeeklyReportSummarizer(week_ending_date=args.week_ending)
    success = summarizer.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
