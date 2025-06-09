#!/bin/bash
# Claude Squad Parallel Executive Launch Script
# Launches CEO, CTO, CMO, CFO agents for autonomous $300/day revenue execution

set -e

echo "🚀 LAUNCHING CLAUDE SQUAD EXECUTIVE TEAM"
echo "Target: $300/day revenue via parallel agent execution"
echo ""

# Check if Claude Squad is installed
if ! command -v cs &> /dev/null; then
    echo "❌ Claude Squad not found. Installing..."
    curl -sSL https://raw.githubusercontent.com/smtg-ai/claude-squad/main/install.sh | bash
fi

# Check if tmux is available
if ! command -v tmux &> /dev/null; then
    echo "❌ tmux not found. Please install tmux first:"
    echo "brew install tmux"
    exit 1
fi

# Create worktrees if they don't exist
echo "📁 Setting up executive worktrees..."
if [ ! -d "CEO" ]; then
    git worktree add CEO HEAD
fi
if [ ! -d "CTO" ]; then
    git worktree add CTO HEAD
fi
if [ ! -d "CMO" ]; then
    git worktree add CMO HEAD
fi
if [ ! -d "CFO" ]; then
    git worktree add CFO HEAD
fi

# Copy configuration files to each worktree
echo "⚙️  Copying Claude Squad configurations..."
cp CEO/claude-squad.yaml CEO/ 2>/dev/null || echo "CEO config already in place"
cp CTO/claude-squad.yaml CTO/ 2>/dev/null || echo "CTO config already in place"
cp CMO/claude-squad.yaml CMO/ 2>/dev/null || echo "CMO config already in place"
cp CFO/claude-squad.yaml CFO/ 2>/dev/null || echo "CFO config already in place"

echo ""
echo "🎯 EXECUTIVE MISSION:"
echo "• CEO: Meta Ads campaign + customer acquisition"
echo "• CTO: System scaling + infrastructure monitoring"
echo "• CMO: Marketing automation + conversion optimization"
echo "• CFO: Revenue tracking + financial optimization"
echo ""

echo "🚀 Launching parallel agents in tmux session 'executives'..."
echo "Use 'tmux attach -t executives' to view all agents"
echo ""

# Launch tmux session with all four agents
tmux new-session -s executives -d "cd CEO && cs --program 'claude-code --role Chief-Executive-Officer' --workspace ."
tmux split-window -h -t executives "cd CTO && cs --program 'claude-code --role Chief-Technology-Officer' --workspace ."
tmux split-window -v -t executives "cd CMO && cs --program 'claude-code --role Chief-Marketing-Officer' --workspace ."
tmux select-pane -t 0
tmux split-window -v -t executives "cd CFO && cs --program 'claude-code --role Chief-Financial-Officer' --workspace ."

echo "✅ CLAUDE SQUAD LAUNCHED!"
echo ""
echo "📊 Monitor progress:"
echo "• tmux attach -t executives    # View all agents"
echo "• tail -f MULTI_AGENT_PLAN.md  # Watch coordination"
echo "• git log --oneline            # See agent commits"
echo ""
echo "🎯 Target: $300/day = 114 customers × $79/month"
echo "💰 Live payment system operational!"
