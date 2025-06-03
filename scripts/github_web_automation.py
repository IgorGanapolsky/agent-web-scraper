#!/usr/bin/env python3
"""
Web-based GitHub automation using Playwright
"""

import asyncio

from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()


async def create_issues_via_web():
    """Create GitHub issues using web interface automation"""

    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to True for headless
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Navigate to GitHub Issues page
            await page.goto(
                "https://github.com/IgorGanapolsky/agent-web-scraper/issues"
            )
            await page.wait_for_load_state()
            print("📍 Navigated to issues page")

            # Check if logged in by looking for profile or sign-in elements
            profile_element = await page.query_selector(
                '[data-testid="header-user-avatar"]'
            )
            sign_in_element = await page.query_selector('[href="/login"]')

            if sign_in_element and not profile_element:
                print("❌ Not logged into GitHub - please log in manually first")
                print("   Open https://github.com/login in your browser and log in")
                await browser.close()
                return False

            print("✅ Appears to be logged in")

            # Look for "New issue" button with multiple selectors
            await page.wait_for_timeout(2000)  # Wait for page to fully load

            new_issue_selectors = [
                'a[href*="/issues/new"]',
                'text="New issue"',
                '[data-testid="new-issue-button"]',
                '.btn:has-text("New issue")',
            ]

            new_issue_btn = None
            for selector in new_issue_selectors:
                new_issue_btn = await page.query_selector(selector)
                if new_issue_btn:
                    print(f"✅ Found New issue button with selector: {selector}")
                    break

            if new_issue_btn:
                await new_issue_btn.click()
                await page.wait_for_load_state()
                print("✅ Clicked New issue button")

                # Wait for the form to load and fill out first issue
                await page.wait_for_selector('[name="issue[title]"]', timeout=10000)
                await page.fill(
                    '[name="issue[title]"]', "Add Stripe integration for monetization"
                )
                print("✅ Filled title")

                issue_body = """Implement Stripe payment workflow for paid research packs to enable revenue generation from the platform.

**Acceptance Criteria:**
- Integrate Stripe checkout flow
- Create pricing tiers for research packs
- Implement payment success/failure handling
- Add subscription management
- Set up webhook handling for payment events

**Business Impact:** Direct revenue generation capability"""

                await page.wait_for_selector('[name="issue[body]"]', timeout=5000)
                await page.fill('[name="issue[body]"]', issue_body)
                print("✅ Filled body")

                # Submit issue
                submit_selectors = [
                    'button:has-text("Submit new issue")',
                    'input[value="Submit new issue"]',
                    '[data-testid="submit-new-issue"]',
                ]

                submit_btn = None
                for selector in submit_selectors:
                    submit_btn = await page.query_selector(selector)
                    if submit_btn:
                        print(f"✅ Found submit button with selector: {selector}")
                        break

                if submit_btn:
                    await submit_btn.click()
                    await page.wait_for_load_state()
                    print("✅ Successfully created first issue via web interface!")

                    # Wait to see the created issue
                    await page.wait_for_timeout(3000)
                    return True
                else:
                    print("❌ Could not find submit button")
                    print("   Available buttons on page:")
                    buttons = await page.query_selector_all("button")
                    for i, btn in enumerate(buttons[:5]):  # Show first 5 buttons
                        text = await btn.inner_text()
                        print(f"     Button {i+1}: '{text}'")
                    return False
            else:
                print("❌ Could not find 'New issue' button")
                return False

        except Exception as e:
            print(f"❌ Error during web automation: {e}")
            return False
        finally:
            await browser.close()


if __name__ == "__main__":
    print("🚀 Starting web-based GitHub automation...")
    result = asyncio.run(create_issues_via_web())
    print(f"Result: {result}")
