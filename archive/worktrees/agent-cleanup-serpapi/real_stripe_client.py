import os
from datetime import datetime, timedelta

import stripe

# Set up Stripe with your real API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


class RealStripeRevenueTracker:
    """Real Stripe revenue tracking for $600/day target"""

    def __init__(self):
        self.target_daily_revenue = 600
        self.week2_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def get_real_revenue_data(self):
        """Get actual revenue from Stripe dashboard"""

        try:
            # Get payments from the last 7 days (Week 2)
            week_ago = int((self.week2_start - timedelta(days=7)).timestamp())

            # Fetch real payment intents
            payment_intents = stripe.PaymentIntent.list(
                created={"gte": week_ago}, limit=100
            )

            # Fetch real charges
            charges = stripe.Charge.list(created={"gte": week_ago}, limit=100)

            # Fetch real subscriptions
            subscriptions = stripe.Subscription.list(
                created={"gte": week_ago}, limit=100
            )

            return {
                "payment_intents": payment_intents,
                "charges": charges,
                "subscriptions": subscriptions,
                "total_revenue": sum(
                    charge.amount / 100 for charge in charges if charge.paid
                ),
                "total_customers": len(
                    {charge.customer for charge in charges if charge.customer}
                ),
            }

        except stripe.error.AuthenticationError:
            return {"error": "Invalid Stripe API key"}
        except stripe.error.APIConnectionError:
            return {"error": "Network connection to Stripe failed"}
        except Exception as e:
            return {"error": f"Stripe API error: {e!s}"}

    def get_trial_conversions(self):
        """Get real trial-to-paid conversion data"""

        try:
            # Get subscription events
            events = stripe.Event.list(
                type="customer.subscription.created",
                created={"gte": int((datetime.now() - timedelta(days=7)).timestamp())},
                limit=50,
            )

            trial_conversions = []
            for event in events:
                subscription = event.data.object
                if (
                    subscription.trial_end
                    and subscription.trial_end < datetime.now().timestamp()
                ):
                    trial_conversions.append(
                        {
                            "customer_id": subscription.customer,
                            "amount": subscription.items.data[0].price.unit_amount
                            / 100,
                            "trial_started": subscription.trial_start,
                            "converted_at": subscription.current_period_start,
                        }
                    )

            return {
                "trial_conversions": trial_conversions,
                "conversion_count": len(trial_conversions),
                "conversion_revenue": sum(tc["amount"] for tc in trial_conversions),
            }

        except Exception as e:
            return {"error": f"Trial conversion fetch error: {e!s}"}

    def calculate_daily_metrics(self, revenue_data):
        """Calculate daily revenue metrics for Week 2 target"""

        if "error" in revenue_data:
            return revenue_data

        total_revenue = revenue_data["total_revenue"]
        days_elapsed = (datetime.now() - self.week2_start).days + 1

        return {
            "total_week2_revenue": total_revenue,
            "days_elapsed": days_elapsed,
            "average_daily_revenue": (
                total_revenue / days_elapsed if days_elapsed > 0 else 0
            ),
            "target_daily_revenue": self.target_daily_revenue,
            "target_gap": self.target_daily_revenue
            - (total_revenue / days_elapsed if days_elapsed > 0 else 0),
            "on_track_for_target": (
                total_revenue / days_elapsed if days_elapsed > 0 else 0
            )
            >= self.target_daily_revenue * 0.8,
            "projected_week_revenue": (
                total_revenue / days_elapsed if days_elapsed > 0 else 0
            )
            * 7,
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
