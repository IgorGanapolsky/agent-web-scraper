#!/usr/bin/env python3
"""
Enhanced GitHub Issues and Project Board Automation Script

This script provides a comprehensive solution for:
1. Creating GitHub Issues from ROADMAP_ISSUES.md
2. Adding them to GitHub Project Board
3. Handling various project board configurations
4. Providing detailed logging and error handling
5. Fallback mechanisms for manual setup
"""

import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("kanban_sync.log"),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class ProjectInfo:
    """Project board information"""

    id: str
    title: str
    url: str
    number: int


class EnhancedGitHubProjectManager:
    """Enhanced GitHub Project manager with better error handling and fallbacks"""

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
                "User-Agent": "enhanced-kanban-sync/1.0",
            }
        )

        self.graphql_url = "https://api.github.com/graphql"
        self.graphql_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def test_github_connection(self) -> bool:
        """Test GitHub API connection and permissions"""
        try:
            response = self.session.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}"
            )
            if response.status_code == 200:
                repo_data = response.json()
                logger.info(f"✅ Connected to repository: {repo_data['full_name']}")
                return True
            else:
                logger.error(
                    f"❌ Failed to connect to repository: {response.status_code}"
                )
                return False
        except Exception as e:
            logger.error(f"❌ Connection test failed: {e}")
            return False

    def find_user_projects(self) -> list[ProjectInfo]:
        """Find all user projects"""
        projects = []
        try:
            query = """
            query($owner: String!) {
                user(login: $owner) {
                    projectsV2(first: 10) {
                        nodes {
                            id
                            title
                            url
                            number
                        }
                    }
                }
            }
            """

            variables = {"owner": self.owner}
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            )

            if response.status_code == 200:
                data = response.json()
                if "data" in data and data["data"]["user"]["projectsV2"]:
                    for project in data["data"]["user"]["projectsV2"]["nodes"]:
                        projects.append(
                            ProjectInfo(
                                id=project["id"],
                                title=project["title"],
                                url=project["url"],
                                number=project["number"],
                            )
                        )
                        logger.info(
                            f"📋 Found project: {project['title']} (#{project['number']})"
                        )

        except Exception as e:
            logger.error(f"Error finding projects: {e}")

        return projects

    def create_issues_from_roadmap(
        self, roadmap_file: str = "ROADMAP_ISSUES.md"
    ) -> list[int]:
        """Create issues from roadmap file and return issue numbers"""
        if not os.path.exists(roadmap_file):
            logger.error(f"Roadmap file not found: {roadmap_file}")
            return []

        # Import the parsing logic from populate_github_kanban.py
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from populate_github_kanban import parse_roadmap_file

        logger.info(f"📖 Parsing roadmap file: {roadmap_file}")
        issues = parse_roadmap_file(roadmap_file)

        if not issues:
            logger.error("No issues found in roadmap file")
            return []

        created_issues = []
        logger.info(f"🔨 Creating {len(issues)} GitHub issues...")

        for i, issue in enumerate(issues, 1):
            if self.dry_run:
                logger.info(
                    f"[DRY RUN] Would create issue {i}/{len(issues)}: {issue.title}"
                )
                created_issues.append(i)  # Mock issue number
            else:
                logger.info(f"Creating issue {i}/{len(issues)}: {issue.title}")
                issue_number = self.create_issue(issue)
                if issue_number:
                    created_issues.append(issue_number)
                    logger.info(f"✅ Created issue #{issue_number}: {issue.title}")
                else:
                    logger.error(f"❌ Failed to create issue: {issue.title}")

                # Rate limiting
                time.sleep(1)

        logger.info(
            f"📊 Successfully created {len(created_issues)}/{len(issues)} issues"
        )
        return created_issues

    def create_issue(self, issue) -> Optional[int]:
        """Create a single GitHub issue"""
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
                return response.json()["number"]
            else:
                logger.error(
                    f"Failed to create issue: {response.status_code} - {response.text}"
                )
                return None

        except Exception as e:
            logger.error(f"Exception creating issue: {e}")
            return None

    def add_issues_to_project(self, project_id: str, issue_numbers: list[int]) -> int:
        """Add multiple issues to project board"""
        success_count = 0

        for issue_number in issue_numbers:
            if self.dry_run:
                logger.info(f"[DRY RUN] Would add issue #{issue_number} to project")
                success_count += 1
            else:
                if self.add_issue_to_project(project_id, issue_number):
                    success_count += 1
                    logger.info(f"✅ Added issue #{issue_number} to project board")
                else:
                    logger.error(
                        f"❌ Failed to add issue #{issue_number} to project board"
                    )

                # Rate limiting
                time.sleep(0.5)

        logger.info(
            f"📊 Added {success_count}/{len(issue_numbers)} issues to project board"
        )
        return success_count

    def add_issue_to_project(self, project_id: str, issue_number: int) -> bool:
        """Add a single issue to project board"""
        try:
            # Get issue node ID
            response = self.session.get(
                f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{issue_number}"
            )

            if response.status_code != 200:
                logger.error(
                    f"Failed to get issue #{issue_number}: {response.status_code}"
                )
                return False

            issue_node_id = response.json()["node_id"]

            # Add to project
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
                return "errors" not in data
            else:
                logger.error(f"GraphQL mutation failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Exception adding issue to project: {e}")
            return False

    def generate_manual_instructions(
        self, issue_numbers: list[int], project_url: str | None = None
    ):
        """Generate manual setup instructions"""
        logger.info("📝 Generating manual setup instructions...")

        instructions = [
            "🔧 MANUAL SETUP REQUIRED",
            "=" * 50,
            "",
            "The automated project board sync encountered issues.",
            "Please follow these manual steps:",
            "",
            "1. 📋 Go to your GitHub Project Board:",
            f"   {project_url or 'https://github.com/users/' + self.owner + '/projects/2'}",
            "",
            "2. + Add the following issues to your project:",
        ]

        for issue_num in issue_numbers:
            instructions.append(
                f"   - Issue #{issue_num}: https://github.com/{self.owner}/{self.repo}/issues/{issue_num}"
            )

        instructions.extend(
            [
                "",
                "3. 🏷️ Organize issues by priority labels:",
                "   - high-priority issues → 'To Do' or 'High Priority' column",
                "   - medium-priority issues → 'Medium Priority' column",
                "   - low-priority issues → 'Low Priority' column",
                "",
                "4. 🔄 Set up automation rules (optional):",
                "   - Auto-move issues to 'In Progress' when assigned",
                "   - Auto-move to 'Done' when closed",
                "",
                "📧 For support, create an issue in the repository or contact the maintainer.",
            ]
        )

        manual_guide = "\n".join(instructions)

        # Save to file
        with open("manual_kanban_setup.txt", "w") as f:
            f.write(manual_guide)

        logger.info("💾 Manual setup guide saved to: manual_kanban_setup.txt")
        print("\n" + manual_guide)


def main():
    """Main execution function"""
    load_dotenv()

    # Configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    OWNER = "IgorGanapolsky"
    REPO = "agent-web-scraper"
    ROADMAP_FILE = "ROADMAP_ISSUES.md"

    # Check for dry run
    dry_run = "--dry-run" in sys.argv
    if dry_run:
        logger.info("🧪 DRY RUN MODE - No actual changes will be made")

    # Validate
    if not GITHUB_TOKEN:
        logger.error("❌ GITHUB_TOKEN not found in environment variables")
        return 1

    if not os.path.exists(ROADMAP_FILE):
        logger.error(f"❌ Roadmap file not found: {ROADMAP_FILE}")
        return 1

    # Initialize manager
    manager = EnhancedGitHubProjectManager(GITHUB_TOKEN, OWNER, REPO, dry_run)

    logger.info("🚀 Enhanced GitHub Kanban Sync Starting")
    logger.info(f"📁 Repository: {OWNER}/{REPO}")

    # Test connection
    if not manager.test_github_connection():
        logger.error("❌ GitHub connection failed")
        return 1

    # Find projects
    projects = manager.find_user_projects()
    if not projects:
        logger.warning(
            "⚠️ No projects found - issues will be created without project assignment"
        )

    # Create issues
    issue_numbers = manager.create_issues_from_roadmap(ROADMAP_FILE)
    if not issue_numbers:
        logger.error("❌ No issues were created")
        return 1

    # Add to project board
    project_success = 0
    if projects and issue_numbers:
        # Use the first project found (or find specific one)
        target_project = projects[0]  # Could be made configurable
        logger.info(f"🎯 Adding issues to project: {target_project.title}")

        project_success = manager.add_issues_to_project(
            target_project.id, issue_numbers
        )

    # Generate manual instructions if needed
    if not projects or project_success < len(issue_numbers):
        project_url = projects[0].url if projects else None
        manager.generate_manual_instructions(issue_numbers, project_url)

    # Summary
    logger.info("🎉 Enhanced Kanban Sync Complete!")
    logger.info(f"📊 Issues created: {len(issue_numbers)}")
    if projects:
        logger.info(
            f"📋 Issues added to project: {project_success}/{len(issue_numbers)}"
        )

    if dry_run:
        logger.info("🧪 This was a dry run - no actual changes were made")

    return 0


if __name__ == "__main__":
    sys.exit(main())
