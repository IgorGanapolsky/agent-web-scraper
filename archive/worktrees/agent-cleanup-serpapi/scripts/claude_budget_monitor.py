#!/usr/bin/env python3
"""
Claude Budget Monitor - Real-time token usage tracking and optimization
Prevents budget overruns and optimizes Claude 4 costs
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.claude_token_monitor import ClaudeTokenMonitor


def main():
    """Main budget monitoring dashboard"""
    monitor = ClaudeTokenMonitor()

    print("=" * 60)
    print("🤖 CLAUDE 4 BUDGET MONITOR")
    print("=" * 60)

    # Daily usage summary
    daily_spend = monitor.get_daily_spend()
    daily_budget = monitor.daily_budget

    print("\n💰 DAILY BUDGET STATUS")
    print(f"Daily Spend:     ${daily_spend:.4f}")
    print(f"Daily Budget:    ${daily_budget:.2f}")
    print(f"Remaining:       ${daily_budget - daily_spend:.4f}")
    print(f"Utilization:     {(daily_spend / daily_budget * 100):.1f}%")

    # Budget progress bar
    utilization = min((daily_spend / daily_budget) * 100, 100)
    bar_length = 30
    filled_length = int(bar_length * utilization / 100)
    bar = "█" * filled_length + "░" * (bar_length - filled_length)
    print(f"Progress: [{bar}] {utilization:.1f}%")

    # Weekly analytics
    analytics = monitor.get_usage_analytics(7)
    if "error" not in analytics:
        print("\n WEEKLY ANALYTICS")
        print(f"Total Requests:   {analytics['total_requests']}")
        print(f"Total Cost:       ${analytics['total_cost']:.4f}")
        print(f"Avg per Request:  ${analytics['avg_cost_per_request']:.4f}")
        print(f"Monthly Proj:     ${analytics['monthly_projection']:.2f}")

        # Model breakdown
        print("\n MODEL USAGE")
        for model, data in analytics["model_breakdown"].items():
            print(f"{model:15}: {data['requests']:3d} calls, ${data['cost']:.4f}")

        # Task breakdown
        print("\n TASK BREAKDOWN")
        for task, data in analytics["task_breakdown"].items():
            print(f"{task:15}: {data['requests']:3d} calls, ${data['cost']:.4f}")

    # Optimization recommendations
    recommendations = monitor.get_optimization_recommendations()
    if recommendations:
        print("\n OPTIMIZATION RECOMMENDATIONS")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    # Budget alerts
    if daily_spend > daily_budget * 0.9:
        print("\n BUDGET ALERT: 90% of daily budget used!")
        print("Consider switching to Claude 4 Sonnet for routine tasks")
    elif daily_spend > daily_budget * 0.7:
        print("\n  BUDGET WARNING: 70% of daily budget used")
        print("Monitor usage closely for remainder of day")
    else:
        print(f"\n BUDGET HEALTHY: {(daily_spend / daily_budget * 100):.1f}% used")

    # Claude 4 pricing reference
    print("\n CLAUDE 4 PRICING REFERENCE")
    print("Sonnet 4:  $3 input  / $15 output  (per 1M tokens)")
    print("Opus 4:    $15 input / $75 output  (per 1M tokens)")
    print("Tip: Use Sonnet for routine tasks, Opus for complex reasoning")

    print("=" * 60)

    # Export report if requested
    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"data/claude_usage_report_{timestamp}.json"
        monitor.export_usage_report(report_file)
        print(f" Report exported to {report_file}")


def setup_budget_alerts():
    """Set up automated budget alerts via n8n"""
    print("Setting up automated Claude budget alerts...")

    # n8n workflow configuration for Claude Budget Monitor
    # This workflow is configured in n8n and runs daily to monitor Claude API usage
    # It checks if we're on track to exceed our monthly budget and sends alerts if needed
    pass


def optimize_prompts():
    """Provide prompt optimization guidance"""
    print("\n PROMPT OPTIMIZATION TIPS")
    print("1. Use specific, concise prompts")
    print("2. Avoid redundant context in follow-up messages")
    print("3. Batch similar requests together")
    print("4. Use Claude 4 Sonnet for routine tasks")
    print("5. Reserve Opus 4 for complex reasoning only")
    print("6. Implement session memory to reduce context repetition")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup-alerts":
            setup_budget_alerts()
        elif sys.argv[1] == "--optimize":
            optimize_prompts()
        else:
            main()
    else:
        main()
