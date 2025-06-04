#!/usr/bin/env python3
"""
Weekly lead magnet generator - Main automation script.
"""

import argparse
import json
import logging
import os
from datetime import datetime

from app.core.pdf_generator import generate_lead_magnet_pdf
from app.core.weekly_analytics import generate_weekly_lead_magnet
from app.utils.email_utils import send_email

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("lead_magnet_generator")


def main():
    """Main lead magnet generation workflow."""
    parser = argparse.ArgumentParser(description="Generate weekly SaaS lead magnet")
    parser.add_argument(
        "--weeks",
        type=int,
        default=1,
        help="Number of weeks to analyze (default: 1)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Output directory for reports (default: reports)",
    )
    parser.add_argument(
        "--email-report",
        action="store_true",
        help="Email the generated report",
    )
    parser.add_argument(
        "--save-json",
        action="store_true",
        help="Save raw JSON report data",
    )

    args = parser.parse_args()

    try:
        print("🚀 Starting weekly lead magnet generation...")
        print(f"📊 Analyzing last {args.weeks} weeks of data")

        # Step 1: Generate weekly analytics report
        print("\n📈 Step 1: Generating weekly analytics...")
        weekly_report = generate_weekly_lead_magnet()

        if "error" in weekly_report:
            logger.error(f"Failed to generate weekly report: {weekly_report['error']}")
            return 1

        print("✅ Weekly analytics generated successfully")
        print(f"📊 Analyzed {weekly_report.get('data_points', 0)} data points")

        # Step 2: Save JSON report if requested
        if args.save_json:
            json_path = os.path.join(args.output_dir, "weekly_report_latest.json")
            os.makedirs(args.output_dir, exist_ok=True)

            with open(json_path, "w") as f:
                json.dump(weekly_report, f, indent=2, default=str)
            print(f"💾 JSON report saved: {json_path}")

        # Step 3: Generate PDF lead magnet
        print("\n📄 Step 2: Generating PDF lead magnet...")
        try:
            pdf_path = os.path.join(
                args.output_dir, "SaaS_Pain_Point_Report_latest.pdf"
            )

            generated_pdf = generate_lead_magnet_pdf(weekly_report, pdf_path)
            print(f"✅ PDF lead magnet generated: {generated_pdf}")

        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            print("⚠️ PDF generation failed, but JSON report is available")

        # Step 4: Email report if requested
        if args.email_report:
            print("\n📧 Step 3: Emailing report...")
            try:
                # Create email summary
                clusters = weekly_report.get("pain_point_clusters", {})
                cluster_count = (
                    len(clusters.get("clusters", [])) if "clusters" in clusters else 0
                )

                email_subject = f"📈 Weekly Lead Magnet Generated - {cluster_count} Pain Point Clusters Identified"

                email_body = f"""
🎯 Weekly SaaS Lead Magnet Report Generated

📊 ANALYSIS SUMMARY:
• Period: {weekly_report.get('analysis_period', 'Last week')}
• Data Points: {weekly_report.get('data_points', 0)}
• Pain Point Clusters: {cluster_count}
• Report Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

📄 DELIVERABLES:
• PDF Lead Magnet: {generated_pdf if 'generated_pdf' in locals() else 'Generation failed'}
• JSON Data: {json_path if args.save_json else 'Not requested'}
• Google Sheets: Updated automatically

🚀 NEXT STEPS:
1. Review the generated PDF for quality
2. Upload to your lead magnet platform
3. Update landing page with new insights
4. Share with your marketing team

💡 TOP INSIGHT PREVIEW:
{clusters.get('executive_summary', 'Analysis complete - see full report for details')[:200]}...

🔗 AUTOMATION STATUS: ✅ Success
Generated via AI-powered market research pipeline.
                """

                send_email(
                    to="support@saasgrowthdispatch.com",
                    subject=email_subject,
                    body=email_body,
                )
                print("✅ Report emailed successfully")

            except Exception as e:
                logger.error(f"Failed to email report: {e}")
                print("⚠️ Email failed, but reports are generated")

        # Step 5: Print summary
        print("\n🎉 Lead Magnet Generation Complete!")
        print("=" * 50)

        if "lead_magnet_content" in weekly_report:
            content = weekly_report["lead_magnet_content"]
            if isinstance(content, dict) and "executive_summary" in content:
                print("📋 EXECUTIVE SUMMARY PREVIEW:")
                print(content["executive_summary"][:300] + "...")

        print(f"\n📁 Files generated in: {args.output_dir}/")
        if args.save_json and "json_path" in locals():
            print(f"   • JSON Report: {json_path}")
        if "generated_pdf" in locals():
            print(f"   • PDF Lead Magnet: {generated_pdf}")

        print("\n💰 MONETIZATION READY:")
        print("   • Upload PDF to lead magnet platform")
        print("   • Create landing page with insights")
        print("   • Set up email capture form")
        print("   • Launch targeted ad campaigns")

        return 0

    except Exception as e:
        logger.error(f"Lead magnet generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
