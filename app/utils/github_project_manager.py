"""
GitHub Project Board Automation
Automatically manages Kanban board based on issue status and labels
"""

import os
from typing import Optional

import requests
from github import Github

from app.config.logging import get_logger

logger = get_logger(__name__)


class GitHubProjectManager:
    """Automated GitHub Project Board management"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_name = "IgorGanapolsky/agent-web-scraper"
        self.project_id = "2"  # Your project ID from URL

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable required")

        self.github = Github(self.github_token)
        self.repo = self.github.get_repo(self.repo_name)

        # GitHub GraphQL API for Projects v2
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }

    def get_project_columns(self) -> dict[str, str]:
        """Get project column IDs and names"""

        query = """
        query($owner: String!, $number: Int!) {
            user(login: $owner) {
                projectV2(number: $number) {
                    id
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"owner": "IgorGanapolsky", "number": int(self.project_id)}

        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )

            if response.status_code == 200:
                data = response.json()
                project = data["data"]["user"]["projectV2"]

                # Find the Status field
                status_field = None
                for field in project["fields"]["nodes"]:
                    if field.get("name") == "Status":
                        status_field = field
                        break

                if status_field:
                    columns = {}
                    for option in status_field["options"]:
                        columns[option["name"]] = option["id"]
                    return columns
                else:
                    logger.warning("Status field not found in project")
                    return {}
            else:
                logger.error(f"GraphQL query failed: {response.text}")
                return {}

        except Exception as e:
            logger.error(f"Failed to get project columns: {e}")
            return {}

    def move_issue_to_column(self, issue_number: int, column_name: str) -> bool:
        """Move issue to specified column"""

        try:
            # First, get the project item ID for this issue
            query = """
            query($owner: String!, $repo: String!, $number: Int!, $projectNumber: Int!) {
                repository(owner: $owner, name: $repo) {
                    issue(number: $number) {
                        projectItems(first: 10) {
                            nodes {
                                id
                                project {
                                    number
                                }
                            }
                        }
                    }
                }
            }
            """

            variables = {
                "owner": "IgorGanapolsky",
                "repo": "agent-web-scraper",
                "number": issue_number,
                "projectNumber": int(self.project_id),
            }

            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )

            if response.status_code != 200:
                logger.error(f"Failed to get issue project items: {response.text}")
                return False

            data = response.json()
            issue_data = data["data"]["repository"]["issue"]

            # Find the project item for our project
            project_item_id = None
            for item in issue_data["projectItems"]["nodes"]:
                if item["project"]["number"] == int(self.project_id):
                    project_item_id = item["id"]
                    break

            if not project_item_id:
                logger.warning(f"Issue #{issue_number} not found in project")
                return False

            # Get column IDs
            columns = self.get_project_columns()
            if column_name not in columns:
                logger.error(f"Column '{column_name}' not found")
                return False

            column_id = columns[column_name]

            # Update the project item status
            mutation = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                }) {
                    projectV2Item {
                        id
                    }
                }
            }
            """

            # Get project and status field IDs
            project_data = self.get_project_info()
            if not project_data:
                return False

            mutation_variables = {
                "projectId": project_data["project_id"],
                "itemId": project_item_id,
                "fieldId": project_data["status_field_id"],
                "value": {"singleSelectOptionId": column_id},
            }

            response = requests.post(
                self.graphql_url,
                json={"query": mutation, "variables": mutation_variables},
                headers=self.headers,
            )

            if response.status_code == 200:
                logger.info(f"Moved issue #{issue_number} to {column_name}")
                return True
            else:
                logger.error(f"Failed to move issue: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to move issue #{issue_number}: {e}")
            return False

    def get_project_info(self) -> Optional[dict]:
        """Get project ID and status field ID"""

        query = """
        query($owner: String!, $number: Int!) {
            user(login: $owner) {
                projectV2(number: $number) {
                    id
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"owner": "IgorGanapolsky", "number": int(self.project_id)}

        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )

            if response.status_code == 200:
                data = response.json()
                project = data["data"]["user"]["projectV2"]

                # Find status field ID
                status_field_id = None
                for field in project["fields"]["nodes"]:
                    if field.get("name") == "Status":
                        status_field_id = field["id"]
                        break

                return {"project_id": project["id"], "status_field_id": status_field_id}
            else:
                logger.error(f"Failed to get project info: {response.text}")
                return None

        except Exception as e:
            logger.error(f"Failed to get project info: {e}")
            return None

    def auto_organize_board(self) -> dict:
        """Automatically organize board based on issue labels and status"""

        try:
            # Define automation rules
            automation_rules = {
                "✅ COMPLETED": "Done",
                "🚀 n8n": "In Progress",
                "🚀 Dagger": "In Progress",
                "🚀 Gamma": "Backlog",
                "🚀 Meta": "Backlog",
                "enhancement": "Todo",
                "bug": "In Progress",
            }

            results = {"moved": [], "errors": [], "total_processed": 0}

            # Get recent issues
            issues = self.repo.get_issues(
                state="open", sort="created", direction="desc"
            )

            for issue in list(issues)[:20]:  # Process last 20 issues
                results["total_processed"] += 1

                # Determine target column based on title and labels
                target_column = None

                # Check title for keywords
                for keyword, column in automation_rules.items():
                    if keyword in issue.title:
                        target_column = column
                        break

                # If no title match, check labels
                if not target_column:
                    for label in issue.labels:
                        if label.name in automation_rules:
                            target_column = automation_rules[label.name]
                            break

                # Default to Todo if no rules match
                if not target_column:
                    target_column = "Todo"

                # Move issue to target column
                success = self.move_issue_to_column(issue.number, target_column)

                if success:
                    results["moved"].append(
                        {
                            "issue": issue.number,
                            "title": issue.title,
                            "column": target_column,
                        }
                    )
                else:
                    results["errors"].append(
                        {
                            "issue": issue.number,
                            "title": issue.title,
                            "error": f"Failed to move to {target_column}",
                        }
                    )

            logger.info(
                f"Board automation completed: {len(results['moved'])} moved, {len(results['errors'])} errors"
            )
            return results

        except Exception as e:
            logger.error(f"Board automation failed: {e}")
            return {"moved": [], "errors": [str(e)], "total_processed": 0}

    def add_issue_to_project(self, issue_number: int) -> bool:
        """Add issue to project board"""

        try:
            # Get project info
            project_data = self.get_project_info()
            if not project_data:
                return False

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

            # Get issue node ID
            issue = self.repo.get_issue(issue_number)

            variables = {
                "projectId": project_data["project_id"],
                "contentId": issue.node_id,
            }

            response = requests.post(
                self.graphql_url,
                json={"query": mutation, "variables": variables},
                headers=self.headers,
            )

            if response.status_code == 200:
                logger.info(f"Added issue #{issue_number} to project")
                return True
            else:
                logger.error(f"Failed to add issue to project: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Failed to add issue #{issue_number} to project: {e}")
            return False


def run_board_automation():
    """Main function to run board automation"""

    try:
        manager = GitHubProjectManager()

        # Auto-organize the board
        results = manager.auto_organize_board()

        if results["moved"]:
            logger.info("Board automation successful:")
            for item in results["moved"]:
                logger.info(f"  #{item['issue']}: {item['title']} → {item['column']}")

        if results["errors"]:
            logger.warning("Board automation errors:")
            for error in results["errors"]:
                logger.warning(f"  #{error['issue']}: {error['error']}")

        return results

    except Exception as e:
        logger.error(f"Board automation failed: {e}")
        return {"moved": [], "errors": [str(e)], "total_processed": 0}


if __name__ == "__main__":
    result = run_board_automation()
    print(f"Board automation result: {result}")
