# GitHub Issues Automation Scripts

This directory contains automation scripts for managing GitHub Issues and Project Boards.

## 🚀 populate_github_kanban.py

Automatically creates GitHub Issues from `ROADMAP_ISSUES.md` and assigns them to your GitHub Project Board.

### Features
- ✅ Parses ROADMAP_ISSUES.md into individual GitHub Issues
- ✅ Creates issues with proper labels and priorities
- ✅ Assigns issues to GitHub Project Board (when permissions allow)
- ✅ Dry-run mode for testing
- ✅ Comprehensive logging
- ✅ Rate limiting and error handling

### Prerequisites

```bash
# Install dependencies
pip install -r requirements-scripts.txt

# Ensure GitHub token is in .env
echo "GITHUB_TOKEN=your_github_token_here" >> .env
```

### Usage

```bash
# Test run (no changes made)
python scripts/populate_github_kanban.py --dry-run

# Create issues for real
python scripts/populate_github_kanban.py
```

### GitHub Token Requirements

Your GitHub token needs these scopes:
- `repo` - Full repository access
- `project` - Project board access (if you want automatic project assignment)

**Note:** Project board integration requires specific permissions and may not work with all token types.

### What it does

1. **Labels Creation:** Creates necessary priority and category labels
2. **Issue Parsing:** Extracts 16 issues from ROADMAP_ISSUES.md:
   - 7 High Priority issues
   - 5 Medium Priority issues
   - 3 Low Priority issues
   - 1 API access issue
3. **Issue Creation:** Creates GitHub Issues with proper:
   - Titles and descriptions
   - Priority labels (high-priority, medium-priority, low-priority)
   - Category labels (business, automation, ai, etc.)
   - Formatted acceptance criteria
4. **Project Assignment:** Attempts to add issues to Project Board #2

### Example Output

```
🚀 Starting GitHub Issues and Project Board automation
📋 Creating repository labels...
📖 Parsing roadmap file...
🔨 Creating 16 GitHub issues...
✅ Automation complete!
📊 Issues created: 16/16
```

### Troubleshooting

**"Project not accessible"**: This is normal - requires specific GitHub permissions. Issues will still be created successfully.

**"No issues found"**: Check that ROADMAP_ISSUES.md exists and has the correct format.

**Rate limiting**: The script includes automatic rate limiting (1 second between requests).

### Manual Project Board Setup

If automatic project assignment doesn't work, you can manually:
1. Go to https://github.com/users/IgorGanapolsky/projects/2
2. Add the created issues to appropriate columns
3. Filter by labels (high-priority, medium-priority, etc.)

### Daily Automation (Future)

This script can be integrated into GitHub Actions for daily synchronization:

```yaml
# .github/workflows/sync-kanban.yml
name: Sync Kanban Board
on:
  schedule:
    - cron: '0 9 * * *'  # Daily at 9 AM
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install -r requirements-scripts.txt
      - name: Sync Issues
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python scripts/populate_github_kanban.py
```
