# 🧠 CLAUDE PERMANENT MEMORY

## ⚠️ CRITICAL WORKTREE RULES

### **NEVER DELETE WORKTREE DIRECTORIES**
- `langchain/` - ACTIVE WORKTREE - DO NOT DELETE
- `agent-*` directories - These are Git worktrees for parallel development
- Always check `git worktree list` before removing any directories
- Worktrees are essential for the Git Worktree cost-saving development method

### **WORKTREE IDENTIFICATION**
```bash
# Always run this before cleanup operations:
git worktree list

# Look for directories that might be worktrees:
- langchain/
- agent-*
- Any directory mentioned in git worktree list
```

### **WHY WORKTREES MATTER**
- Save 95%+ on Claude token costs by working in isolated contexts
- Enable parallel development on different features
- Each worktree is a separate working directory for a specific branch
- Deleting worktrees breaks the development workflow

### **SAFE CLEANUP PROTOCOL**
1. Always check `git worktree list` first
2. Never delete directories that appear in worktree list
3. Never delete directories starting with `agent-` without verification
4. When in doubt, ASK the user before deleting any directory

### **MISTAKE MADE**
On 2025-06-09, I accidentally deleted the `langchain/` worktree directory. 
This was a critical error that broke an active development workflow.
This memory file prevents future occurrences.

---
**This file ensures Claude remembers worktree safety across all sessions.**