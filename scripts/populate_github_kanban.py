#!/usr/bin/env python3
"""
GitHub Issues and Project Board Automation Script

This script parses ROADMAP_ISSUES.md and creates GitHub Issues,
then assigns them to the GitHub Project Board with proper labels and columns.
"""

import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Issue:
    """Represents a GitHub Issue to be created"""

    title: str
    body: str
    labels: list[str]
    priority: str
    category: str
    status: str


class GitHubProjectManager:
    """Manages GitHub Issues and Project Board operations"""

    def __init__(self, token: str, owner: str, repo: str, dry_run: bool = False):
        self.token = token
        self.owner = owner
        self.repo = repo
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "agent-web-scraper-kanban-automation",
            }
        )

        # GitHub GraphQL endpoint for Project V2 operations
        self.graphql_url = "https://api.github.com/graphql"
        self.graphql_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def get_project_id(self, project_url: str) -> Optional[str]:
        """Extract project ID from GitHub Project URL"""
        try:
            # Extract project number from URL like https://github.com/users/IgorGanapolsky/projects/2
            project_number = project_url.split("/")[-1]

            query = """
            query($owner: String!, $number: Int!) {
                user(login: $owner) {
                    projectV2(number: $number) {
                        id
                        title
                    }
                }
            }
            """

            variables = {"owner": self.owner, "number": int(project_number)}
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["user"]["projectV2"]:
                    project_id = data["data"]["user"]["projectV2"]["id"]
                    project_title = data["data"]["user"]["projectV2"]["title"]
                    logger.info(f"Found project: {project_title} (ID: {project_id})")
                    return project_id
                else:
                    logger.error(f"Project not found or not accessible: {data}")
            else:
                logger.error(
                    f"GraphQL query failed: {response.status_code} - {response.text}"
                )
        except Exception as e:
            logger.error(f"Error getting project ID: {e}")

        return None

    def create_labels(self) -> dict[str, bool]:
        """Create necessary labels in the repository"""
        labels_to_create = [
            {
                "name": "high-priority",
                "color": "d73a4a",
                "description": "High priority task",
            },
            {
                "name": "medium-priority",
                "color": "fbca04",
                "description": "Medium priority task",
            },
            {
                "name": "low-priority",
                "color": "0075ca",
                "description": "Low priority task",
            },
            {
                "name": "enhancement",
                "color": "a2eeef",
                "description": "New feature or request",
            },
            {"name": "ai", "color": "7057ff", "description": "AI/ML related task"},
            {
                "name": "automation",
                "color": "1d76db",
                "description": "Automation related task",
            },
            {
                "name": "business",
                "color": "d4c5f9",
                "description": "Business related task",
            },
            {
                "name": "analytics",
                "color": "e99695",
                "description": "Analytics related task",
            },
            {
                "name": "integration",
                "color": "bfd4f2",
                "description": "Integration related task",
            },
            {
                "name": "infrastructure",
                "color": "0e8a16",
                "description": "Infrastructure related task",
            },
            {"name": "api", "color": "5319e7", "description": "API related task"},
        ]

        results = {}

        for label_info in labels_to_create:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create label: {label_info['name']}")
                results[label_info["name"]] = True
                continue

            try:
                # Check if label exists
                response = self.session.get(
                    f"https://api.github.com/repos/{self.owner}/{self.repo}/labels/{label_info['name']}"
                )

                if response.status_code == 200:
                    logger.info(f"Label '{label_info['name']}' already exists")
                    results[label_info["name"]] = True
                elif response.status_code == 404:
                    # Create the label
                    response = self.session.post(
                        f"https://api.github.com/repos/{self.owner}/{self.repo}/labels",
                        json=label_info,
                    )

                    if response.status_code == 201:
                        logger.info(f"Created label: {label_info['name']}")
                        results[label_info["name"]] = True
                    else:
                        logger.error(
                            f"Failed to create label {label_info['name']}: {response.status_code}"
                        )
                        results[label_info["name"]] = False
                else:
                    logger.error(
                        f"Error checking label {label_info['name']}: {response.status_code}"
                    )
                    results[label_info["name"]] = False

                # Rate limiting
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Exception creating label {label_info['name']}: {e}")
                results[label_info["name"]] = False

        return results

    def create_issue(self, issue: Issue) -> Optional[int]:
        """Create a GitHub Issue"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would create issue: {issue.title}")
            return 12345  # Mock issue number for dry run

        try:
            issue_data = {
                "title": issue.title,
                "body": issue.body,
                "labels": issue.labels,
            }

            response = self.session.post(
                f"https://api.github.com/repos/{self.owner}/{self.repo}/issues",
                json=issue_data,
            )

            if response.status_code == 201:
                issue_number = response.json()["number"]
                logger.info(f"Created issue #{issue_number}: {issue.title}")
                return issue_number
            else:
                logger.error(
                    f"Failed to create issue '{issue.title}': {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception creating issue '{issue.title}': {e}")
            return None

    def add_issue_to_project(self, project_id: str, issue_number: int) -> bool:
        """Add an issue to the GitHub Project Board"""
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would add issue #{issue_number} to project {project_id}"
            )
            return True

        try:
            # First get the issue node ID
            response = self.session.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{issue_number}"
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to get issue #{issue_number}: {response.status_code}"
                )
                return False

            issue_node_id = response.json()["node_id"]

            # Add issue to project using GraphQL
            mutation = """
            mutation($projectId: ID!, $contentId: ID!) {
                addProjectV2ItemByContentId(input: {
                    projectId: $projectId
                    contentId: $contentId
                }) {
                    item {
                        id
                    }
                }
            }
            """

            variables = {"projectId": project_id, "contentId": issue_node_id}

            response = requests.post(
                self.graphql_url,
                json={"query": mutation, "variables": variables},
                headers=self.graphql_headers,
            )

            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    logger.info(f"Added issue #{issue_number} to project board")
                    return True
                else:
                    logger.error(
                        f"GraphQL errors adding issue to project: {data['errors']}"
                    )
                    return False
            else:
                logger.error(
                    f"Failed to add issue to project: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Exception adding issue #{issue_number} to project: {e}")
            return False


def parse_roadmap_file(file_path: str) -> list[Issue]:
    """Parse ROADMAP_ISSUES.md and extract issues"""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error(f"Roadmap file not found: {file_path}")
        return []

    issues = []
    current_priority = None

    # Split content by lines and process sequentially
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Check for priority section headers (## High Priority Issues, etc.)
        if line.startswith("## ") and "Priority Issues" in line:
            if "High Priority" in line:
                current_priority = "High Priority"
            elif "Medium Priority" in line:
                current_priority = "Medium Priority"
            elif "Low Priority" in line:
                current_priority = "Low Priority"
            logger.debug(f"Found priority section: {current_priority}")
            i += 1
            continue

        # Check for individual issue headers (### 1. Title, etc.)
        if line.startswith("### ") and current_priority and re.search(r"\d+\.", line):
            # Extract title (remove numbering)
            issue_title = re.sub(r"^###\s*\d+\.\s*", "", line).strip()

            # Parse issue content
            labels = ["enhancement"]
            status = "To Do"
            category = "general"
            body_lines = []

            i += 1  # Move to next line

            # Collect issue content until next ### or ## or end of file
            while i < len(lines):
                current_line = lines[i].strip()

                # Stop at next issue or section
                if current_line.startswith("###") or current_line.startswith("##"):
                    break

                # Parse metadata
                if current_line.startswith("**Labels:**"):
                    label_text = current_line.replace("**Labels:**", "").strip()
                    # Parse labels, removing backticks and quotes
                    labels = [
                        l.strip().strip("`").strip('"').strip("'")
                        for l in label_text.split(",")
                        if l.strip()
                    ]
                elif current_line.startswith("**Status:**"):
                    status = current_line.replace("**Status:**", "").strip()
                elif current_line.startswith("**Category:**"):
                    category = current_line.replace("**Category:**", "").strip()
                elif current_line == "---":
                    # End of this issue
                    break
                elif current_line and not current_line.startswith("**"):
                    # Regular content line
                    body_lines.append(current_line)
                elif current_line.startswith("**") and ":" in current_line:
                    # Other metadata lines like **Business Impact:**
                    body_lines.append(current_line)
                elif current_line.startswith("-"):
                    # Acceptance criteria items
                    body_lines.append(current_line)

                i += 1

            # Add priority label if not already present
            priority_label = current_priority.lower().replace(" ", "-") + "-priority"
            if priority_label not in labels:
                labels.append(priority_label)

            # Clean up body
            issue_body = "\n".join(body_lines).strip()

            issue = Issue(
                title=issue_title,
                body=issue_body,
                labels=labels,
                priority=current_priority,
                category=category,
                status=status,
            )

            issues.append(issue)
            logger.debug(
                f"Parsed issue: {issue.title} [{issue.priority}] - Labels: {labels}"
            )
            continue

        i += 1

    logger.info(f"Parsed {len(issues)} issues from roadmap file")
    return issues


def main():
    """Main execution function"""
    # Load environment variables
    load_dotenv()

    # Configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OWNER = "IgorGanapolsky"
    REPO = "agent-web-scraper"
    PROJECT_URL = "https://github.com/users/IgorGanapolsky/projects/2"
    ROADMAP_FILE = "ROADMAP_ISSUES.md"

    # Check for dry run mode
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("🧪 DRY RUN MODE - No actual changes will be made")

    # Validate configuration
    if not GITHUB_TOKEN:
        logger.error("GITHUB_TOKEN not found in environment variables")
        return 1

    if not os.path.exists(ROADMAP_FILE):
        logger.error(f"Roadmap file not found: {ROADMAP_FILE}")
        return 1

    # Initialize GitHub manager
    github = GitHubProjectManager(GITHUB_TOKEN, OWNER, REPO, dry_run)

    logger.info("🚀 Starting GitHub Issues and Project Board automation")
    logger.info(f"Repository: {OWNER}/{REPO}")
    logger.info(f"Project URL: {PROJECT_URL}")

    # Get project ID
    project_id = github.get_project_id(PROJECT_URL)
    if not project_id:
        logger.error("Failed to get project ID. Continuing with issue creation only.")

    # Create necessary labels
    logger.info("📋 Creating repository labels...")
    label_results = github.create_labels()
    successful_labels = sum(1 for success in label_results.values() if success)
    logger.info(f"Labels created/verified: {successful_labels}/{len(label_results)}")

    # Parse roadmap file
    logger.info("📖 Parsing roadmap file...")
    issues = parse_roadmap_file(ROADMAP_FILE)

    if not issues:
        logger.error("No issues found in roadmap file")
        return 1

    # Create issues and add to project
    logger.info(f"🔨 Creating {len(issues)} GitHub issues...")

    created_count = 0
    project_count = 0

    for i, issue in enumerate(issues, 1):
        logger.info(f"Processing issue {i}/{len(issues)}: {issue.title}")

        # Create the issue
        issue_number = github.create_issue(issue)
        if issue_number:
            created_count += 1

            # Add to project board if we have project ID
            if project_id:
                if github.add_issue_to_project(project_id, issue_number):
                    project_count += 1

        # Rate limiting
        if not dry_run:
            time.sleep(1)

    # Summary
    logger.info("✅ Automation complete!")
    logger.info(f"📊 Issues created: {created_count}/{len(issues)}")
    if project_id:
        logger.info(f"📋 Issues added to project: {project_count}/{created_count}")

    if dry_run:
        logger.info("🧪 This was a dry run - no actual changes were made")
        logger.info("Remove --dry-run flag to execute for real")

    return 0


if __name__ == "__main__":
    sys.exit(main())
