"""
Professional PDF report generator for lead magnets.
"""

import logging
import os
from datetime import datetime
from typing import Any

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate professional PDF reports from lead magnet content."""

    def __init__(self):
        """Initialize PDF generator with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(
            ParagraphStyle(
                name="CustomTitle",
                parent=self.styles["Title"],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor("#1a365d"),
                alignment=1,  # Center
            )
        )

        # Subtitle style
        self.styles.add(
            ParagraphStyle(
                name="Subtitle",
                parent=self.styles["Heading1"],
                fontSize=16,
                spaceAfter=20,
                textColor=colors.HexColor("#2d3748"),
                leftIndent=0,
            )
        )

        # Insight box style
        self.styles.add(
            ParagraphStyle(
                name="InsightBox",
                parent=self.styles["Normal"],
                fontSize=11,
                spaceAfter=15,
                leftIndent=20,
                rightIndent=20,
                borderWidth=1,
                borderColor=colors.HexColor("#3182ce"),
                borderPadding=10,
                backColor=colors.HexColor("#ebf8ff"),
            )
        )

        # Key finding style
        self.styles.add(
            ParagraphStyle(
                name="KeyFinding",
                parent=self.styles["Normal"],
                fontSize=12,
                spaceAfter=10,
                leftIndent=15,
                bulletIndent=0,
                bulletFontName="Helvetica-Bold",
            )
        )

    def _create_chart(self, clusters: list, chart_type: str = "opportunity") -> str:
        """
        Create a chart from cluster data.

        Args:
            clusters: List of pain point clusters
            chart_type: Type of chart to create

        Returns:
            str: Path to saved chart image
        """
        try:
            fig, ax = plt.subplots(figsize=(10, 6))

            if chart_type == "opportunity":
                # Create opportunity score chart
                cluster_names = [
                    c.get("cluster_name", f"Cluster {i+1}")[:20]
                    for i, c in enumerate(clusters)
                ]

                # Calculate opportunity scores
                scores = []
                for cluster in clusters:
                    market_score = {
                        "Small": 1,
                        "Medium": 2,
                        "Large": 3,
                        "Massive": 4,
                    }.get(cluster.get("market_size", "Medium"), 2)
                    urgency_score = {
                        "Low": 1,
                        "Medium": 2,
                        "High": 3,
                        "Critical": 4,
                    }.get(cluster.get("urgency", "Medium"), 2)
                    revenue_score = {
                        "Low": 1,
                        "Medium": 2,
                        "High": 3,
                        "Massive": 4,
                    }.get(cluster.get("revenue_potential", "Medium"), 2)
                    scores.append(
                        (market_score + urgency_score + revenue_score) / 3 * 25
                    )

                bars = ax.bar(
                    cluster_names,
                    scores,
                    color=["#3182ce", "#38a169", "#d69e2e", "#e53e3e"][: len(clusters)],
                )
                ax.set_ylabel("Opportunity Score")
                ax.set_title(
                    "Business Opportunity Analysis by Pain Point Cluster",
                    fontsize=14,
                    fontweight="bold",
                )
                ax.set_ylim(0, 100)

                # Add value labels on bars
                for bar, score in zip(bars, scores, strict=False):
                    height = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2.0,
                        height + 1,
                        f"{score:.0f}",
                        ha="center",
                        va="bottom",
                        fontweight="bold",
                    )

            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()

            # Save chart
            chart_path = (
                f"reports/chart_{chart_type}_{datetime.now().strftime('%Y%m%d')}.png"
            )
            os.makedirs("reports", exist_ok=True)
            plt.savefig(chart_path, dpi=150, bbox_inches="tight")
            plt.close()

            return chart_path

        except Exception as e:
            logger.error(f"Error creating chart: {e}")
            return None

    def generate_pdf_report(
        self,
        lead_magnet_content: dict[str, str],
        clusters: dict[str, Any],
        output_path: str | None = None,
    ) -> str:
        """
        Generate a professional PDF report.

        Args:
            lead_magnet_content: Content sections for the report
            clusters: Pain point cluster analysis
            output_path: Output file path (optional)

        Returns:
            str: Path to generated PDF
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"reports/SaaS_Pain_Point_Report_{timestamp}.pdf"

        os.makedirs("reports", exist_ok=True)

        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18,
            )

            # Build content
            story = []

            # Cover page
            current_date = datetime.now()
            quarter = f"Q{((current_date.month - 1) // 3) + 1}"
            year = current_date.year

            # Title
            title_text = lead_magnet_content.get(
                "title", f"The {quarter} {year} SaaS Pain Point Report"
            )
            story.append(Paragraph(title_text, self.styles["CustomTitle"]))
            story.append(Spacer(1, 0.5 * inch))

            # Subtitle
            subtitle = "Market Research Insights for SaaS Founders & Product Leaders"
            story.append(Paragraph(subtitle, self.styles["Subtitle"]))
            story.append(Spacer(1, 0.3 * inch))

            # Date and branding
            date_text = f"Generated: {current_date.strftime('%B %d, %Y')}"
            story.append(Paragraph(date_text, self.styles["Normal"]))
            story.append(
                Paragraph(
                    "By: SaaS Growth Dispatch AI Research Team", self.styles["Normal"]
                )
            )
            story.append(PageBreak())

            # Executive Summary
            story.append(Paragraph("Executive Summary", self.styles["Heading1"]))
            story.append(Spacer(1, 0.2 * inch))

            exec_summary = lead_magnet_content.get(
                "executive_summary",
                "Comprehensive analysis of current SaaS market pain points.",
            )
            story.append(Paragraph(exec_summary, self.styles["Normal"]))
            story.append(Spacer(1, 0.3 * inch))

            # Key Findings
            if "key_findings" in lead_magnet_content:
                story.append(Paragraph("Key Findings", self.styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))

                findings = lead_magnet_content["key_findings"]
                if isinstance(findings, str):
                    story.append(Paragraph(findings, self.styles["Normal"]))
                elif isinstance(findings, list):
                    for finding in findings:
                        # Handle both string findings and dict findings
                        if isinstance(finding, dict):
                            finding_text = finding.get("finding", str(finding))
                        else:
                            finding_text = str(finding)
                        story.append(
                            Paragraph(f"• {finding_text}", self.styles["KeyFinding"])
                        )

                story.append(Spacer(1, 0.3 * inch))

            # Add chart if clusters available
            if clusters.get("clusters"):
                chart_path = self._create_chart(clusters["clusters"])
                if chart_path and os.path.exists(chart_path):
                    story.append(
                        Paragraph(
                            "Market Opportunity Analysis", self.styles["Heading2"]
                        )
                    )
                    story.append(Spacer(1, 0.1 * inch))

                    # Add chart image
                    img = Image(chart_path, width=6 * inch, height=3.6 * inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2 * inch))

            # Market Opportunities
            if "market_opportunities" in lead_magnet_content:
                story.append(PageBreak())
                story.append(Paragraph("Market Opportunities", self.styles["Heading1"]))
                story.append(Spacer(1, 0.2 * inch))

                market_opps = lead_magnet_content["market_opportunities"]
                if isinstance(market_opps, str):
                    story.append(Paragraph(market_opps, self.styles["Normal"]))
                else:
                    story.append(Paragraph(str(market_opps), self.styles["Normal"]))

                story.append(Spacer(1, 0.3 * inch))

            # Actionable Insights
            if "actionable_insights" in lead_magnet_content:
                story.append(Paragraph("Actionable Insights", self.styles["Heading1"]))
                story.append(Spacer(1, 0.2 * inch))

                insights_text = lead_magnet_content["actionable_insights"]
                if isinstance(insights_text, str):
                    story.append(Paragraph(insights_text, self.styles["InsightBox"]))
                else:
                    story.append(
                        Paragraph(str(insights_text), self.styles["InsightBox"])
                    )
                story.append(Spacer(1, 0.3 * inch))

            # Industry Trends
            if "industry_trends" in lead_magnet_content:
                story.append(Paragraph("Industry Trends", self.styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))

                trends_text = lead_magnet_content["industry_trends"]
                if isinstance(trends_text, str):
                    story.append(Paragraph(trends_text, self.styles["Normal"]))
                else:
                    story.append(Paragraph(str(trends_text), self.styles["Normal"]))

                story.append(Spacer(1, 0.3 * inch))

            # Next Steps
            if "next_steps" in lead_magnet_content:
                story.append(PageBreak())
                story.append(Paragraph("Next Steps", self.styles["Heading1"]))
                story.append(Spacer(1, 0.2 * inch))

                next_steps_text = lead_magnet_content["next_steps"]
                if isinstance(next_steps_text, str):
                    story.append(Paragraph(next_steps_text, self.styles["Normal"]))
                else:
                    story.append(Paragraph(str(next_steps_text), self.styles["Normal"]))

                story.append(Spacer(1, 0.3 * inch))

            # About section
            if "about_section" in lead_magnet_content:
                story.append(Paragraph("About This Research", self.styles["Heading2"]))
                story.append(Spacer(1, 0.1 * inch))

                about_text = lead_magnet_content["about_section"]
                if isinstance(about_text, str):
                    story.append(Paragraph(about_text, self.styles["Normal"]))
                else:
                    story.append(Paragraph(str(about_text), self.styles["Normal"]))

            # Build PDF
            doc.build(story)

            logger.info(f"PDF report generated successfully: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            raise


def generate_lead_magnet_pdf(
    weekly_report: dict[str, Any], output_path: str | None = None
) -> str:
    """
    Generate a lead magnet PDF from weekly report data.

    Args:
        weekly_report: Weekly analytics report
        output_path: Output file path (optional)

    Returns:
        str: Path to generated PDF
    """
    try:
        generator = PDFReportGenerator()

        lead_magnet_content = weekly_report.get("lead_magnet_content", {})
        clusters = weekly_report.get("pain_point_clusters", {})

        return generator.generate_pdf_report(lead_magnet_content, clusters, output_path)

    except Exception as e:
        logger.error(f"Error generating lead magnet PDF: {e}")
        raise


if __name__ == "__main__":
    # Test PDF generation with sample data
    sample_content = {
        "executive_summary": "This report analyzes the top SaaS pain points identified through AI-powered market research...",
        "key_findings": [
            "73% of businesses struggle with AI tool adoption",
            "Customer support automation is the #1 priority",
            "SMBs are willing to pay $200+/month for the right solution",
        ],
        "market_opportunities": "The market shows significant opportunities in three key areas...",
        "actionable_insights": "Based on our analysis, SaaS founders should focus on...",
        "next_steps": "To capitalize on these insights, we recommend...",
    }

    sample_clusters = {
        "clusters": [
            {
                "cluster_name": "AI Adoption Barriers",
                "market_size": "Large",
                "urgency": "High",
                "revenue_potential": "High",
            }
        ]
    }

    generator = PDFReportGenerator()
    pdf_path = generator.generate_pdf_report(sample_content, sample_clusters)
    print(f"Sample PDF generated: {pdf_path}")
