from datetime import datetime, timedelta

import stripe
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="Real Stripe Revenue Dashboard")


@app.get("/revenue/live")
async def get_live_revenue():
    """Get real-time revenue from Stripe"""

    try:
        # Last 24 hours
        yesterday = int((datetime.now() - timedelta(days=1)).timestamp())

        charges = stripe.Charge.list(created={"gte": yesterday}, limit=100)

        daily_revenue = sum(charge.amount / 100 for charge in charges if charge.paid)

        return {
            "status": "live",
            "daily_revenue": daily_revenue,
            "target": 600,
            "gap": 600 - daily_revenue,
            "timestamp": datetime.now().isoformat(),
            "charges_count": len([c for c in charges if c.paid]),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {e!s}")


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
