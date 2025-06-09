#!/usr/bin/env python3
import json
import os


def main():
    # Load GitHub prospects
    with open("github_prospects_database.json") as f:
        github_prospects = json.load(f)

    # Load existing prospects if they exist
    main_prospects = []
    if os.path.exists("prospects_database.json"):
        with open("prospects_database.json") as f:
            main_prospects = json.load(f)

    # Convert GitHub prospects to main format
    converted_prospects = []
    for prospect in github_prospects:
        converted = {
            "id": prospect["id"],
            "name": prospect["name"],
            "company": prospect.get("company", ""),
            "title": "Developer/Founder",
            "industry": "Tech/SaaS",
            "company_size": "Unknown",
            "email": prospect.get("email", ""),
            "pain_points": [
                "market research",
                "product development",
                "customer acquisition",
            ],
            "niche_opportunities": [
                f"{prospect.get('repo_language', 'tech')} automation",
                "developer tools",
            ],
            "status": "new",
            "last_contact": None,
            "response_probability": 0.08,  # Higher for GitHub prospects
            "conversion_probability": 0.25,  # Higher quality prospects
            "created_at": prospect.get("discovered_at", ""),
            "source": "github_marketing",
            "github_data": {
                "username": prospect.get("username", ""),
                "github_url": prospect.get("github_url", ""),
                "followers": prospect.get("followers", 0),
                "repositories": prospect.get("repositories", 0),
                "prospect_score": prospect.get("prospect_score", 0),
            },
        }
        converted_prospects.append(converted)

    # Merge with existing prospects (avoid duplicates)
    existing_ids = {p["id"] for p in main_prospects}
    new_prospects = [p for p in converted_prospects if p["id"] not in existing_ids]

    # Add new prospects
    main_prospects.extend(new_prospects)

    # Save updated database
    with open("prospects_database.json", "w") as f:
        json.dump(main_prospects, f, indent=2)

    print(f"✅ Added {len(new_prospects)} new GitHub prospects to main pipeline")
    print(f"📊 Total prospects in pipeline: {len(main_prospects)}")


if __name__ == "__main__":
    main()
