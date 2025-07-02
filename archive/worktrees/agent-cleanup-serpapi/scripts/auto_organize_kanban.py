#!/usr/bin/env python3
"""
Automatic Kanban Organization
Automatically moves issues to correct columns based on priority labels
"""

import os
import sys
import time
from typing import Optional

import requests
from dotenv import load_dotenv

load_dotenv()


class AutoKanbanOrganizer:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = "IgorGanapolsky"
        self.repo = "agent-web-scraper"
        self.project_number = 2  # Your project board number

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

        self.graphql_headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def get_project_data(self) -> Optional[dict]:
        """Get project data including field IDs"""
        query = """
        query($owner: String!, $number: Int!) {
            user(login: $owner) {
                projectV2(number: $number) {
                    id
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                            }
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
                    items(first: 100) {
                        nodes {
                            id
                            content {
                                ... on Issue {
                                    number
                                    title
                                    labels(first: 10) {
                                        nodes {
                                            name
                                        }
                                    }
                                }
                            }
                            fieldValues(first: 8) {
                                nodes {
                                    ... on ProjectV2ItemFieldSingleSelectValue {
                                        name
                                        field {
                                            ... on ProjectV2SingleSelectField {
                                                name
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"owner": self.owner, "number": self.project_number}

        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            timeout=60)

            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("user", {}).get("projectV2")
            else:
                print(f"❌ GraphQL query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ Error getting project data: {e}")
            return None

    def organize_issues_by_priority(self, project_data: dict) -> bool:
        """Automatically organize issues based on priority labels"""
        if not project_data:
            print("❌ No project data available")
            return False

        # Find the Status field and its options
        status_field = None
        status_options = {}

        for field in project_data["fields"]["nodes"]:
            if field["name"] == "Status" and "options" in field:
                status_field = field
                for option in field["options"]:
                    status_options[option["name"]] = option["id"]
                break

        if not status_field:
            print("❌ Status field not found in project")
            return False

        print(f"✅ Found Status field with options: {list(status_options.keys())}")

        # Map priority labels to status columns
        priority_mapping = {
            "high-priority": status_options.get("Todo", status_options.get("To Do")),
            "medium-priority": status_options.get(
                "In Progress", status_options.get("Backlog")
            ),
            "low-priority": status_options.get("Backlog", status_options.get("Done")),
        }

        # Process each item in the project
        updated_count = 0

        for item in project_data["items"]["nodes"]:
            if not item.get("content") or item["content"].get("__typename") != "Issue":
                continue

            issue = item["content"]
            issue_number = issue["number"]
            labels = [label["name"] for label in issue["labels"]["nodes"]]

            # Determine target status based on priority labels
            target_status_id = None
            priority_found = None

            for label in labels:
                if priority_mapping.get(label):
                    target_status_id = priority_mapping[label]
                    priority_found = label
                    break

            if not target_status_id:
                print(f"⚠️  Issue #{issue_number}: No priority label found")
                continue

            # Check current status
            current_status = None
            for field_value in item["fieldValues"]["nodes"]:
                if (
                    field_value.get("field", {}).get("name") == "Status"
                    and "name" in field_value
                ):
                    current_status = field_value["name"]
                    break

            # Update if status needs to change
            target_status_name = next(
                (name for name, id in status_options.items() if id == target_status_id),
                "Unknown",
            )

            if current_status != target_status_name:
                print(
                    f"🔄 Moving Issue #{issue_number} ({priority_found}) to {target_status_name}"
                )

                if self.update_item_status(
                    item["id"], status_field["id"], target_status_id
                ):
                    updated_count += 1
                    print(f"✅ Issue #{issue_number} moved successfully")
                else:
                    print(f"❌ Failed to move Issue #{issue_number}")

                # Rate limiting
                time.sleep(0.5)
            else:
                print(
                    f"✅ Issue #{issue_number} already in correct column ({current_status})"
                )

        print(f"\n🎉 Auto-organization complete! Updated {updated_count} issues")
        return True

    def update_item_status(self, item_id: str, field_id: str, option_id: str) -> bool:
        """Update an item's status field"""
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

        # We need the project ID - get it from project data
        project_id = self.get_project_id()
        if not project_id:
            return False

        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": {"singleSelectOptionId": option_id},
        }

        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": mutation, "variables": variables},
                headers=self.graphql_headers,
            timeout=60)

            if response.status_code == 200:
                data = response.json()
                return "errors" not in data
            else:
                print(f"❌ Mutation failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Error updating item status: {e}")
            return False

    def get_project_id(self) -> Optional[str]:
        """Get the project's global ID"""
        query = """
        query($owner: String!, $number: Int!) {
            user(login: $owner) {
                projectV2(number: $number) {
                    id
                }
            }
        }
        """

        variables = {"owner": self.owner, "number": self.project_number}

        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=self.graphql_headers,
            timeout=60)

            if response.status_code == 200:
                data = response.json()
                return (
                    data.get("data", {}).get("user", {}).get("projectV2", {}).get("id")
                )
            else:
                return None

        except Exception as e:
            print(f"❌ Error getting project ID: {e}")
            return None

    def run(self) -> bool:
        """Execute automatic Kanban organization"""
        print("🚀 Starting Automatic Kanban Organization...")
        print(f"📁 Repository: {self.owner}/{self.repo}")
        print(f"📋 Project: #{self.project_number}")

        # Get project data
        print("\n📊 Fetching project data...")
        project_data = self.get_project_data()

        if not project_data:
            print("❌ Failed to get project data")
            return False

        # Organize issues automatically
        print("\n🎯 Auto-organizing issues by priority...")
        success = self.organize_issues_by_priority(project_data)

        if success:
            print("\n✅ Automatic Kanban organization complete!")
            print("🎯 Issues organized by priority:")
            print("   • high-priority → Todo")
            print("   • medium-priority → In Progress/Backlog")
            print("   • low-priority → Backlog")
            return True
        else:
            print("\n❌ Auto-organization failed")
            return False


def main():
    if not os.getenv("GITHUB_TOKEN"):
        print("❌ GITHUB_TOKEN not found in environment variables")
        return 1

    organizer = AutoKanbanOrganizer()
    success = organizer.run()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
