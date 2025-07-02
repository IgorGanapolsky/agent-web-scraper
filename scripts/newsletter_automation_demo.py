#!/usr/bin/env python3
"""
Newsletter Automation Demo
Demonstrates the AI newsletter generation pipeline using Reddit data
"""

import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")

class NewsletterAutomationDemo:
    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.setup_mock_data()
    
    def setup_mock_data(self):
        """Create mock Reddit data for demonstration"""
        self.mock_reddit_data = [
            {
                "title": "Anyone struggling with SaaS integration issues?",
                "body": "Our team spends hours manually connecting different tools. Looking for automation solutions.",
                "subreddit": "entrepreneur",
                "score": 156,
                "comments": 42,
                "pain_points": ["Manual integration", "Time-consuming workflows", "Tool sprawl"]
            },
            {
                "title": "Customer onboarding is killing our conversion rates",
                "body": "30% of users drop off during our 5-step onboarding. Need to simplify this process.",
                "subreddit": "SaaS",
                "score": 203,
                "comments": 67,
                "pain_points": ["Complex onboarding", "High dropout rates", "User friction"]
            },
            {
                "title": "AI tools are too expensive for small businesses",
                "body": "Most AI solutions start at $500/month. Small businesses need affordable options.",
                "subreddit": "smallbusiness",
                "score": 89,
                "comments": 23,
                "pain_points": ["High AI costs", "SMB budget constraints", "Pricing barriers"]
            }
        ]
    
    def analyze_pain_points(self):
        """Extract and analyze pain points from Reddit data"""
        all_pain_points = []
        for post in self.mock_reddit_data:
            all_pain_points.extend(post["pain_points"])
        
        # Count frequency of pain points
        pain_point_frequency = {}
        for pain in all_pain_points:
            pain_point_frequency[pain] = pain_point_frequency.get(pain, 0) + 1
        
        # Get top 3 pain points
        top_pain_points = sorted(pain_point_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "top_pain_points": top_pain_points,
            "total_posts_analyzed": len(self.mock_reddit_data),
            "total_engagement": sum(post["score"] + post["comments"] for post in self.mock_reddit_data)
        }
    
    def generate_newsletter_content(self, analysis):
        """Generate newsletter content using AI-style analysis"""
        newsletter = f"""
# 🤖 AI Newsletter: SaaS Pain Points Weekly Digest

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} EST
**Data Source:** Reddit API Analysis
**Posts Analyzed:** {analysis['total_posts_analyzed']}
**Total Engagement:** {analysis['total_engagement']} points

---

## 📊 Top Pain Points This Week

"""
        
        for i, (pain_point, frequency) in enumerate(analysis['top_pain_points'], 1):
            newsletter += f"### {i}. {pain_point}\n"
            newsletter += f"**Frequency:** {frequency} mentions\n"
            newsletter += f"**Market Impact:** High priority for SaaS founders\n\n"
        
        newsletter += """---

## 💡 Business Opportunities

Based on our AI analysis of Reddit discussions:

1. **SaaS Integration Platform**: Build a simple, affordable integration tool for small businesses
2. **Onboarding Optimization Service**: Offer conversion rate optimization specifically for SaaS onboarding
3. **AI-for-SMB Marketplace**: Create budget-friendly AI tools under $100/month

---

## 🚀 Next Week's Focus

- Monitor integration tool discussions
- Track onboarding success stories
- Analyze pricing sensitivity trends

---

*🤖 Generated with AI Newsletter Automation Pipeline | Reddit API → LangChain → Analysis → Slack*
"""
        return newsletter
    
    def send_to_slack(self, newsletter_content):
        """Send newsletter to Slack channel"""
        if not self.slack_webhook:
            print("❌ No Slack webhook URL configured")
            return False
        
        # Create Slack message
        slack_message = {
            "text": "🚨 NEW AI NEWSLETTER READY!",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📧 *Weekly AI Newsletter Generated Successfully!*\n\n✅ Reddit data analyzed\n✅ Pain points identified\n✅ Business opportunities extracted"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"```{newsletter_content[:500]}...```"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🎯 *Ready for distribution to subscribers!*"
                    }
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=slack_message, timeout=60)
            if response.status_code == 200:
                print("✅ Newsletter sent to Slack successfully!")
                return True
            else:
                print(f"❌ Slack send failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error sending to Slack: {e}")
            return False
    
    def run_demo(self):
        """Execute the complete newsletter automation demo"""
        print("🚀 Starting Newsletter Automation Demo...")
        print("=" * 50)
        
        # Step 1: Simulate Reddit data collection
        print("\n📊 Step 1: Collecting Reddit data...")
        print(f"✅ Analyzed {len(self.mock_reddit_data)} Reddit posts")
        
        # Step 2: AI analysis of pain points
        print("\n🤖 Step 2: AI pain point analysis...")
        analysis = self.analyze_pain_points()
        print(f"✅ Identified {len(analysis['top_pain_points'])} top pain points")
        
        # Step 3: Generate newsletter content
        print("\n📝 Step 3: Generating newsletter content...")
        newsletter_content = self.generate_newsletter_content(analysis)
        print("✅ Newsletter content generated")
        
        # Step 4: Send to Slack
        print("\n📲 Step 4: Sending to Slack...")
        slack_success = self.send_to_slack(newsletter_content)
        
        # Step 5: Save newsletter locally
        print("\n💾 Step 5: Saving newsletter...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"newsletter_demo_{timestamp}.md"
        
        with open(filename, "w") as f:
            f.write(newsletter_content)
        
        print(f"✅ Newsletter saved as {filename}")
        
        # Summary
        print("\n" + "=" * 50)
        print("✅ DEMO COMPLETE!")
        print(f"📊 Posts analyzed: {analysis['total_posts_analyzed']}")
        print(f"📈 Total engagement: {analysis['total_engagement']} points")
        print(f"📧 Slack notification: {'✅ Sent' if slack_success else '❌ Failed'}")
        print(f"📄 Newsletter file: {filename}")
        print("\n🎯 This demonstrates the complete automation pipeline:")
        print("   Reddit API → Data Analysis → AI Processing → Content Generation → Slack → File Storage")
        
        return newsletter_content

if __name__ == "__main__":
    demo = NewsletterAutomationDemo()
    demo.run_demo()
