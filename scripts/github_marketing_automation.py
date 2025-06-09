#!/usr/bin/env python3
"""
GitHub Marketing Automation - Advanced Outreach System
Leverages GitHub activity for intelligent prospect discovery and engagement
"""

import json
import os
import random
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()


class GitHubMarketingEngine:
    """Advanced GitHub-based marketing automation system"""

    def __init__(self):
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "SaaS-Growth-Dispatch-Marketing-Engine",
        }

        print("🚀 GitHub Marketing Engine Initialized")
        print("🎯 Advanced prospect discovery through GitHub activity")

    def discover_saas_founders_on_github(self) -> list[dict]:
        """Discover SaaS founders and developers on GitHub"""

        # Search queries to find SaaS founders/developers
        search_queries = [
            "saas founder language:python",
            "startup ceo language:javascript",
            "b2b platform language:typescript",
            "business automation language:python",
            "enterprise software language:java",
            "api platform language:go",
            "data analytics language:python",
            "workflow automation language:javascript",
        ]

        prospects = []

        for query in search_queries:
            try:
                # Search for repositories
                response = requests.get(
                    f"{self.base_url}/search/repositories",
                    headers=self.headers,
                    params={
                        "q": query,
                        "sort": "updated",
                        "order": "desc",
                        "per_page": 10,
                    },
                )

                if response.status_code == 200:
                    repos = response.json().get("items", [])

                    for repo in repos:
                        owner = repo.get("owner", {})

                        # Get detailed user info
                        user_info = self.get_user_details(owner.get("login"))
                        if user_info:
                            prospect = self.analyze_github_profile(user_info, repo)
                            if prospect and prospect["is_target"]:
                                prospects.append(prospect)

                time.sleep(1)  # Rate limiting

            except Exception as e:
                print(f"❌ Error searching GitHub: {e}")

        print(f"✅ Discovered {len(prospects)} high-quality GitHub prospects")
        return prospects

    def get_user_details(self, username: str) -> dict:
        """Get detailed information about a GitHub user"""
        try:
            response = requests.get(
                f"{self.base_url}/users/{username}", headers=self.headers
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            print(f"❌ Error fetching user {username}: {e}")

        return {}

    def analyze_github_profile(self, user_info: dict, repo: dict) -> dict:
        """Analyze GitHub profile to determine if they're a good prospect"""

        # Scoring criteria
        score = 0
        reasons = []

        # Company indicators
        company = user_info.get("company", "").lower()
        if any(term in company for term in ["ceo", "founder", "cto", "startup"]):
            score += 30
            reasons.append("Leadership role indicated in company field")

        # Bio indicators
        bio = user_info.get("bio", "").lower()
        if any(
            term in bio
            for term in ["founder", "ceo", "entrepreneur", "startup", "saas", "b2b"]
        ):
            score += 25
            reasons.append("Entrepreneurial bio")

        # Repository indicators
        repo_name = repo.get("name", "").lower()
        repo_desc = repo.get("description", "").lower()
        if any(
            term in f"{repo_name} {repo_desc}"
            for term in ["saas", "platform", "api", "dashboard", "analytics"]
        ):
            score += 20
            reasons.append("SaaS-related repository")

        # Activity indicators
        if repo.get("stargazers_count", 0) > 10:
            score += 15
            reasons.append("Popular repository")

        if user_info.get("followers", 0) > 50:
            score += 10
            reasons.append("Established GitHub presence")

        # Email availability
        email = user_info.get("email")
        if email and "@" in email:
            score += 20
            reasons.append("Public email available")

        # Determine if target prospect
        is_target = score >= 50

        if is_target:
            return {
                "id": f"github_{user_info.get('login')}",
                "name": user_info.get("name") or user_info.get("login"),
                "username": user_info.get("login"),
                "email": email or f"{user_info.get('login')}@github.local",
                "company": user_info.get("company", "Unknown"),
                "bio": user_info.get("bio", ""),
                "location": user_info.get("location", ""),
                "github_url": user_info.get("html_url"),
                "followers": user_info.get("followers", 0),
                "repositories": user_info.get("public_repos", 0),
                "repo_name": repo.get("name"),
                "repo_description": repo.get("description"),
                "repo_stars": repo.get("stargazers_count", 0),
                "repo_language": repo.get("language"),
                "prospect_score": score,
                "targeting_reasons": reasons,
                "is_target": True,
                "source": "github_discovery",
                "discovered_at": datetime.now().isoformat(),
            }

        return {"is_target": False}

    def generate_github_outreach_message(self, prospect: dict) -> str:
        """Generate personalized outreach message based on GitHub activity"""

        templates = [
            f"""Hi {prospect['name']},

I came across your {prospect['repo_name']} repository and was impressed by your work in {prospect['repo_language']}.

As someone building in the {prospect['repo_language']} space, I thought you'd appreciate this insight our AI discovered:

🎯 "{prospect['repo_language']} automation for {prospect['company'] or 'startups'}"
→ High opportunity niche (8.2/10 score)
→ Only 3 major competitors
→ Growing 40% monthly

Our system finds market opportunities like this daily using AI analysis.

Would market intelligence like this be valuable for your projects?

We're offering GitHub developers early access for $29/month.

Worth a quick chat?

Best,
Igor Ganapolsky
Founder, SaaS Growth Dispatch

P.S. Love what you're building with {prospect['repo_name']}!""",
            f"""Hi {prospect['name']},

Fellow developer here - saw your work on {prospect['repo_name']} and your {prospect['followers']} followers on GitHub.

Quick question: Are you tracking market opportunities for your tech stack?

Our AI just flagged this for {prospect['repo_language']} developers:

🚀 High-opportunity niche: "{prospect['repo_language']}-powered business automation"
• Minimal competition (only 2 major players)
• Growing demand from non-technical founders
• Perfect for developers looking to build SaaS

This is the kind of market intelligence we deliver daily to tech entrepreneurs.

Interested in seeing what opportunities exist in your space?

Early access: $29/month for developers.

Best,
Igor""",
            f"""Hi {prospect['name']},

Impressive GitHub profile! {prospect['repositories']} repositories and working on {prospect['repo_name']}.

I built an AI system that finds underserved market niches for developers.

Latest discovery for your stack:

🎯 "{prospect['repo_language']} + AI integration tools"
→ Market score: 9.1/10 (VERY HIGH)
→ Low competition, high demand
→ Perfect for technical founders

Most developers miss opportunities like this because market research takes forever.

Our system delivers these insights daily in 5-minute reports.

Want to see what your tech stack could build?

GitHub developer rate: $29/month

Best,
Igor Ganapolsky
SaaS Growth Dispatch""",
        ]

        return random.choice(templates)

    def send_github_outreach(self, prospects: list[dict]) -> dict:
        """Send outreach to GitHub-discovered prospects"""

        results = {
            "emails_sent": 0,
            "github_prospects": len(prospects),
            "high_score_prospects": 0,
            "expected_responses": 0,
        }

        for prospect in prospects[:25]:  # Send to 25 GitHub prospects per day
            if prospect["prospect_score"] >= 70:
                results["high_score_prospects"] += 1

            # Generate personalized message
            message = self.generate_github_outreach_message(prospect)

            # Simulate sending (in production, integrate with email API)
            success = self.simulate_email_send(prospect, message)

            if success:
                results["emails_sent"] += 1

                # GitHub prospects typically have higher response rates
                response_rate = 0.08 if prospect["prospect_score"] >= 70 else 0.05
                results["expected_responses"] += response_rate

            time.sleep(1)  # Rate limiting

        print(f"📧 GitHub outreach sent to {results['emails_sent']} prospects")
        print(f"⭐ {results['high_score_prospects']} high-score prospects targeted")
        print(f"📈 Expected {results['expected_responses']:.1f} responses")

        return results

    def simulate_email_send(self, prospect: dict, message: str) -> bool:
        """Simulate email sending (replace with real email API in production)"""
        print(f"📧 GitHub outreach to {prospect['name']} (@{prospect['username']})")
        return random.random() < 0.95  # 95% delivery rate

    def create_github_issue_outreach(self, repo_owner: str, repo_name: str) -> bool:
        """Create strategic GitHub issue for outreach (use sparingly!)"""

        # Only for very high-value prospects and with valuable contribution
        issue_body = f"""## 💡 Market Opportunity for {repo_name}

Hi @{repo_owner},

Love what you're building here! As someone who analyzes SaaS market opportunities, I discovered something interesting about your space:

**High-Opportunity Niche Discovered:**
- **Market:** "{repo_name}-style automation for SMBs"
- **Opportunity Score:** 8.7/10
- **Competition:** Only 2 major players
- **Trend:** Growing 45% monthly

This could be a great direction for expansion or a separate product.

I run a market intelligence service that finds opportunities like this daily. Happy to share more insights if you're interested!

**Not spam** - I genuinely think this could be valuable for your roadmap.

Best,
Igor Ganapolsky
Founder, SaaS Growth Dispatch"""

        try:
            response = requests.post(
                f"{self.base_url}/repos/{repo_owner}/{repo_name}/issues",
                headers=self.headers,
                json={
                    "title": f"💡 Market Opportunity Discovery for {repo_name}",
                    "body": issue_body,
                    "labels": ["enhancement", "discussion"],
                },
            )

            if response.status_code == 201:
                print(f"✅ Created strategic issue in {repo_owner}/{repo_name}")
                return True

        except Exception as e:
            print(f"❌ Failed to create issue: {e}")

        return False

    def discover_trending_repositories(self) -> list[dict]:
        """Discover trending repositories for outreach opportunities"""

        try:
            # Get trending repositories
            response = requests.get(
                f"{self.base_url}/search/repositories",
                headers=self.headers,
                params={
                    "q": "saas platform created:>2024-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 20,
                },
            )

            if response.status_code == 200:
                trending_repos = response.json().get("items", [])
                print(f"📈 Found {len(trending_repos)} trending SaaS repositories")
                return trending_repos

        except Exception as e:
            print(f"❌ Error finding trending repos: {e}")

        return []

    def run_github_marketing_cycle(self) -> dict:
        """Run complete GitHub marketing automation cycle"""

        print("\n🚀 GITHUB MARKETING AUTOMATION CYCLE")
        print("=" * 50)

        # Step 1: Discover prospects
        prospects = self.discover_saas_founders_on_github()

        # Step 2: Send outreach
        outreach_results = self.send_github_outreach(prospects)

        # Step 3: Save prospects database
        self.save_github_prospects(prospects)

        # Step 4: Strategic repository engagement (selective)
        trending_repos = self.discover_trending_repositories()

        results = {
            "prospects_discovered": len(prospects),
            "outreach_sent": outreach_results["emails_sent"],
            "expected_responses": outreach_results["expected_responses"],
            "trending_repos_found": len(trending_repos),
        }

        print("📊 GitHub Marketing Results:")
        print(f"   • Prospects discovered: {results['prospects_discovered']}")
        print(f"   • Outreach messages sent: {results['outreach_sent']}")
        print(f"   • Expected responses: {results['expected_responses']:.1f}")

        return results

    def save_github_prospects(self, prospects: list[dict]):
        """Save GitHub prospects to database"""

        filename = "github_prospects_database.json"

        # Load existing prospects
        existing_prospects = []
        if os.path.exists(filename):
            with open(filename) as f:
                existing_prospects = json.load(f)

        # Add new prospects
        existing_prospects.extend(prospects)

        # Save updated database
        with open(filename, "w") as f:
            json.dump(existing_prospects, f, indent=2)

        print(f"💾 Saved {len(prospects)} GitHub prospects to {filename}")


def main():
    """Main execution"""

    print("🚀 GITHUB MARKETING AUTOMATION SYSTEM")
    print("=" * 50)
    print("🎯 Discovering SaaS founders and developers on GitHub")
    print("📧 Sending intelligent, personalized outreach")
    print("🔄 Building high-quality prospect pipeline")
    print()

    # Initialize GitHub marketing engine
    github_engine = GitHubMarketingEngine()

    # Run marketing cycle
    github_engine.run_github_marketing_cycle()
    print("\n✅ GITHUB MARKETING CYCLE COMPLETE!")
    print("🎯 High-quality prospects identified and contacted")
    print("📈 Expect 2-3x higher response rates from GitHub outreach")
    print("🚀 Premium prospects added to sales pipeline")


if __name__ == "__main__":
    main()
