# Example: Cost-Effective Claude Prompt Using Source Maps

## The Problem
Without source maps, your Claude prompt might include 1000+ files = 40,000+ tokens = $$$$

## The Solution
With source maps, your Claude prompt includes only relevant files = 500-2,000 tokens = $

## Example Workflow

### 1. Generate Focused Source Map
```bash
# In bare repo: Only get API files (12 files vs 1000+)
./generate_src_map.sh main api_map.txt app/api/
```

### 2. Create Minimal Claude Prompt
```bash
# In your worktree
cat << 'EOF' > claude_prompt.txt
Hi Claude! I need to add a new API endpoint for user analytics.

Here are the existing API files in this project:

$(cat api_map.txt)

Based on the existing pattern in app/api/insights.py, please create:
- app/api/user_analytics.py

The new endpoint should:
- Accept GET /api/user-analytics 
- Return JSON with user metrics
- Follow the same auth pattern as insights.py

Please provide the complete code for the new file.
EOF
```

### 3. Token Count Comparison

**Without Source Maps (Old Method):**
- Full project context: 40,000+ tokens
- Cost: High $$$$

**With Source Maps (New Method):**
- Only API files: ~500 tokens
- API file list: ~200 tokens  
- Your instructions: ~200 tokens
- **Total: ~900 tokens = 95%+ savings!**

## Available Source Map Filters

| Filter | Files | Use Case | Token Savings |
|--------|-------|----------|---------------|
| `app/api/` | 12 files | API endpoints | 98% reduction |
| `app/core/` | 56 files | Business logic | 95% reduction |
| `app/services/` | 10 files | Service layer | 98% reduction |
| `scripts/` | 55 files | Automation | 95% reduction |
| `tests/` | 20 files | Testing | 97% reduction |

## Real Examples

### Adding New API Endpoint
```bash
./generate_src_map.sh main api_map.txt app/api/
# Result: 12 files, ~500 tokens vs 40,000+
```

### Fixing Core Business Logic  
```bash
./generate_src_map.sh main core_map.txt app/core/
# Result: 56 files, ~2,000 tokens vs 40,000+
```

### Adding New Service
```bash
./generate_src_map.sh main services_map.txt app/services/
# Result: 10 files, ~400 tokens vs 40,000+
```

## Cost Impact

For your agent-web-scraper project:
- **Before**: 40,000+ tokens per Claude interaction
- **After**: 500-2,000 tokens per Claude interaction  
- **Savings**: 95%+ cost reduction
- **ROI**: Script pays for itself immediately

## Pro Tips

1. **Be Specific**: Use narrow filters (`app/api/` not `app/`)
2. **Single Purpose**: One feature per worktree
3. **Relevant Only**: Include only files Claude needs to understand
4. **Test First**: Verify your source map has the right files before sending to Claude