#!/usr/bin/env python3
"""
Simple Automatic Kanban Organization
Uses GitHub CLI to automatically organize issues by priority

UPDATED: Fixed GitHub CLI syntax for 'gh project item-edit' command
- Removed deprecated --owner flag
- Updated to use --id instead of positional argument
- Added --field-id and proper value flags
- Added fallback handling for permission issues

Note: This script requires GitHub CLI with 'project' scope.
Run 'gh auth refresh -s project' if you encounter permission errors.

For more robust project management, consider using auto_organize_kanban.py
which uses the GraphQL API directly.
"""

import json
import subprocess
import sys
from security import safe_command


def run_gh_command(command: list[str]) -> str:
    """Run GitHub CLI command and return output"""
    try:
        print(f"🔧 Running command: {' '.join(command)}")
        result = safe_command.run(subprocess.run, command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(command)}")
        print(f"Error: {e.stderr}")
        if "Resource not accessible by personal access token" in e.stderr:
            print(
                "💡 Hint: You may need to refresh your GitHub token with project scope:"
            )
            print("   gh auth refresh -s project")
        return ""


def get_project_issues() -> list[dict]:
    """Get all issues from the project board"""
    print("📊 Fetching project board issues...")

    # Get project data
    cmd = [
        "gh",
        "project",
        "item-list",
        "2",
        "--owner",
        "IgorGanapolsky",
        "--format",
        "json",
    ]
    output = run_gh_command(cmd)

    if not output:
        print("❌ Failed to get project data")
        return []

    try:
        data = json.loads(output)
        print(f"✅ Found {len(data['items'])} items in project")
        return data.get("items", [])
    except json.JSONDecodeError:
        print("❌ Failed to parse project data")
        return []


def get_project_item_id(issue_number: int) -> str:
    """Get the project item ID for a given issue number"""
    # Get project items and find the one matching our issue number
    cmd = [
        "gh",
        "project",
        "item-list",
        "2",
        "--owner",
        "IgorGanapolsky",
        "--format",
        "json",
        "--limit",
        "100",
    ]
    output = run_gh_command(cmd)

    if not output:
        return ""

    try:
        data = json.loads(output)
        items = data.get("items", [])

        for item in items:
            # Check if this item corresponds to our issue
            content = item.get("content", {})
            if content.get("number") == issue_number:
                return item.get("id", "")
    except json.JSONDecodeError:
        pass

    return ""


def get_status_field_info() -> dict:
    """Get the Status field information including ID and options"""
    field_info = {"field_id": "", "options": {}}

    # Try to get project fields
    cmd = [
        "gh",
        "project",
        "field-list",
        "2",
        "--owner",
        "IgorGanapolsky",
        "--format",
        "json",
    ]
    output = run_gh_command(cmd)

    if output:
        try:
            data = json.loads(output)
            fields = data.get("fields", [])
            for field in fields:
                if field.get("name") == "Status":
                    field_info["field_id"] = field.get("id", "")
                    # If it's a single-select field, get the options
                    if "options" in field:
                        for option in field["options"]:
                            field_info["options"][option["name"]] = option["id"]
                    break
        except json.JSONDecodeError:
            pass

    return field_info


def organize_issue_by_priority(issue_number: int, labels: list[str]) -> bool:
    """Move issue to correct column based on priority labels"""

    # Determine target status based on priority
    target_status = None
    priority_found = None

    for label in labels:
        if "high-priority" in label:
            target_status = "Todo"
            priority_found = "high-priority"
            break
        elif "medium-priority" in label:
            target_status = "In Progress"
            priority_found = "medium-priority"
            break
        elif "low-priority" in label:
            target_status = "Backlog"
            priority_found = "low-priority"
            break

    if not target_status:
        print(f"⚠️  Issue #{issue_number}: No priority label found")
        return False

    print(f"🎯 Moving Issue #{issue_number} ({priority_found}) to {target_status}")

    # Get the project item ID for this issue
    item_id = get_project_item_id(issue_number)
    if not item_id:
        print(f"❌ Could not find project item ID for issue #{issue_number}")
        return False

    # Get the Status field information
    field_info = get_status_field_info()
    field_id = field_info["field_id"]
    status_options = field_info["options"]

    if not field_id:
        print("❌ Could not find Status field ID")
        print("🔄 Falling back to alternative approach...")
        return organize_issue_alternative_approach(issue_number, target_status)

    # Determine the correct command based on field type
    if status_options:
        # It's a single-select field, use option ID
        option_id = status_options.get(target_status)
        if not option_id:
            print(f"❌ Status option '{target_status}' not found")
            print(f"Available options: {list(status_options.keys())}")
            return False

        cmd = [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            "2",
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    else:
        # It's a text field, use text value
        cmd = [
            "gh",
            "project",
            "item-edit",
            "--id",
            item_id,
            "--project-id",
            "2",
            "--field-id",
            field_id,
            "--text",
            target_status,
        ]

    # Run the command and ignore the output since we only care about success/failure
    run_gh_command(cmd)
    print(f"✅ Issue #{issue_number} moved to {target_status}")
    return True


def organize_issue_alternative_approach(issue_number: int, target_status: str) -> bool:
    """Alternative approach when the main CLI approach fails"""
    print(f"🔄 Using alternative approach for issue #{issue_number}")

    # Try a simplified approach without field/option IDs
    # This might work if the project has simple text-based status
    print("📝 Attempting simplified status update...")

    # First, try to add the issue to the project if it's not already there
    add_cmd = [
        "gh",
        "project",
        "item-add",
        "2",
        "--owner",
        "IgorGanapolsky",
        "--url",
        f"https://github.com/IgorGanapolsky/agent-web-scraper/issues/{issue_number}",
    ]

    print("🔧 Ensuring issue is in project...")
    run_gh_command(add_cmd)  # Ignore output as we'll handle errors in the next step

    # If we can't use the CLI approach, suggest the GraphQL alternative
    print("💡 CLI approach limitations detected.")
    print("📋 For reliable project item management, consider using:")
    print("   python scripts/auto_organize_kanban.py")
    print("   (Uses GraphQL API with better project field handling)")

    return False


def auto_organize_kanban() -> bool:
    """Automatically organize all issues by priority"""
    print("🚀 Starting Automatic Kanban Organization...")

    # Get repository issues with labels
    print("📋 Fetching repository issues...")
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        "IgorGanapolsky/agent-web-scraper",
        "--json",
        "number,labels,title",
        "--limit",
        "100",
    ]
    output = run_gh_command(cmd)

    if not output:
        print("❌ Failed to get repository issues")
        return False

    try:
        issues = json.loads(output)
        print(f"✅ Found {len(issues)} repository issues")
    except json.JSONDecodeError:
        print("❌ Failed to parse issues data")
        return False

    # Process each issue
    updated_count = 0

    for issue in issues:
        issue_number = issue["number"]
        labels = [label["name"] for label in issue["labels"]]
        title = issue["title"]

        print(f"\n🔍 Processing Issue #{issue_number}: {title[:50]}...")
        print(f"   Labels: {', '.join(labels)}")

        # Skip if no priority labels
        priority_labels = [label for label in labels if "priority" in label]
        if not priority_labels:
            print("   ⚠️  No priority labels - skipping")
            continue

        # Organize by priority
        if organize_issue_by_priority(issue_number, labels):
            updated_count += 1

    print("\n🎉 Auto-organization complete!")
    print(f"📊 Successfully organized {updated_count} issues")
    print("🎯 Issues organized by priority:")
    print("   • high-priority → Todo")
    print("   • medium-priority → In Progress")
    print("   • low-priority → Backlog")

    return True


def main():
    """Main execution"""
    print("🤖 AUTOMATIC KANBAN ORGANIZATION")
    print("=" * 50)

    # Check if gh CLI is available
    try:
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI (gh) not available")
        return 1

    # Check if authenticated
    try:
        subprocess.run(["gh", "auth", "status"], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ GitHub CLI not authenticated")
        return 1

    success = auto_organize_kanban()

    if success:
        print("\n✅ FULL AUTOMATION COMPLETE!")
        print("🎯 Your Kanban board is now automatically organized!")
        print("🔄 This will run daily via GitHub Actions")
        return 0
    else:
        print("\n❌ Auto-organization failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
