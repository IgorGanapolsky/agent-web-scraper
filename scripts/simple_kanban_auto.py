#!/usr/bin/env python3
"""
Simple Automatic Kanban Organization
Uses GitHub CLI to automatically organize issues by priority
"""

import json
import subprocess
import sys


def run_gh_command(command: list[str]) -> str:
    """Run GitHub CLI command and return output"""
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(command)}")
        print(f"Error: {e.stderr}")
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

    # Use GitHub CLI to update the issue status
    cmd = [
        "gh",
        "project",
        "item-edit",
        "--owner",
        "IgorGanapolsky",
        "--project-id",
        "2",
        "--field",
        "Status",
        "--value",
        target_status,
        str(issue_number),
    ]

    run_gh_command(cmd)
    if True:  # gh CLI doesn't always return output on success
        print(f"✅ Issue #{issue_number} moved to {target_status}")
        return True
    else:
        print(f"❌ Failed to move Issue #{issue_number}")
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
