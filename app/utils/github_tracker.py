"""
GitHub Issue Tracker for Daily Commit Status
Logs daily progress to GitHub issues with proper #Issue references
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from github import Github

from app.config.logging import get_logger

logger = get_logger(__name__)


class GitHubTracker:
    """Track daily commits and update GitHub issues"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_name = "IgorGanapolsky/agent-web-scraper"

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)

    def get_daily_commits(self, date: Optional[datetime] = None) -> list[dict]:
        """Get commits for a specific day"""

        if date is None:
            date = datetime.now()

        # Get commits from the last 24 hours
        since = date.replace(hour=0, minute=0, second=0, microsecond=0)
        until = since + timedelta(days=1)

        try:
            commits = self.repo.get_commits(since=since, until=until)

            commit_data = []
            for commit in commits:
                commit_info = {
                    "sha": commit.sha[:8],
                    "message": commit.commit.message.split("\n")[0],  # First line only
                    "author": commit.commit.author.name,
                    "timestamp": commit.commit.author.date.isoformat(),
                    "url": commit.html_url,
                    "files_changed": len(commit.files) if commit.files else 0,
                }
                commit_data.append(commit_info)

            return commit_data

        except Exception as e:
            logger.error(f"Failed to fetch commits: {e}")
            return []

    def extract_issue_references(self, commit_message: str) -> list[int]:
        """Extract issue numbers from commit message (#123, #456, etc.)"""

        import re

        # Find patterns like #123, #456
        pattern = r"#(\d+)"
        matches = re.findall(pattern, commit_message)

        return [int(match) for match in matches]

    def get_repository_stats(self) -> dict:
        """Get current repository statistics"""

        try:
            # Basic repo info
            stats = {
                "total_commits": self.repo.get_commits().totalCount,
                "open_issues": self.repo.open_issues_count,
                "total_issues": self.repo.get_issues(state="all").totalCount,
                "stars": self.repo.stargazers_count,
                "forks": self.repo.forks_count,
                "size_kb": self.repo.size,
                "last_updated": self.repo.updated_at.isoformat(),
            }

            # Get language breakdown
            languages = self.repo.get_languages()
            stats["languages"] = dict(
                sorted(languages.items(), key=lambda x: x[1], reverse=True)
            )

            return stats

        except Exception as e:
            logger.error(f"Failed to get repository stats: {e}")
            return {}

    def create_daily_status_issue(
        self, date: Optional[datetime] = None
    ) -> Optional[int]:
        """Create or update daily status issue"""

        if date is None:
            date = datetime.now()

        date_str = date.strftime("%Y-%m-%d")
        title = f"Daily Status Report - {date_str}"

        # Get commits for the day
        commits = self.get_daily_commits(date)
        repo_stats = self.get_repository_stats()

        # Build issue body
        body_parts = [
            f"# Daily Development Status - {date_str}",
            "",
            "## 📊 Summary",
            f"- **Commits today**: {len(commits)}",
            f"- **Total repository commits**: {repo_stats.get('total_commits', 'N/A')}",
            f"- **Open issues**: {repo_stats.get('open_issues', 'N/A')}",
            f"- **Repository size**: {repo_stats.get('size_kb', 0)} KB",
            "",
        ]

        if commits:
            body_parts.extend(["## 🚀 Today's Commits", ""])

            for commit in commits:
                # Extract issue references
                issue_refs = self.extract_issue_references(commit["message"])
                issue_links = []

                for issue_num in issue_refs:
                    try:
                        issue = self.repo.get_issue(issue_num)
                        issue_links.append(f"#{issue_num} ({issue.title})")
                    except Exception:
                        issue_links.append(f"#{issue_num}")

                issue_text = f" → {', '.join(issue_links)}" if issue_links else ""

                body_parts.extend(
                    [
                        f"### [{commit['sha']}]({commit['url']})",
                        f"**{commit['message']}**{issue_text}",
                        f"- Author: {commit['author']}",
                        f"- Files changed: {commit['files_changed']}",
                        f"- Time: {commit['timestamp']}",
                        "",
                    ]
                )
        else:
            body_parts.extend(
                [
                    "## ⚠️ No Commits Today",
                    "",
                    "No commits were made today. Consider:",
                    "- Checking if development is on track",
                    "- Reviewing pending tasks",
                    "- Planning tomorrow's work",
                    "",
                ]
            )

        # Add language breakdown
        if repo_stats.get("languages"):
            body_parts.extend(["## 💻 Repository Languages", ""])

            total_bytes = sum(repo_stats["languages"].values())
            for lang, bytes_count in list(repo_stats["languages"].items())[:5]:  # Top 5
                percentage = (bytes_count / total_bytes) * 100
                body_parts.append(f"- **{lang}**: {percentage:.1f}%")

            body_parts.append("")

        # Add automation footer
        body_parts.extend(
            [
                "---",
                f"🤖 Generated automatically at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EST",
                "",
                "**Next Actions:**",
                "- [ ] Review commit quality and completeness",
                "- [ ] Update issue references if missing",
                "- [ ] Plan tomorrow's development priorities",
                "- [ ] Check if daily revenue target was met ($300)",
            ]
        )

        body = "\n".join(body_parts)

        try:
            # Check if issue already exists for today
            existing_issues = self.repo.get_issues(
                state="open", labels=["daily-status"], creator=self.repo.owner.login
            )

            today_issue = None
            for issue in existing_issues:
                if date_str in issue.title:
                    today_issue = issue
                    break

            if today_issue:
                # Update existing issue
                today_issue.edit(title=title, body=body)
                logger.info(f"Updated daily status issue #{today_issue.number}")
                return today_issue.number
            else:
                # Create new issue
                issue = self.repo.create_issue(
                    title=title, body=body, labels=["daily-status", "automation"]
                )
                logger.info(f"Created daily status issue #{issue.number}")
                return issue.number

        except Exception as e:
            logger.error(f"Failed to create/update daily status issue: {e}")
            return None

    def update_issue_with_commit_reference(
        self, issue_number: int, commit_sha: str, commit_message: str
    ):
        """Add commit reference to existing issue"""

        try:
            issue = self.repo.get_issue(issue_number)

            # Add comment with commit reference
            comment_body = f"**Commit Reference**: [{commit_sha[:8]}](https://github.com/{self.repo_name}/commit/{commit_sha})\n\n{commit_message}"

            issue.create_comment(comment_body)
            logger.info(f"Added commit reference to issue #{issue_number}")

        except Exception as e:
            logger.error(
                f"Failed to update issue #{issue_number} with commit reference: {e}"
            )

    def get_recent_issues_summary(self, days: int = 7) -> dict:
        """Get summary of recent issues for reporting"""

        try:
            since = datetime.now() - timedelta(days=days)

            all_issues = self.repo.get_issues(state="all", since=since)

            summary = {
                "total_issues": 0,
                "open_issues": 0,
                "closed_issues": 0,
                "issues_by_label": {},
                "recent_activity": [],
            }

            for issue in all_issues:
                summary["total_issues"] += 1

                if issue.state == "open":
                    summary["open_issues"] += 1
                else:
                    summary["closed_issues"] += 1

                # Count labels
                for label in issue.labels:
                    if label.name not in summary["issues_by_label"]:
                        summary["issues_by_label"][label.name] = 0
                    summary["issues_by_label"][label.name] += 1

                # Recent activity
                if len(summary["recent_activity"]) < 5:
                    summary["recent_activity"].append(
                        {
                            "number": issue.number,
                            "title": issue.title,
                            "state": issue.state,
                            "updated": issue.updated_at.isoformat(),
                            "url": issue.html_url,
                        }
                    )

            return summary

        except Exception as e:
            logger.error(f"Failed to get issues summary: {e}")
            return {}


def run_daily_commit_tracking():
    """Main function to run daily commit tracking"""

    try:
        tracker = GitHubTracker()

        # Create or update daily status issue
        issue_number = tracker.create_daily_status_issue()

        if issue_number:
            logger.info(
                f"Daily commit tracking completed. Issue #{issue_number} updated."
            )
            return {
                "success": True,
                "issue_number": issue_number,
                "timestamp": datetime.now().isoformat(),
            }
        else:
            logger.error("Failed to create daily status issue")
            return {"success": False, "error": "Failed to create daily status issue"}

    except Exception as e:
        logger.error(f"Daily commit tracking failed: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    result = run_daily_commit_tracking()
    print(f"Daily tracking result: {result}")
