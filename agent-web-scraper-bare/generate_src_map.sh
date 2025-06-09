#!/bin/bash

# Generate source map for agent-web-scraper worktrees
# Usage: ./generate_src_map.sh [BRANCH] [OUTPUT_FILE] [DIRECTORY_FILTER]
# Examples:
#   ./generate_src_map.sh main app_map.txt app/
#   ./generate_src_map.sh feature/csv-writer csv_map.txt app/core/
#   ./generate_src_map.sh main scripts_map.txt scripts/

BRANCH=${1:-main}
OUTPUT_FILE=${2:-src_map.txt}
DIR_FILTER=${3:-app/}

echo "🔍 Fetching latest changes from origin..."
git fetch origin

# Try different ref formats
if git rev-parse --verify origin/$BRANCH >/dev/null 2>&1; then
    REF="origin/$BRANCH"
elif git rev-parse --verify refs/remotes/origin/$BRANCH >/dev/null 2>&1; then
    REF="refs/remotes/origin/$BRANCH" 
elif git rev-parse --verify $BRANCH >/dev/null 2>&1; then
    REF="$BRANCH"
else
    echo "❌ Error: Cannot find branch $BRANCH"
    echo "Available branches:"
    git branch -a | head -10
    exit 1
fi

echo "📝 Generating src map from $REF for directory: $DIR_FILTER"

# Generate the source map with filtering
if [ "$DIR_FILTER" = "app/" ]; then
    # For app directory, include Python files and key configs
    git ls-tree -r --name-only $REF | grep -E "^(app/|scripts/|tests/)" | grep -E "\.(py|yaml|yml|json)$" | sort > $OUTPUT_FILE
elif [ "$DIR_FILTER" = "all" ]; then
    # Include all source files (exclude data, logs, cache)
    git ls-tree -r --name-only $REF | grep -v -E "^(data/|logs/|\.git/|venv/|__pycache__/|\.pytest_cache/)" | sort > $OUTPUT_FILE
else
    # Custom directory filter
    git ls-tree -r --name-only $REF | grep "^$DIR_FILTER" | sort > $OUTPUT_FILE
fi

FILE_COUNT=$(cat $OUTPUT_FILE | wc -l)
echo "✅ Generated $OUTPUT_FILE from $REF"
echo "📊 File count: $FILE_COUNT files in $DIR_FILTER"
echo ""

# Show file breakdown by type
echo "=== FILE TYPE BREAKDOWN ==="
if [ -s $OUTPUT_FILE ]; then
    echo "Python files: $(grep '\.py$' $OUTPUT_FILE | wc -l)"
    echo "Config files: $(grep -E '\.(yaml|yml|json)$' $OUTPUT_FILE | wc -l)"
    echo "Documentation: $(grep '\.md$' $OUTPUT_FILE | wc -l)"
    echo "Other files: $(grep -v -E '\.(py|yaml|yml|json|md)$' $OUTPUT_FILE | wc -l)"
else
    echo "No files found matching filter: $DIR_FILTER"
fi
echo ""

echo "=== LATEST COMMIT DETAILS ==="
git log -1 --pretty=format:"Commit: %H%nAuthor: %an <%ae>%nDate: %ad%nTitle: %s%nBody:%n%b" --date=format:"%Y-%m-%d %H:%M:%S %Z" $REF
echo ""
echo ""

echo "=== FILES CHANGED IN LATEST COMMIT ==="
git show --stat --pretty="" $REF | head -20
echo ""

echo "=== COMMIT SUMMARY ==="
git show --oneline --name-only $REF | head -15
echo ""

# Only show detailed instructions if run without arguments or with --help
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo ""
    echo "=== WORKTREE USAGE INSTRUCTIONS ==="
    echo "💡 To use this src map in a worktree for Claude:"
    echo "1. Create worktree: git worktree add ../agent-feature-name $BRANCH"
    echo "2. Copy this script: cp generate_src_map.sh ../agent-feature-name/"
    echo "3. In worktree: ./generate_src_map.sh $BRANCH feature_map.txt app/core/"
    echo "4. Send feature_map.txt contents to Claude with minimal context"
    echo ""

    echo "=== COST OPTIMIZATION TIPS ==="
    echo "🔥 For maximum token savings:"
    echo "- Use specific directory filters (app/core/, app/api/, etc.)"
    echo "- Focus on single feature areas"
    echo "- Include only files Claude needs to see"
    echo ""

    echo "=== AVAILABLE FILTERS & EXAMPLES ==="
    echo "🔹 app/           - All application code (default)"
    echo "   Example: ./generate_src_map.sh main app_map.txt app/"
    echo ""
    echo "🔹 app/core/      - Core business logic only (56 files)"
    echo "   Example: ./generate_src_map.sh main core_map.txt app/core/"
    echo ""
    echo "🔹 app/api/       - API endpoints only (12 files)"
    echo "   Example: ./generate_src_map.sh main api_map.txt app/api/"
    echo ""
    echo "🔹 app/services/  - Service layer only (~10 files)"
    echo "   Example: ./generate_src_map.sh main services_map.txt app/services/"
    echo ""
    echo "🔹 scripts/       - Automation scripts only (~55 files)"
    echo "   Example: ./generate_src_map.sh main scripts_map.txt scripts/"
    echo ""
    echo "🔹 tests/         - Test files only (~20 files)"
    echo "   Example: ./generate_src_map.sh main tests_map.txt tests/"
    echo ""
    echo "🔹 all            - All source files (excluding data/logs)"
    echo "   Example: ./generate_src_map.sh main full_map.txt all"
    echo ""
    echo "💡 WORKFLOW EXAMPLE:"
    echo "1. ./generate_src_map.sh feature/csv-writer api_map.txt app/api/"
    echo "2. git worktree add ../agent-csv-writer feature/csv-writer"
    echo "3. cp api_map.txt ../agent-csv-writer/"
    echo "4. Send api_map.txt contents to Claude with minimal context"
    
    # Exit after showing help
    if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        exit 0
    fi
fi