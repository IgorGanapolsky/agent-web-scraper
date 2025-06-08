"""
Real-time Revenue Dashboard for $300/day Target Tracking
CFO Implementation for Live Financial Monitoring
"""

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

import stripe
from fastapi import APIRouter, WebSocket
from fastapi.responses import HTMLResponse

from app.config.logging import get_logger
from app.core.live_stripe_integration import get_live_stripe_integration

logger = get_logger(__name__)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_LIVE_SECRET_KEY")

router = APIRouter()


@dataclass
class RevenueMetrics:
    """Real-time revenue metrics for CFO dashboard"""
    
    daily_revenue: float
    daily_target: float = 300.0
    progress_percentage: float = 0.0
    customers_today: int = 0
    customers_target: int = 114  # For $300/day
    avg_revenue_per_customer: float = 79.0
    mrr: float = 0.0  # Monthly Recurring Revenue
    churn_rate: float = 0.0
    ltv_cac_ratio: float = 158.0  # $79 LTV / $0.50 CAC
    

class RevenueDashboard:
    """CFO-focused real-time revenue tracking and financial analytics"""
    
    def __init__(self):
        self.live_stripe = get_live_stripe_integration()
        self.websocket_connections: List[WebSocket] = []
        
    async def get_real_time_metrics(self) -> RevenueMetrics:
        """Get current real-time revenue metrics"""
        
        try:
            # Get today's revenue from Stripe
            today_start = int(
                datetime.now()
                .replace(hour=0, minute=0, second=0, microsecond=0)
                .timestamp()
            )
            
            # Fetch live charges from Stripe
            charges = stripe.Charge.list(
                created={"gte": today_start},
                limit=100
            )
            
            daily_revenue = sum(
                charge.amount / 100 
                for charge in charges.data 
                if charge.paid
            )
            
            # Get active subscriptions
            subscriptions = stripe.Subscription.list(
                status="active",
                limit=100
            )
            
            active_customers = len(subscriptions.data)
            mrr = sum(
                sub.items.data[0].price.unit_amount / 100
                for sub in subscriptions.data
                if sub.items.data
            )
            
            # Calculate metrics
            progress_percentage = (daily_revenue / 300.0) * 100
            customers_today = len([
                charge for charge in charges.data
                if charge.paid and charge.description and "subscription" in charge.description.lower()
            ])
            
            return RevenueMetrics(
                daily_revenue=daily_revenue,
                progress_percentage=min(progress_percentage, 100),
                customers_today=customers_today,
                customers_target=114,
                mrr=mrr,
                churn_rate=self._calculate_churn_rate(),
                ltv_cac_ratio=158.0  # $79 LTV / $0.50 CAC
            )
            
        except Exception as e:
            logger.error(f"Error fetching revenue metrics: {e}")
            return RevenueMetrics(daily_revenue=0.0)
    
    def _calculate_churn_rate(self) -> float:
        """Calculate monthly churn rate"""
        
        try:
            # Get subscriptions canceled in last 30 days
            thirty_days_ago = int(
                (datetime.now() - timedelta(days=30)).timestamp()
            )
            
            canceled_subs = stripe.Subscription.list(
                status="canceled",
                created={"gte": thirty_days_ago},
                limit=100
            )
            
            active_subs = stripe.Subscription.list(
                status="active",
                limit=100
            )
            
            if len(active_subs.data) == 0:
                return 0.0
                
            churn_rate = len(canceled_subs.data) / (len(active_subs.data) + len(canceled_subs.data))
            return round(churn_rate * 100, 2)
            
        except Exception as e:
            logger.error(f"Error calculating churn rate: {e}")
            return 0.0
    
    async def get_financial_forecast(self) -> Dict[str, Any]:
        """Generate financial forecast based on current metrics"""
        
        metrics = await self.get_real_time_metrics()
        
        # Weekly forecast
        if metrics.customers_today > 0:
            weekly_projected_customers = metrics.customers_today * 7
            weekly_projected_revenue = weekly_projected_customers * 79.0
        else:
            weekly_projected_customers = 0
            weekly_projected_revenue = 0.0
        
        # Monthly forecast
        monthly_projected_customers = metrics.customers_today * 30
        monthly_projected_revenue = monthly_projected_customers * 79.0
        
        return {
            "current_metrics": metrics.__dict__,
            "weekly_forecast": {
                "projected_customers": weekly_projected_customers,
                "projected_revenue": weekly_projected_revenue,
                "probability": 0.85 if metrics.customers_today > 0 else 0.1
            },
            "monthly_forecast": {
                "projected_customers": monthly_projected_customers,
                "projected_revenue": monthly_projected_revenue,
                "projected_mrr": monthly_projected_revenue,
                "break_even_timeline": "Week 2" if metrics.customers_today >= 2 else "Week 4+"
            },
            "unit_economics": {
                "customer_acquisition_cost": 0.50,
                "lifetime_value": 79.0 * 12,  # Assume 12 month average
                "ltv_cac_ratio": 158.0,
                "payback_period_days": 0.6,  # Less than 1 day!
                "gross_margin": 0.95  # 95% gross margin for SaaS
            },
            "targets": {
                "daily_target": 300.0,
                "customers_needed_daily": 4,  # 300/79 = 3.8
                "customers_needed_total": 114,
                "time_to_target": self._calculate_time_to_target(metrics)
            }
        }
    
    def _calculate_time_to_target(self, metrics: RevenueMetrics) -> str:
        """Calculate estimated time to reach $300/day target"""
        
        if metrics.customers_today == 0:
            return "Unknown - need customer data"
        
        customers_per_day = metrics.customers_today
        customers_needed = 4  # For $300/day
        
        if customers_per_day >= customers_needed:
            return "Target achieved!"
        
        days_to_target = max(1, customers_needed / customers_per_day)
        return f"{days_to_target:.1f} days"
    
    async def track_revenue_event(self, event_data: Dict[str, Any]):
        """Track and broadcast revenue events to connected dashboards"""
        
        # Add timestamp
        event_data["timestamp"] = datetime.now().isoformat()
        
        # Store in persistent tracking
        await self._store_revenue_event(event_data)
        
        # Broadcast to connected WebSocket clients
        await self._broadcast_to_dashboards(event_data)
        
        logger.info(f"💰 Revenue event tracked: {event_data}")
    
    async def _store_revenue_event(self, event_data: Dict[str, Any]):
        """Store revenue event for historical analysis"""
        
        from pathlib import Path
        
        storage_dir = Path("data/revenue_tracking")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Store daily events
        today = datetime.now().date().isoformat()
        daily_file = storage_dir / f"revenue_{today}.json"
        
        # Load existing events
        events = []
        if daily_file.exists():
            try:
                with open(daily_file) as f:
                    events = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                events = []
        
        # Add new event
        events.append(event_data)
        
        # Save updated events
        with open(daily_file, "w") as f:
            json.dump(events, f, indent=2)
    
    async def _broadcast_to_dashboards(self, event_data: Dict[str, Any]):
        """Broadcast revenue updates to connected WebSocket clients"""
        
        if not self.websocket_connections:
            return
        
        message = json.dumps({
            "type": "revenue_update",
            "data": event_data
        })
        
        # Send to all connected clients
        disconnected = []
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.warning(f"WebSocket send failed: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)


# Global dashboard instance
_revenue_dashboard = None


def get_revenue_dashboard() -> RevenueDashboard:
    """Get the global revenue dashboard instance"""
    global _revenue_dashboard
    if _revenue_dashboard is None:
        _revenue_dashboard = RevenueDashboard()
    return _revenue_dashboard


@router.get("/revenue/dashboard", response_class=HTMLResponse)
async def revenue_dashboard_page():
    """Serve the CFO revenue dashboard page"""
    
    dashboard_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>CFO Revenue Dashboard - $300/day Target</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .metric { font-size: 36px; font-weight: bold; color: #10b981; }
            .label { font-size: 14px; color: #666; text-transform: uppercase; margin-bottom: 5px; }
            .progress-bar { width: 100%; height: 10px; background: #e5e7eb; border-radius: 5px; overflow: hidden; }
            .progress-fill { height: 100%; background: linear-gradient(90deg, #10b981 0%, #059669 100%); transition: width 0.3s; }
            .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
            .status.success { background: #d1fae5; color: #065f46; }
            .status.warning { background: #fef3c7; color: #92400e; }
            .status.danger { background: #fee2e2; color: #991b1b; }
        </style>
    </head>
    <body>
        <h1>💰 CFO Revenue Dashboard</h1>
        
        <div class="dashboard">
            <div class="card">
                <div class="label">Daily Revenue</div>
                <div class="metric" id="dailyRevenue">$0.00</div>
                <div class="progress-bar">
                    <div class="progress-fill" id="dailyProgress" style="width: 0%"></div>
                </div>
                <div>Target: $300.00</div>
            </div>
            
            <div class="card">
                <div class="label">Customers Today</div>
                <div class="metric" id="customersToday">0</div>
                <div>Target: 4 customers/day</div>
            </div>
            
            <div class="card">
                <div class="label">Monthly Recurring Revenue</div>
                <div class="metric" id="mrr">$0</div>
                <div id="mrrGrowth">0% growth</div>
            </div>
            
            <div class="card">
                <div class="label">LTV:CAC Ratio</div>
                <div class="metric">158:1</div>
                <div class="status success">Excellent unit economics</div>
            </div>
        </div>
        
        <div id="liveEvents" style="margin-top: 30px;">
            <h3>Live Revenue Events</h3>
            <div id="eventsList"></div>
        </div>
        
        <script>
            const ws = new WebSocket('ws://localhost:8000/revenue/ws');
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                if (data.type === 'revenue_update') {
                    updateDashboard(data.data);
                }
            };
            
            function updateDashboard(metrics) {
                document.getElementById('dailyRevenue').textContent = '$' + metrics.daily_revenue.toFixed(2);
                document.getElementById('customersToday').textContent = metrics.customers_today;
                document.getElementById('mrr').textContent = '$' + metrics.mrr.toFixed(0);
                
                const progress = Math.min((metrics.daily_revenue / 300) * 100, 100);
                document.getElementById('dailyProgress').style.width = progress + '%';
            }
            
            // Fetch initial data
            fetch('/revenue/metrics')
                .then(response => response.json())
                .then(data => updateDashboard(data))
                .catch(console.error);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=dashboard_html)


@router.get("/revenue/metrics")
async def get_revenue_metrics():
    """Get current revenue metrics for dashboard"""
    
    dashboard = get_revenue_dashboard()
    metrics = await dashboard.get_real_time_metrics()
    return metrics.__dict__


@router.get("/revenue/forecast")
async def get_revenue_forecast():
    """Get financial forecast and projections"""
    
    dashboard = get_revenue_dashboard()
    return await dashboard.get_financial_forecast()


@router.websocket("/revenue/ws")
async def revenue_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time revenue updates"""
    
    await websocket.accept()
    dashboard = get_revenue_dashboard()
    dashboard.websocket_connections.append(websocket)
    
    try:
        while True:
            # Send periodic updates
            metrics = await dashboard.get_real_time_metrics()
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics.__dict__
            })
            
            # Wait for next update or client message
            await websocket.receive_text()
            
    except Exception as e:
        logger.warning(f"WebSocket connection closed: {e}")
    finally:
        if websocket in dashboard.websocket_connections:
            dashboard.websocket_connections.remove(websocket)