#!/usr/bin/env python3
"""
REAL Stripe Integration - Live Revenue Tracking
Connect to actual Stripe dashboard for Week 2 $600/day target
"""

from pathlib import Path


def setup_stripe_api_connection():
    """Set up real Stripe API connection"""

    print("🔥 REAL STRIPE INTEGRATION SETUP")
    print("=" * 50)
    print("⚠️  IMPORTANT: This will connect to your LIVE Stripe account")
    print()

    # Check for existing Stripe configuration
    env_file = Path(".env")
    stripe_config = {}

    if env_file.exists():
        print("📁 Found existing .env file")
        with open(env_file) as f:
            for line in f:
                if line.startswith("STRIPE_"):
                    key, value = line.strip().split("=", 1)
                    stripe_config[key] = value.strip('"')

    # Required Stripe credentials
    required_keys = [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
    ]

    print("\n🔑 STRIPE API CREDENTIALS NEEDED:")
    print("=" * 40)

    for key in required_keys:
        if key in stripe_config:
            masked_value = (
                stripe_config[key][:12] + "..."
                if len(stripe_config[key]) > 12
                else stripe_config[key]
            )
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"❌ {key}: NOT FOUND")
            print("   → Get from: https://dashboard.stripe.com/apikeys")

    print("\n📋 TO SET UP REAL STRIPE CONNECTION:")
    print("1. Go to: https://dashboard.stripe.com/apikeys")
    print("2. Copy your SECRET KEY (starts with sk_live_ or sk_test_)")
    print("3. Copy your PUBLISHABLE KEY (starts with pk_live_ or pk_test_)")
    print("4. Go to: https://dashboard.stripe.com/webhooks")
    print("5. Create webhook endpoint: https://yourdomain.com/webhook/stripe")
    print("6. Copy the webhook secret (starts with whsec_)")
    print("7. Add to .env file:")
    print("   STRIPE_SECRET_KEY=sk_live_...")
    print("   STRIPE_PUBLISHABLE_KEY=pk_live_...")
    print("   STRIPE_WEBHOOK_SECRET=whsec_...")

    return stripe_config


def create_real_stripe_client():
    """Create real Stripe client for live data"""

    print("\n💳 CREATING REAL STRIPE CLIENT...")

    # This would normally use: import stripe
    # But we'll show the setup code for when you have credentials

    stripe_setup_code = '''
import stripe
import os
from datetime import datetime, timedelta

# Set up Stripe with your real API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class RealStripeRevenueTracker:
    """Real Stripe revenue tracking for $600/day target"""

    def __init__(self):
        self.target_daily_revenue = 600
        self.week2_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    def get_real_revenue_data(self):
        """Get actual revenue from Stripe dashboard"""

        try:
            # Get payments from the last 7 days (Week 2)
            week_ago = int((self.week2_start - timedelta(days=7)).timestamp())

            # Fetch real payment intents
            payment_intents = stripe.PaymentIntent.list(
                created={"gte": week_ago},
                limit=100
            )

            # Fetch real charges
            charges = stripe.Charge.list(
                created={"gte": week_ago},
                limit=100
            )

            # Fetch real subscriptions
            subscriptions = stripe.Subscription.list(
                created={"gte": week_ago},
                limit=100
            )

            return {
                "payment_intents": payment_intents,
                "charges": charges,
                "subscriptions": subscriptions,
                "total_revenue": sum(charge.amount/100 for charge in charges if charge.paid),
                "total_customers": len(set(charge.customer for charge in charges if charge.customer))
            }

        except stripe.error.AuthenticationError:
            return {"error": "Invalid Stripe API key"}
        except stripe.error.APIConnectionError:
            return {"error": "Network connection to Stripe failed"}
        except Exception as e:
            return {"error": f"Stripe API error: {str(e)}"}

    def get_trial_conversions(self):
        """Get real trial-to-paid conversion data"""

        try:
            # Get subscription events
            events = stripe.Event.list(
                type="customer.subscription.created",
                created={"gte": int((datetime.now() - timedelta(days=7)).timestamp())},
                limit=50
            )

            trial_conversions = []
            for event in events:
                subscription = event.data.object
                if subscription.trial_end and subscription.trial_end < datetime.now().timestamp():
                    trial_conversions.append({
                        "customer_id": subscription.customer,
                        "amount": subscription.items.data[0].price.unit_amount / 100,
                        "trial_started": subscription.trial_start,
                        "converted_at": subscription.current_period_start
                    })

            return {
                "trial_conversions": trial_conversions,
                "conversion_count": len(trial_conversions),
                "conversion_revenue": sum(tc["amount"] for tc in trial_conversions)
            }

        except Exception as e:
            return {"error": f"Trial conversion fetch error: {str(e)}"}

    def calculate_daily_metrics(self, revenue_data):
        """Calculate daily revenue metrics for Week 2 target"""

        if "error" in revenue_data:
            return revenue_data

        total_revenue = revenue_data["total_revenue"]
        days_elapsed = (datetime.now() - self.week2_start).days + 1

        return {
            "total_week2_revenue": total_revenue,
            "days_elapsed": days_elapsed,
            "average_daily_revenue": total_revenue / days_elapsed if days_elapsed > 0 else 0,
            "target_daily_revenue": self.target_daily_revenue,
            "target_gap": self.target_daily_revenue - (total_revenue / days_elapsed if days_elapsed > 0 else 0),
            "on_track_for_target": (total_revenue / days_elapsed if days_elapsed > 0 else 0) >= self.target_daily_revenue * 0.8,
            "projected_week_revenue": (total_revenue / days_elapsed if days_elapsed > 0 else 0) * 7
        }

# Usage:
tracker = RealStripeRevenueTracker()
revenue_data = tracker.get_real_revenue_data()
trial_data = tracker.get_trial_conversions()
metrics = tracker.calculate_daily_metrics(revenue_data)

print("💰 REAL STRIPE REVENUE DATA:")
print(f"Total Revenue: ${revenue_data.get('total_revenue', 0)}")
print(f"Total Customers: {revenue_data.get('total_customers', 0)}")
print(f"Daily Average: ${metrics.get('average_daily_revenue', 0):.2f}")
print(f"Target Gap: ${metrics.get('target_gap', 0):.2f}")
print(f"On Track: {metrics.get('on_track_for_target', False)}")
'''

    return stripe_setup_code


def create_stripe_environment_file():
    """Create .env file template for Stripe credentials"""

    env_template = """# STRIPE API CONFIGURATION - REAL CREDENTIALS
# Get these from: https://dashboard.stripe.com/apikeys

# Secret Key (starts with sk_live_ for production or sk_test_ for testing)
STRIPE_SECRET_KEY=sk_live_your_actual_secret_key_here

# Publishable Key (starts with pk_live_ for production or pk_test_ for testing)
STRIPE_PUBLISHABLE_KEY=pk_live_your_actual_publishable_key_here

# Webhook Secret (starts with whsec_)
# Get from: https://dashboard.stripe.com/webhooks
STRIPE_WEBHOOK_SECRET=whsec_your_actual_webhook_secret_here

# LIVE MODE CONFIRMATION
STRIPE_LIVE_MODE=true

# YOUR BUSINESS DETAILS
BUSINESS_NAME=Your SaaS Company
SUPPORT_EMAIL=support@yourdomain.com
"""

    env_file = Path(".env")

    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_template)
        print("✅ Created .env template file")
        print("📝 Please edit .env with your real Stripe credentials")
    else:
        print("⚠️  .env file already exists")
        print("📝 Please verify your Stripe credentials in .env")

    return env_file


def create_real_revenue_dashboard():
    """Create real-time revenue dashboard connector"""

    dashboard_code = '''
import stripe
import json
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Real Stripe Revenue Dashboard")

@app.get("/revenue/live")
async def get_live_revenue():
    """Get real-time revenue from Stripe"""

    try:
        # Last 24 hours
        yesterday = int((datetime.now() - timedelta(days=1)).timestamp())

        charges = stripe.Charge.list(
            created={"gte": yesterday},
            limit=100
        )

        daily_revenue = sum(charge.amount/100 for charge in charges if charge.paid)

        return {
            "status": "live",
            "daily_revenue": daily_revenue,
            "target": 600,
            "gap": 600 - daily_revenue,
            "timestamp": datetime.now().isoformat(),
            "charges_count": len([c for c in charges if c.paid])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")

@app.get("/revenue/dashboard", response_class=HTMLResponse)
async def revenue_dashboard():
    """Real-time revenue dashboard"""

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Real Stripe Revenue - $600/day Target</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .metric { display: inline-block; margin: 20px; padding: 20px; border: 1px solid #ccc; border-radius: 8px; }
            .target { background-color: #e8f5e8; }
            .current { background-color: #fff3cd; }
            .gap { background-color: #f8d7da; }
        </style>
    </head>
    <body>
        <h1>🔥 REAL Stripe Revenue Dashboard</h1>
        <div id="metrics"></div>
        <canvas id="revenueChart" width="400" height="200"></canvas>

        <script>
            async function updateMetrics() {
                try {
                    const response = await fetch('/revenue/live');
                    const data = await response.json();

                    document.getElementById('metrics').innerHTML = `
                        <div class="metric current">
                            <h3>Current Daily Revenue</h3>
                            <h2>$${data.daily_revenue.toFixed(2)}</h2>
                        </div>
                        <div class="metric target">
                            <h3>Daily Target</h3>
                            <h2>$${data.target}</h2>
                        </div>
                        <div class="metric gap">
                            <h3>Gap to Target</h3>
                            <h2>$${data.gap.toFixed(2)}</h2>
                        </div>
                    `;

                } catch (error) {
                    console.error('Error fetching revenue data:', error);
                }
            }

            // Update every 30 seconds
            updateMetrics();
            setInterval(updateMetrics, 30000);
        </script>
    </body>
    </html>
    """

    return html

# To run: uvicorn real_stripe_dashboard:app --reload --port 8000
# Then visit: http://localhost:8000/revenue/dashboard
'''

    with open("real_stripe_dashboard.py", "w") as f:
        f.write(dashboard_code)

    print("✅ Created real_stripe_dashboard.py")
    print("🚀 Run with: uvicorn real_stripe_dashboard:app --reload --port 8000")


def main():
    """Main execution - Set up real Stripe integration"""

    print("🔥 REAL STRIPE INTEGRATION - NO MORE TEST DATA!")
    print("💰 Target: $600/day Week 2 Revenue")
    print("=" * 60)

    # Step 1: Check existing credentials
    setup_stripe_api_connection()

    # Step 2: Create environment file
    create_stripe_environment_file()

    # Step 3: Generate real Stripe client code
    stripe_code = create_real_stripe_client()

    # Step 4: Create real revenue dashboard
    create_real_revenue_dashboard()

    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS TO CONNECT TO REAL STRIPE:")
    print("=" * 60)
    print("1. Edit .env file with your real Stripe API keys")
    print("2. Install Stripe: pip install stripe")
    print('3. Run: python -c "from real_stripe_integration import *; main()"')
    print("4. Launch dashboard: uvicorn real_stripe_dashboard:app --reload")
    print("5. Visit: http://localhost:8000/revenue/dashboard")
    print("\n🔥 REAL MONEY TRACKING READY!")

    # Save the Stripe client code
    with open("real_stripe_client.py", "w") as f:
        f.write(stripe_code)

    print("✅ Saved real_stripe_client.py - Your live revenue tracker")


if __name__ == "__main__":
    main()
