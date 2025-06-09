#!/usr/bin/env python3
"""
Roadmap Issues Initialization Script
Automatically creates GitHub issues and adds them to project board
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import Optional

import requests


class RoadmapInitializer:
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo = os.getenv("GITHUB_REPOSITORY", "IgorGanapolsky/agent-web-scraper")
        self.owner = self.repo.split("/")[0]
        self.repo_name = self.repo.split("/")[1]

        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")

        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
        }

        self.graphql_headers = {
            "Authorization": f"Bearer {self.github_token}",
            "Content-Type": "application/json",
        }

        print(f"🚀 Roadmap Initializer {'(TEST MODE)' if test_mode else '(LIVE MODE)'}")
        print(f"📁 Repository: {self.repo}")

    def parse_roadmap_file(self) -> list[dict]:
        """Parse ROADMAP_ISSUES.md or use fallback data"""
        roadmap_file = Path("ROADMAP_ISSUES.md")

        if roadmap_file.exists():
            return self.parse_markdown_issues(roadmap_file)
        else:
            print(
                "⚠️  ROADMAP_ISSUES.md not found, using JSON data from automation script"
            )
            return self.load_from_json()

    def parse_markdown_issues(self, file_path: Path) -> list[dict]:
        """Parse issues from markdown file"""
        with open(file_path) as f:
            content = f.read()

        issues = []
        # Split by numbered headings that represent actual issues (### \d+\. )
        issue_blocks = re.split(r"\n###\s+\d+\.\s+", content)[
            1:
        ]  # Skip first split before numbered issues

        for block in issue_blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue

            title = lines[0].strip()

            # Skip certain sections that aren't real issues
            skip_titles = [
                "Instructions for Implementation",
                "Project Board Columns Suggestion",
                "Priority Levels",
            ]
            if any(skip_title in title for skip_title in skip_titles):
                continue

            # Extract labels from **Labels:** line and clean them
            labels = []
            description_lines = []

            for line in lines[1:]:
                if line.startswith("**Labels:**"):
                    labels_text = line.replace("**Labels:**", "").strip()
                    # Clean up backticks and split by comma
                    raw_labels = [
                        label.strip().strip("`") for label in labels_text.split(",")
                    ]
                    labels = [label for label in raw_labels if label]
                elif not line.startswith("**Status:**") and not line.startswith(
                    "**Category:**"
                ):
                    # Skip status and category lines, include everything else
                    description_lines.append(line)

            # Add roadmap label to all issues
            if "roadmap" not in labels:
                labels.append("roadmap")

            description = "\n".join(description_lines).strip()

            if title and description:
                issues.append({"title": title, "body": description, "labels": labels})

        print(f"📝 Parsed {len(issues)} issues from {file_path}")
        return issues

    def load_from_json(self) -> list[dict]:
        """Load issues from JSON file created by automation scripts"""
        json_file = Path("github_issues_roadmap.json")

        if json_file.exists():
            with open(json_file) as f:
                data = json.load(f)
            print(f"📝 Loaded {len(data)} issues from {json_file}")
            return data
        else:
            print("❌ No roadmap data found")
            return []

    def get_existing_issues(self) -> list[dict]:
        """Get all existing issues to avoid duplicates"""
        url = f"https://api.github.com/repos/{self.repo}/issues"
        params = {"state": "all", "per_page": 100}

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            issues = response.json()

            existing_titles = [issue["title"] for issue in issues]
            print(f"📋 Found {len(existing_titles)} existing issues")
            return existing_titles

        except Exception as e:
            print(f"❌ Error fetching existing issues: {e}")
            return []

    def create_github_issue(self, issue_data: dict) -> Optional[dict]:
        """Create a single GitHub issue"""
        if self.test_mode:
            print(f"🧪 TEST: Would create issue '{issue_data['title']}'")
            print(f"   Labels: {issue_data.get('labels', [])}")
            print(f"   Body length: {len(issue_data.get('body', ''))}")
            return {"number": 999, "id": 999999}  # Mock response

        url = f"https://api.github.com/repos/{self.repo}/issues"

        try:
            response = requests.post(url, json=issue_data, headers=self.headers)
            response.raise_for_status()

            issue = response.json()
            print(f"✅ Created issue #{issue['number']}: {issue['title']}")
            return issue

        except Exception as e:
            print(f"❌ Error creating issue '{issue_data['title']}': {e}")
            return None

    def get_project_id(
        self, project_name: str = "SaaS Growth Dispatch - Execution Board"
    ) -> Optional[str]:
        """Get project ID using GraphQL"""
        query = """
        query($owner: String!) {
          user(login: $owner) {
            projectsV2(first: 20) {
              nodes {
                id
                title
                number
              }
            }
          }
        }
        """

        variables = {"owner": self.owner}

        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            )
            response.raise_for_status()

            data = response.json()

            if "errors" in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return None

            if not data.get("data") or not data["data"].get("user"):
                print(f"❌ No user data found for {self.owner}")
                return None

            projects = data["data"]["user"]["projectsV2"]["nodes"]

            for project in projects:
                if project["title"] == project_name:
                    print(f"✅ Found project: {project_name} (ID: {project['id']})")
                    return project["id"]

            print(f"❌ Project '{project_name}' not found")
            print(f"Available projects: {[p['title'] for p in projects]}")
            return None

        except Exception as e:
            print(f"❌ Error fetching project ID: {e}")
            if hasattr(e, "response"):
                print(f"Response: {e.response.text}")
            return None

    def add_issue_to_project(self, issue_id: str, project_id: str) -> bool:
        """Add issue to project board using GraphQL"""
        if self.test_mode:
            print(f"🧪 TEST: Would add issue {issue_id} to project {project_id}")
            return True

        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item {
              id
            }
          }
        }
        """

        variables = {"projectId": project_id, "contentId": issue_id}

        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": mutation, "variables": variables},
                headers=self.graphql_headers,
            )
            response.raise_for_status()

            data = response.json()
            if "errors" in data:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False

            print("✅ Added issue to project board")
            return True

        except Exception as e:
            print(f"❌ Error adding issue to project: {e}")
            return False

    def create_labels_if_missing(self, required_labels: list[str]):
        """Create any missing labels in the repository"""
        if self.test_mode:
            print(f"🧪 TEST: Would ensure labels exist: {required_labels}")
            return

        # Get existing labels
        url = f"https://api.github.com/repos/{self.repo}/labels"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            existing_labels = {label["name"] for label in response.json()}

            # Label definitions with colors
            label_definitions = {
                "enhancement": "a2eeef",
                "high-priority": "d73a4a",
                "medium-priority": "fbca04",
                "low-priority": "0075ca",
                "ai": "7057ff",
                "automation": "1d76db",
                "business": "d4c5f9",
                "analytics": "e99695",
                "integration": "bfd4f2",
                "infrastructure": "0e8a16",
                "api": "5319e7",
                "feature": "0052cc",
                "insight": "c5def5",
                "daily-report": "e4e669",
            }

            # Create missing labels
            for label in required_labels:
                if label not in existing_labels:
                    color = label_definitions.get(label, "ededed")
                    label_data = {
                        "name": label,
                        "color": color,
                        "description": f"Auto-created label for {label}",
                    }

                    create_response = requests.post(
                        f"https://api.github.com/repos/{self.repo}/labels",
                        json=label_data,
                        headers=self.headers,
                    )

                    if create_response.status_code == 201:
                        print(f"✅ Created label: {label}")
                    else:
                        print(
                            f"⚠️  Could not create label {label}: {create_response.status_code}"
                        )

        except Exception as e:
            print(f"❌ Error managing labels: {e}")

    def run(self):
        """Execute the complete roadmap initialization"""
        print("\n📋 Step 1: Parsing roadmap data...")
        issues_data = self.parse_roadmap_file()

        if not issues_data:
            print("❌ No issues to create")
            return

        print("\n🏷️  Step 2: Ensuring labels exist...")
        all_labels = set()
        for issue in issues_data:
            all_labels.update(issue.get("labels", []))
        self.create_labels_if_missing(list(all_labels))

        print("\n🔍 Step 3: Checking for existing issues...")
        existing_titles = self.get_existing_issues()

        print("\n📝 Step 4: Creating GitHub issues...")
        created_issues = []

        for issue_data in issues_data:
            title = issue_data["title"]

            # Skip if issue already exists
            if title in existing_titles:
                print(f"⏭️  Skipping existing issue: {title}")
                continue

            issue = self.create_github_issue(issue_data)
            if issue:
                created_issues.append(issue)

        if not created_issues:
            print("i No new issues created")
            return

        print("\n🎯 Step 5: Adding issues to project board...")
        project_id = self.get_project_id()

        if project_id:
            for issue in created_issues:
                self.add_issue_to_project(issue["node_id"], project_id)
        else:
            print("⚠️  Could not add issues to project board - project not found")

        print("\n✅ Roadmap initialization complete!")
        print(f"📊 Created {len(created_issues)} new issues")
        if not self.test_mode:
            print(f"🔗 View issues: https://github.com/{self.repo}/issues")
            print(f"📋 View project: https://github.com/users/{self.owner}/projects")


def main():
    parser = argparse.ArgumentParser(description="Initialize roadmap issues on GitHub")
    parser.add_argument(
        "--test",
        "--dry-run",
        action="store_true",
        help="Run in test mode (no actual changes)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    try:
        initializer = RoadmapInitializer(test_mode=args.test)
        initializer.run()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
