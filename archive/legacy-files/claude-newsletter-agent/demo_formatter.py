# demo_formatter.py - Mock Claude formatter for testing

import os
import sys

# === Load the input summary ===
input_file = sys.argv[1] if len(sys.argv) > 1 else "temp/raw_summary.txt"
with open(input_file, "r") as f:
    raw_input = f.read()

print(f"📥 Input received ({len(raw_input)} characters)")
print(f"Raw input: {raw_input[:100]}...")

# === Mock Claude output (newsletter-ready format) ===
mock_newsletter = """# 🚨 Why Your AI Onboarding Tools Are Sabotaging Customer Success

• **Intent mapping disasters** - AI routes "I need help" to billing instead of support  
• **Rigid automation breaks** - Chatbots fail the moment users go off-script  
• **Trust-killing hallucinations** - GPT gives wrong product info, confusing customers

**The Reality Check**: Reddit founders are sharing brutal truths about AI onboarding failures. While competitors ship cookie-cutter bots, the companies solving flexible automation and reliable intent detection will dominate user activation. These aren't just UX hiccups—they're revenue killers in disguise.

**[Download the Complete Reddit Pain Point Analysis →](https://saasgrowthdispatch.com/ai-onboarding-report)** *(One-time purchase • Implementation roadmap included)*
"""

# === Save the result ===
os.makedirs("output", exist_ok=True)
with open("output/formatted_newsletter.md", "w") as f:
    f.write(mock_newsletter)

print("✅ Mock Claude formatting complete. Output saved to output/formatted_newsletter.md")
print(f"📄 Generated newsletter ({len(mock_newsletter)} characters)")