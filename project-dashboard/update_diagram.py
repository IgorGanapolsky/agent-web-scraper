# /project-dashboard/update_diagram.py
# Script to auto-generate AI business roadmap diagram from kanban.json

import json
from datetime import datetime

from graphviz import Digraph

# Load Kanban data
with open("project-dashboard/kanban.json") as f:
    board = json.load(f)

# Initialize Graphviz Digraph
diagram = Digraph("AI Market Research Agent", format="png")
diagram.attr(rankdir="LR", size="8,5")

# Column colors
colors = {
    "Input Sources": "lightblue",
    "Processing Pipelines": "lightgreen",
    "Outputs": "lightyellow",
    "Automation/Infra": "lightgrey",
    "Business Outcomes": "lightsalmon",
}

# Add Nodes by Column
depth = 0
for col, cards in board.items():
    with diagram.subgraph(name=f"cluster_{col}") as c:
        c.attr(label=col, style="filled", color=colors.get(col, "white"))
        for card in cards:
            if not isinstance(card, dict):
                continue
            status = card.get("status", "")
            label = f"{card.get('title', 'Untitled')}\n[{status}]"
            color = {
                "Completed": "#a0ffa0",
                "In-progress": "#fffda0",
                "Planned": "#ccccee",
                "Future": "#eeeeee",
            }.get(status, "white")
            c.node(
                card.get("id", "unknown_id"),
                label=label,
                style="filled",
                fillcolor=color,
            )

# Add basic edges (customize later if needed)
diagram.edge("reddit", "scraper")
diagram.edge("scraper", "summarizer")
diagram.edge("summarizer", "pain_points")
diagram.edge("pain_points", "email_digest")
diagram.edge("email_digest", "cold_emails")
diagram.edge("cold_emails", "responses")
diagram.edge("responses", "appointments")
diagram.edge("appointments", "revenue")

# Output file
now = datetime.now().strftime("%Y-%m-%d")
diagram.render(filename=f"project-dashboard/ai-business-roadmap-{now}", cleanup=True)
print(f"✅ Diagram updated: ai-business-roadmap-{now}.png")
