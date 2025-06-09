"""
Slack Daily Reporting System
Sends daily progress reports to #chatgpt channel at 6PM EST
"""

import os
from datetime import datetime

import requests

from app.config.logging import get_logger
from app.core.cost_tracker import CostTracker
from app.utils.github_tracker import GitHubTracker

logger = get_logger(__name__)


def post_to_slack(message: str):
    """Post message to Slack using webhook"""
    webhook_url = os.getenv("SLACK_WEBHOOK_CHATGPT")
    if webhook_url:
        try:
            response = requests.post(webhook_url, json={"text": message}, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Posted to Slack: {message[:50]}...")
                return True
            else:
                logger.error(f"❌ Failed to post to Slack: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Slack posting error: {e}")
            return False
    else:
        logger.warning("⚠️ SLACK_WEBHOOK_CHATGPT not set, skipping Slack notification")
        return False


class SlackReporter:
    """Daily Slack reporting for MCP system"""

    def __init__(self):
        self.webhook_url = os.getenv("SLACK_WEBHOOK_CHATGPT")
        self.channel = "#chatgpt"

        if not self.webhook_url:
            raise ValueError("SLACK_WEBHOOK_CHATGPT environment variable required")

        self.github_tracker = GitHubTracker()
        self.cost_tracker = CostTracker(test_mode=False)

    def get_daily_metrics(self) -> dict:
        """Collect daily metrics from various sources"""

        try:
            # GitHub metrics
            commits = self.github_tracker.get_daily_commits()
            repo_stats = self.github_tracker.get_repository_stats()
            issues_summary = self.github_tracker.get_recent_issues_summary(days=1)

            # Revenue metrics
            dashboard_metrics = self.cost_tracker.get_dashboard_metrics()
            daily_revenue = self.cost_tracker.get_daily_revenue()

            # Compile metrics
            metrics = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "commits": {
                    "count": len(commits),
                    "details": commits[:3],  # Top 3 commits
                    "total_files_changed": sum(
                        c.get("files_changed", 0) for c in commits
                    ),
                },
                "repository": {
                    "open_issues": repo_stats.get("open_issues", 0),
                    "total_commits": repo_stats.get("total_commits", 0),
                    "size_kb": repo_stats.get("size_kb", 0),
                },
                "revenue": {
                    "daily": daily_revenue,
                    "mrr": dashboard_metrics.get("current_mrr", 0),
                    "customer_count": dashboard_metrics.get("customer_count", 0),
                    "target_met": daily_revenue >= 300.0,
                    "target_amount": 300.0,
                },
                "issues": {
                    "opened_today": issues_summary.get("open_issues", 0),
                    "closed_today": issues_summary.get("closed_issues", 0),
                },
            }

            return metrics

        except Exception as e:
            logger.error(f"Failed to collect daily metrics: {e}")
            return {}

    def format_slack_message(self, metrics: dict) -> dict:
        """Format metrics into Slack message blocks"""

        date = metrics.get("date", datetime.now().strftime("%Y-%m-%d"))
        commits = metrics.get("commits", {})
        revenue = metrics.get("revenue", {})
        repo = metrics.get("repository", {})
        issues = metrics.get("issues", {})

        # Determine status emoji
        status_emoji = "🟢" if revenue.get("target_met", False) else "🟡"
        if commits.get("count", 0) == 0:
            status_emoji = "🔴"

        # Build header
        header_text = f"{status_emoji} *Daily MCP Report - {date}*"

        # Commits section
        commits_text = "*📝 Development*\n"
        commits_text += f"• {commits.get('count', 0)} commits today\n"
        commits_text += f"• {commits.get('total_files_changed', 0)} files changed\n"
        commits_text += f"• {repo.get('open_issues', 0)} open issues\n"

        if commits.get("details"):
            commits_text += "\n*Recent commits:*\n"
            for commit in commits["details"][:2]:  # Top 2
                commits_text += (
                    f"• `{commit.get('sha', '')}` {commit.get('message', '')[:50]}...\n"
                )

        # Revenue section
        revenue_emoji = "💰" if revenue.get("target_met", False) else "⚠️"
        revenue_text = f"*{revenue_emoji} Revenue*\n"
        revenue_text += f"• Daily: ${revenue.get('daily', 0):.2f} / ${revenue.get('target_amount', 300):.2f}\n"
        revenue_text += f"• MRR: ${revenue.get('mrr', 0):.2f}\n"
        revenue_text += f"• Customers: {revenue.get('customer_count', 0)}\n"

        # Issues section
        issues_text = "*🎯 Issues*\n"
        issues_text += f"• Opened: {issues.get('opened_today', 0)}\n"
        issues_text += f"• Closed: {issues.get('closed_today', 0)}\n"

        # Actions section
        actions = []
        if commits.get("count", 0) == 0:
            actions.append("❗ No commits today - check development pipeline")
        if not revenue.get("target_met", False):
            actions.append(
                f"💵 Revenue target missed by ${revenue.get('target_amount', 300) - revenue.get('daily', 0):.2f}"
            )
        if repo.get("open_issues", 0) > 10:
            actions.append(
                f"📋 High issue count ({repo.get('open_issues', 0)}) - consider triage"
            )

        actions_text = ""
        if actions:
            actions_text = "\n*🚨 Action Items:*\n"
            for action in actions[:3]:  # Max 3 actions
                actions_text += f"• {action}\n"

        # Build Slack blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"SaaS Growth Dispatch - Daily Report {date}",
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": header_text}},
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": commits_text},
                    {"type": "mrkdwn", "text": revenue_text},
                ],
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": issues_text},
                    {
                        "type": "mrkdwn",
                        "text": f"*📊 Repository*\n• Size: {repo.get('size_kb', 0)} KB\n• Total commits: {repo.get('total_commits', 0)}",
                    },
                ],
            },
        ]

        if actions_text:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": actions_text}}
            )

        # Footer
        blocks.extend(
            [
                {"type": "divider"},
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"🤖 Generated at {datetime.now().strftime('%H:%M')} EST | <https://github.com/IgorGanapolsky/agent-web-scraper|View Repository>",
                        }
                    ],
                },
            ]
        )

        return {
            "channel": self.channel,
            "blocks": blocks,
            "text": f"Daily MCP Report - {date}",  # Fallback text
        }

    def format_text_message(self, metrics: dict) -> str:
        """Format metrics into a simple text message for webhook"""

        date = metrics.get("date", datetime.now().strftime("%Y-%m-%d"))
        commits = metrics.get("commits", {})
        revenue = metrics.get("revenue", {})
        repo = metrics.get("repository", {})
        issues = metrics.get("issues", {})

        # Determine status emoji
        status_emoji = "🟢" if revenue.get("target_met", False) else "🟡"
        if commits.get("count", 0) == 0:
            status_emoji = "🔴"

        # Build message text
        message = f"{status_emoji} **Daily MCP Report - {date}**\n\n"

        # Development section
        message += "📝 **Development**\n"
        message += f"• {commits.get('count', 0)} commits today\n"
        message += f"• {commits.get('total_files_changed', 0)} files changed\n"
        message += f"• {repo.get('open_issues', 0)} open issues\n\n"

        # Revenue section
        revenue_emoji = "💰" if revenue.get("target_met", False) else "⚠️"
        message += f"{revenue_emoji} **Revenue**\n"
        message += f"• Daily: ${revenue.get('daily', 0):.2f} / ${revenue.get('target_amount', 300):.2f}\n"
        message += f"• MRR: ${revenue.get('mrr', 0):.2f}\n"
        message += f"• Customers: {revenue.get('customer_count', 0)}\n\n"

        # Issues section
        message += "🎯 **Issues**\n"
        message += f"• Opened: {issues.get('opened_today', 0)}\n"
        message += f"• Closed: {issues.get('closed_today', 0)}\n\n"

        # Recent commits
        if commits.get("details"):
            message += "📋 **Recent Commits**\n"
            for commit in commits["details"][:2]:  # Top 2
                message += f"• `{commit.get('sha', '')[:8]}` {commit.get('message', '')[:50]}...\n"
            message += "\n"

        # Action items
        actions = []
        if commits.get("count", 0) == 0:
            actions.append("❗ No commits today - check development pipeline")
        if not revenue.get("target_met", False):
            actions.append(
                f"💵 Revenue target missed by ${revenue.get('target_amount', 300) - revenue.get('daily', 0):.2f}"
            )
        if repo.get("open_issues", 0) > 10:
            actions.append(
                f"📋 High issue count ({repo.get('open_issues', 0)}) - consider triage"
            )

        if actions:
            message += "🚨 **Action Items**\n"
            for action in actions[:3]:  # Max 3 actions
                message += f"• {action}\n"
            message += "\n"

        # Footer
        message += f"🤖 Generated at {datetime.now().strftime('%H:%M')} EST | <https://github.com/IgorGanapolsky/agent-web-scraper|View Repository>"

        return message

    def send_daily_report(self) -> dict:
        """Send daily report to Slack"""

        try:
            # Collect metrics
            metrics = self.get_daily_metrics()

            if not metrics:
                logger.error("No metrics available for daily report")
                return {"success": False, "error": "No metrics available"}

            # Format message as simple text for webhook
            message_text = self.format_text_message(metrics)

            # Send to Slack using webhook
            success = post_to_slack(message_text)

            if success:
                logger.info(f"Daily report sent to {self.channel}")
                return {
                    "success": True,
                    "metrics": metrics,
                }
            else:
                logger.error("Failed to send Slack message via webhook")
                return {"success": False, "error": "Webhook posting failed"}

        except Exception as e:
            logger.error(f"Failed to send daily report: {e}")
            return {"success": False, "error": str(e)}

    def send_test_message(self) -> dict:
        """Send test message to verify Slack integration"""

        try:
            test_message = f"🧪 **MCP Slack Integration Test**\n\nTest message sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST\n\n🤖 Webhook integration working correctly!"

            success = post_to_slack(test_message)

            if success:
                logger.info("Test message sent successfully")
                return {"success": True, "message": "Test message sent"}
            else:
                return {"success": False, "error": "Failed to send test message"}

        except Exception as e:
            logger.error(f"Test message failed: {e}")
            return {"success": False, "error": str(e)}

    def get_channel_info(self) -> dict:
        """Get information about the webhook configuration"""

        try:
            if self.webhook_url:
                return {
                    "success": True,
                    "channel": self.channel,
                    "webhook_configured": True,
                    "webhook_url": (
                        self.webhook_url[:50] + "..."
                        if len(self.webhook_url) > 50
                        else self.webhook_url
                    ),
                }
            else:
                return {"success": False, "error": "Webhook URL not configured"}

        except Exception as e:
            logger.error(f"Failed to get webhook info: {e}")
            return {"success": False, "error": str(e)}


def run_daily_slack_report():
    """Main function to run daily Slack reporting"""

    try:
        reporter = SlackReporter()

        # Send daily report
        result = reporter.send_daily_report()

        if result["success"]:
            logger.info("Daily Slack report sent successfully")
        else:
            logger.error(f"Daily Slack report failed: {result.get('error')}")

        return result

    except Exception as e:
        logger.error(f"Daily Slack reporting failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = run_daily_slack_report()
    print(f"Daily Slack report result: {result}")
