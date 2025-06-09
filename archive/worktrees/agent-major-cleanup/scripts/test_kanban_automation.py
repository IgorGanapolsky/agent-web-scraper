#!/usr/bin/env python3
"""
Test script for Kanban automation
Run this to validate the automation setup
"""

import os
import sys

from dotenv import load_dotenv


def test_environment():
    """Test environment setup"""
    print("🧪 Testing Kanban Automation Environment")
    print("=" * 50)

    # Load environment
    load_dotenv()

    # Check requirements
    tests = {
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN") is not None,
        "ROADMAP_ISSUES.md": os.path.exists("ROADMAP_ISSUES.md"),
        "populate_github_kanban.py": os.path.exists(
            "scripts/populate_github_kanban.py"
        ),
        "enhanced_kanban_sync.py": os.path.exists("scripts/enhanced_kanban_sync.py"),
        "sync-kanban-board.yml": os.path.exists(
            ".github/workflows/sync-kanban-board.yml"
        ),
        "requirements-scripts.txt": os.path.exists("requirements-scripts.txt"),
    }

    all_passed = True
    for test_name, result in tests.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if not result:
            all_passed = False

    print("\n📋 Automation Setup Summary:")
    if all_passed:
        print("✅ All tests passed! Automation is ready to run.")
        print("\n🚀 To trigger automation:")
        print("1. Push to main branch (triggers on schedule/workflow_dispatch)")
        print("2. Go to Actions tab → 'Sync Kanban Board with Issues' → 'Run workflow'")
        print("3. Or wait for daily scheduled run at 10 AM UTC")
    else:
        print("❌ Some tests failed. Please fix the issues above.")

    print("\n📖 Manual fallback available:")
    print("- Run: python scripts/enhanced_kanban_sync.py --dry-run")
    print("- Or: python scripts/populate_github_kanban.py --dry-run")

    return all_passed


if __name__ == "__main__":
    success = test_environment()
    sys.exit(0 if success else 1)
