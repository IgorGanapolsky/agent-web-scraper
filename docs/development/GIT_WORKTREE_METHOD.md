# Git Worktree Method: Cost-Effective Development

## Overview
The Git Worktree method allows you to work on features in isolated directories, dramatically reducing token costs when working with LLMs like Claude.

## Cost Comparison

### Traditional Method (Expensive)
```
Token Count: ~40,000+ characters
- Full project structure
- All files included in context
- Multiple directories (CEO/, CFO/, CMO/, CTO/)
- Documentation files
- Configuration files
Cost: High $$$$
```

### Git Worktree Method (Cheap)
```
Token Count: ~500-2,000 characters
- Only relevant files
- Isolated feature context
- Minimal prompt structure
Cost: Low $
```

## Implementation Steps

### Step 1: Create Feature Branch and Worktree
```bash
# Create new branch for the feature
git switch -c feature/csv-writer

# Create separate, clean directory (worktree) for this feature
git worktree add ../agent-scraper-csv-writer feature/csv-writer
```

### Step 2: Work in Isolated Environment
```bash
# Navigate to isolated workspace
cd ../agent-scraper-csv-writer

# Your terminal is now focused only on this feature
# All other project files are out of sight
```

### Step 3: Create Minimal, Cost-Effective Prompt
```bash
# Use heredoc for clean multi-line prompt
cat << 'EOF' > claude_prompt.txt
Hello Claude. I am adding a new CsvWriterAgent to my agentic web scraper.

This new agent will receive data from the ScraperAgent. Here is the code for the ScraperAgent so you can see what the data format looks like:

$(cat app/core/scraper.py)

I need you to write the code for a new file, app/core/csv_writer_agent.py.
It should have a class CsvWriterAgent with a method write_to_csv(data, filename).
The data will be the dictionary returned by the ScraperAgent.
Please provide the complete Python code for the new file.
EOF
```

### Step 4: Send Focused Prompt to Claude
- Copy the minimal prompt content
- Send to Claude (claude.ai, API, or VS Code extension)
- Receive targeted code response
- No unnecessary context, dramatically lower costs

### Step 5: Implement and Test
```bash
# Create the new file with Claude's response
# Test the implementation
# Commit when ready
git add .
git commit -m "Add CsvWriterAgent for data export functionality"
```

### Step 6: Merge Back to Main
```bash
# Switch back to main project
cd ../agent-web-scraper
git switch main

# Merge the feature
git merge feature/csv-writer

# Clean up worktree when done
git worktree remove ../agent-scraper-csv-writer
git branch -d feature/csv-writer
```

## Workflow Management Commands

### List All Worktrees
```bash
git worktree list
```

### Remove Worktree
```bash
git worktree remove ../agent-scraper-csv-writer
```

### Prune Stale Worktrees
```bash
git worktree prune
```

## Benefits

1. **Cost Reduction**: 95%+ reduction in token usage
2. **Focus**: Only relevant code in context
3. **Organization**: Clean separation of features
4. **Safety**: No accidental inclusion of unrelated files
5. **Efficiency**: Faster development cycles

## Real Example: CsvWriterAgent

Current worktree setup for CSV writer feature:
- Main project: `/Users/igorganapolsky/workspace/git/agent-web-scraper`
- Feature worktree: `/Users/igorganapolsky/workspace/git/agent-scraper-csv-writer`
- Branch: `feature/csv-writer`

This isolated environment contains only the files needed for the CSV writer feature, resulting in minimal token usage when working with Claude.

## Best Practices

1. **One Feature Per Worktree**: Keep features isolated
2. **Minimal Context**: Only include necessary files in prompts
3. **Clean Commits**: Make focused, single-purpose commits
4. **Regular Cleanup**: Remove worktrees after merging
5. **Descriptive Names**: Use clear worktree and branch names

## Complete Workflow Example

### Act as Developer (Hat #1)
```bash
# 1. Create isolated environment
git worktree add ../my-new-feature feature/new-feature
cd ../my-new-feature

# 2. Prepare cheap prompt
echo "Claude, please write a new agent based on this existing one:" > my_prompt.txt
cat app/core/scraper.py >> my_prompt.txt

# 3. Use Regular Claude: Copy my_prompt.txt contents to claude.ai
# 4. Save Claude's response as new file
# 5. Test and commit
git add .
git commit -m "Add new feature agent"

# 6. Merge back to main
cd ../agent-web-scraper
git switch main
git merge feature/new-feature
git worktree remove ../my-new-feature
```

### Act as Operator (Hat #2)
```bash
# Now use your improved agentic system
python main.py --prompt "Do the new thing I just built!"
```

## Two Distinct Roles

**Developer/Architect Role:**
- Use Git Worktree method to develop code cheaply
- Work with Regular Claude for code generation
- Focus on building and improving the system

**Operator/User Role:**
- Run the finished agentic system
- Your custom agents (PlannerAgent, ScraperAgent, etc.) handle the AI calls
- Execute complex tasks automatically

## Cost Impact

For a project like agent-web-scraper:
- **Without Worktree**: 40,000+ tokens per prompt
- **With Worktree**: 500-2,000 tokens per prompt
- **Savings**: 95%+ reduction in AI costs

This method pays for itself immediately and scales with project size.

## Key Insight

**Don't give development commands to your agents!** Your CTOAgent is designed for task execution, not self-modification. Use the Git Worktree method for development, then use your agents for operational tasks.

## Advanced Tips & Best Practices

### Parallel Development
- **Independent File States**: Each worktree maintains its own file state
- **No Interference**: Changes in one worktree won't affect others
- **Parallel Claude Sessions**: Run multiple Claude Code sessions simultaneously
- **Shared Git History**: All worktrees share the same Git history and remotes

### Long-Running Tasks
```bash
# Worktree 1: Claude working on feature A
git worktree add ../agent-feature-a feature/feature-a

# Worktree 2: You continue development on feature B
git worktree add ../agent-feature-b feature/feature-b
```

### Descriptive Naming Conventions
```bash
# Good examples
git worktree add ../agent-csv-export feature/csv-export
git worktree add ../agent-pdf-generator feature/pdf-generator
git worktree add ../agent-bugfix-scraper bugfix/scraper-timeout

# Clear identification of purpose
```

### Environment Setup Per Worktree

#### Python Projects (like agent-web-scraper)
```bash
cd ../new-worktree

# Option 1: Create new virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Option 2: Use existing venv (if shared)
source ../agent-web-scraper/venv/bin/activate
```

#### JavaScript Projects
```bash
cd ../new-worktree

# Install dependencies
npm install
# or
yarn install

# Set up development environment
npm run dev
```

### Workflow Management

#### Active Worktree Tracking
```bash
# List all worktrees with status
git worktree list

# Check which branch each worktree is on
git branch -vv
```

#### Clean Development Cycles

**You (Project Manager/Architect) prepare the workspace:**
```bash
# 1. YOU create the clean workspace for Claude
git worktree add ../agent-task-name feature/task-name

# 2. YOU set up the environment  
cd ../agent-task-name
source venv/bin/activate  # Python
pip install -e .          # Install project in development mode

# 3. YOU prepare the minimal prompt for Claude
echo "Claude, implement X based on:" > prompt.txt
cat relevant_file.py >> prompt.txt

# 4. YOU send the prompt to Claude (claude.ai)
# 5. YOU receive the code and save it
# 6. YOU test the implementation
python -m pytest tests/

# 7. YOU commit and merge
git add .
git commit -m "Implement task-name feature"

# 8. YOU return to main project and clean up
cd ../agent-web-scraper
git merge feature/task-name
git worktree remove ../agent-task-name
git branch -d feature/task-name
```

**The Key Insight:**
- **You (Igor)**: Project Manager who prepares clean workspaces
- **Claude**: Brilliant programmer who works in the prepared space
- **Git Worktree**: The clean, isolated office you prepare for Claude

## Real-World Example: Tower Screenshot Workflow

**Your Tower View (Project Manager Perspective):**
```
Branches:
├── main (HEAD)
├── feature/csv-writer
├── fix-sonarqube-setup  
├── fleet-local-history
└── [multiple other features]
```

**When You Want to Add a New Feature (e.g., "add-json-output"):**

1. **You See the Big Picture** (In Tower):
   - All branches visible in left panel
   - Managing multiple streams of work
   - Project overview and commit history

2. **You Decide to Work on New Feature**:
   - Choose next feature: "add-json-output"
   - Plan the implementation approach

3. **You Prepare the Workspace** (The Worktree):
   ```bash
   # Create new branch in Tower or terminal
   git switch -c feature/add-json-output
   
   # Create isolated worktree
   git worktree add ../agent-scraper-json-output feature/add-json-output
   
   # Navigate to clean workspace  
   cd ../agent-scraper-json-output
   ```

4. **You Invite Claude into Clean Workspace**:
   ```bash
   # Prepare minimal, cost-effective prompt
   echo "Claude, please write a new agent that outputs JSON, based on:" > prompt.txt
   cat app/core/scraper.py >> prompt.txt
   ```

5. **You Talk to Regular Claude**:
   - Go to claude.ai (or API tool)
   - Paste minimal prompt
   - Claude sees only the clean context you provided
   - Claude has no idea about git branches or worktrees

6. **You Put the Work in Place**:
   - Take code from Claude
   - Save in appropriate files
   - Use Tower to commit changes to `feature/add-json-output`
   - Merge when ready

**The Result**: Clean separation of project management (you) and programming (Claude)

### Cost Optimization Strategies

#### Context Size Management
```bash
# Before sending to Claude, check context size
wc -c my_prompt.txt

# Keep prompts under 2,000 characters for maximum savings
```

#### Selective File Inclusion
```bash
# Include only necessary files
echo "Claude, implement X based on:" > prompt.txt
echo "Core module:" >> prompt.txt
cat app/core/scraper.py >> prompt.txt
echo "Related test:" >> prompt.txt
cat tests/test_scraper.py >> prompt.txt
```

### Integration with agent-web-scraper

Your project structure supports this perfectly:
- **CEO/**: Strategic planning worktrees
- **CFO/**: Financial feature worktrees  
- **CMO/**: Marketing automation worktrees
- **CTO/**: Technical implementation worktrees

Each role can have dedicated worktrees without interference.