# run_formatter.py

import os
import sys
import anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# === Load the input summary ===
input_file = sys.argv[1] if len(sys.argv) > 1 else "temp/raw_summary.txt"
with open(input_file, "r") as f:
    raw_input = f.read()

# === Claude Prompt (ReAct + CoT fusion) ===
prompt = f"""
You are an expert content strategist for SaaS newsletters.

Your task is to refine the following Reddit pain point summary into a polished newsletter segment.

Include:
1. 🔥 An engaging headline
2. 🧠 A 3-bullet pain point list (clear + sharp)
3. 📊 A paragraph explaining relevance
4. 📬 A CTA to subscribe or purchase

Avoid generic phrasing. Be concise and punchy.

---

Input pain summary:
{raw_input}

---

Output your response in Markdown.
"""

# === Claude API Setup ===
client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0.7,
    messages=[
        {"role": "user", "content": prompt}
    ]
)

final_output = response.content[0].text

# === Save the result ===
os.makedirs("output", exist_ok=True)
with open("output/formatted_newsletter.md", "w") as f:
    f.write(final_output)

print("✅ Claude formatting complete. Output saved to output/formatted_newsletter.md")