"""
Claude Token Budget Monitor - CFO $100/Month Budget Management System
Implements real-time tracking, alerts, and optimization for Claude API costs.
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from app.config.logging import get_logger

logger = get_logger(__name__)

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class TokenUsage:
    """Token usage tracking for a single API call"""
    timestamp: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_input: float
    cost_output: float
    total_cost: float
    operation_type: str
    session_id: str = None

@dataclass
class BudgetAlert:
    """Budget alert configuration and tracking"""
    alert_id: str
    level: AlertLevel
    threshold_percentage: float
    threshold_amount: float
    message: str
    triggered_at: str = None
    acknowledged: bool = False

@dataclass
class ModelPricing:
    """Claude model pricing structure"""
    model_name: str
    input_cost_per_million: float
    output_cost_per_million: float
    performance_tier: str

class ClaudeTokenBudgetMonitor:
    """
    Comprehensive Claude token budget monitoring system for $100/month limit.
    
    Features:
    - Real-time cost tracking across all Claude models
    - Progressive budget alerts (50%, 70%, 85%, 95%)
    - Automatic model switching when budget constrained
    - Daily/weekly/monthly budget breakdowns
    - Cost optimization recommendations
    - Emergency cost cutoffs
    """
    
    # Claude model pricing (as of June 2025)
    MODEL_PRICING = {
        "claude-4": ModelPricing("claude-4", 15.0, 75.0, "premium"),
        "claude-4-sonnet": ModelPricing("claude-4-sonnet", 3.0, 15.0, "balanced"),
        "claude-3-haiku": ModelPricing("claude-3-haiku", 0.25, 1.25, "efficient"),
        "claude-3-opus": ModelPricing("claude-3-opus", 15.0, 75.0, "premium")
    }
    
    def __init__(self, monthly_budget: float = 100.0):
        self.monthly_budget = monthly_budget
        self.daily_budget = monthly_budget / 30  # ~$3.33/day
        self.hourly_budget = self.daily_budget / 24  # ~$0.14/hour
        
        # Storage
        self.data_dir = Path("data/token_monitoring")
        self.data_dir.mkdir(exist_ok=True)
        self.usage_file = self.data_dir / "token_usage_log.json"
        self.budget_file = self.data_dir / "budget_tracking.json"
        self.alerts_file = self.data_dir / "budget_alerts.json"
        
        # Current state
        self.current_usage = []
        self.budget_state = self._initialize_budget_state()
        self.active_alerts = []
        
        # Load existing data
        self._load_usage_history()
        self._load_budget_state()
        self._setup_default_alerts()
        
    def track_api_call(self, model: str, input_tokens: int, output_tokens: int, 
                      operation_type: str = "general", session_id: str = None) -> float:
        """
        Track a single Claude API call and return the cost.
        
        Args:
            model: Claude model name (e.g., "claude-4-sonnet")
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens  
            operation_type: Type of operation (code_generation, analysis, etc.)
            session_id: Optional session identifier
            
        Returns:
            float: Cost of this API call in USD
        """
        
        # Get model pricing
        pricing = self.MODEL_PRICING.get(model)
        if not pricing:
            logger.warning(f"Unknown model '{model}', using claude-4-sonnet pricing")
            pricing = self.MODEL_PRICING["claude-4-sonnet"]
            
        # Calculate costs
        input_cost = (input_tokens / 1_000_000) * pricing.input_cost_per_million
        output_cost = (output_tokens / 1_000_000) * pricing.output_cost_per_million
        total_cost = input_cost + output_cost
        
        # Create usage record
        usage = TokenUsage(
            timestamp=datetime.now().isoformat(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_input=input_cost,
            cost_output=output_cost,
            total_cost=total_cost,
            operation_type=operation_type,
            session_id=session_id
        )
        
        # Store usage
        self.current_usage.append(usage)
        self._update_budget_state(total_cost)
        
        # Check for budget alerts
        self._check_budget_thresholds()
        
        # Persist data
        self._persist_usage()
        self._persist_budget_state()
        
        logger.info(f"Claude API call tracked: {model} | ${total_cost:.4f} | {operation_type}")
        
        return total_cost
        
    def get_current_budget_status(self) -> Dict[str, Any]:
        """Get comprehensive current budget status"""
        
        now = datetime.now()
        
        # Calculate current period costs
        daily_cost = self._get_period_cost(now.date())
        weekly_cost = self._get_weekly_cost()
        monthly_cost = self._get_monthly_cost()
        
        # Calculate utilization
        daily_utilization = (daily_cost / self.daily_budget) * 100
        monthly_utilization = (monthly_cost / self.monthly_budget) * 100
        
        # Remaining budgets
        daily_remaining = max(0, self.daily_budget - daily_cost)
        monthly_remaining = max(0, self.monthly_budget - monthly_cost)
        
        return {
            "budget_limits": {
                "monthly_budget": self.monthly_budget,
                "daily_budget": self.daily_budget,
                "hourly_budget": self.hourly_budget
            },
            "current_usage": {
                "daily_cost": round(daily_cost, 4),
                "weekly_cost": round(weekly_cost, 4),
                "monthly_cost": round(monthly_cost, 4)
            },
            "utilization": {
                "daily_percentage": round(daily_utilization, 1),
                "monthly_percentage": round(monthly_utilization, 1)
            },
            "remaining": {
                "daily_remaining": round(daily_remaining, 4),
                "monthly_remaining": round(monthly_remaining, 4),
                "estimated_days_remaining": round(monthly_remaining / max(daily_cost, 0.01), 1)
            },
            "status": self._get_budget_status_level(monthly_utilization),
            "active_alerts": len([a for a in self.active_alerts if not a.acknowledged]),
            "last_updated": now.isoformat()
        }
        
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get model selection recommendations based on current budget status"""
        
        status = self.get_current_budget_status()
        monthly_utilization = status["utilization"]["monthly_percentage"]
        daily_remaining = status["remaining"]["daily_remaining"]
        
        # Model switching logic
        if monthly_utilization >= 95:
            recommended_model = "claude-3-haiku"
            reason = "Emergency budget conservation - use most efficient model"
            allowed_operations = ["simple_queries", "data_processing"]
        elif monthly_utilization >= 85:
            recommended_model = "claude-4-sonnet" 
            reason = "Budget conservation - avoid premium models"
            allowed_operations = ["code_generation", "analysis", "simple_strategy"]
        elif monthly_utilization >= 70:
            recommended_model = "claude-4-sonnet"
            reason = "Balanced efficiency and performance"
            allowed_operations = ["all_except_complex_strategy"]
        elif daily_remaining < 0.50:
            recommended_model = "claude-4-sonnet"
            reason = "Daily budget protection"
            allowed_operations = ["essential_only"]
        else:
            recommended_model = "claude-4"
            reason = "Full budget available - optimal performance"
            allowed_operations = ["all_operations"]
            
        return {
            "recommended_model": recommended_model,
            "reason": reason,
            "allowed_operations": allowed_operations,
            "cost_comparison": {
                model: {
                    "input_cost": f"${pricing.input_cost_per_million}/1M tokens",
                    "output_cost": f"${pricing.output_cost_per_million}/1M tokens",
                    "efficiency_vs_haiku": f"{pricing.input_cost_per_million / 0.25:.1f}x"
                }
                for model, pricing in self.MODEL_PRICING.items()
            },
            "budget_impact": {
                "safe_daily_calls": int(daily_remaining / 0.05),  # Assuming $0.05 avg per call
                "high_cost_calls_remaining": int(daily_remaining / 0.20)  # $0.20 for complex calls
            }
        }
        
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive cost optimization report"""
        
        # Analyze recent usage patterns
        recent_usage = self._get_recent_usage(days=7)
        
        if not recent_usage:
            return {"error": "No recent usage data available"}
            
        # Usage analysis
        total_calls = len(recent_usage)
        total_cost = sum(u.total_cost for u in recent_usage)
        avg_cost_per_call = total_cost / total_calls if total_calls > 0 else 0
        
        # Model distribution
        model_stats = {}
        for usage in recent_usage:
            if usage.model not in model_stats:
                model_stats[usage.model] = {"calls": 0, "cost": 0.0, "tokens": 0}
            model_stats[usage.model]["calls"] += 1
            model_stats[usage.model]["cost"] += usage.total_cost
            model_stats[usage.model]["tokens"] += usage.input_tokens + usage.output_tokens
            
        # Cost savings opportunities
        expensive_calls = [u for u in recent_usage if u.total_cost > 0.10]
        premium_model_usage = [u for u in recent_usage if u.model in ["claude-4", "claude-3-opus"]]
        
        # Calculate potential savings
        potential_savings = 0.0
        for usage in premium_model_usage:
            if usage.operation_type in ["data_processing", "simple_analysis"]:
                # Could use Sonnet instead
                sonnet_cost = (usage.input_tokens / 1_000_000) * 3.0 + (usage.output_tokens / 1_000_000) * 15.0
                potential_savings += usage.total_cost - sonnet_cost
                
        return {
            "usage_summary": {
                "period": "Last 7 days",
                "total_calls": total_calls,
                "total_cost": round(total_cost, 4),
                "average_cost_per_call": round(avg_cost_per_call, 4),
                "daily_average": round(total_cost / 7, 4)
            },
            "model_distribution": {
                model: {
                    "calls": stats["calls"],
                    "cost": round(stats["cost"], 4),
                    "percentage": round((stats["cost"] / total_cost) * 100, 1),
                    "avg_cost_per_call": round(stats["cost"] / stats["calls"], 4)
                }
                for model, stats in model_stats.items()
            },
            "optimization_opportunities": {
                "expensive_calls_count": len(expensive_calls),
                "premium_model_overuse": len(premium_model_usage),
                "potential_monthly_savings": round(potential_savings * 4.3, 2),  # Weekly to monthly
                "efficiency_score": round(100 - (len(premium_model_usage) / total_calls * 50), 1)
            },
            "recommendations": self._generate_optimization_recommendations(model_stats, total_cost, expensive_calls)
        }
        
    def emergency_budget_cutoff(self) -> Dict[str, Any]:
        """Implement emergency budget cutoff procedures"""
        
        status = self.get_current_budget_status()
        
        # Create emergency alert
        emergency_alert = BudgetAlert(
            alert_id=f"emergency_{int(time.time())}",
            level=AlertLevel.EMERGENCY,
            threshold_percentage=100.0,
            threshold_amount=self.monthly_budget,
            message="EMERGENCY: Monthly budget exceeded. All Claude API calls suspended.",
            triggered_at=datetime.now().isoformat()
        )
        
        self.active_alerts.append(emergency_alert)
        
        # Log emergency
        logger.critical(f"EMERGENCY BUDGET CUTOFF: ${status['current_usage']['monthly_cost']:.2f} exceeds ${self.monthly_budget:.2f}")
        
        return {
            "cutoff_activated": True,
            "reason": "Monthly budget exceeded",
            "current_usage": status["current_usage"]["monthly_cost"],
            "budget_limit": self.monthly_budget,
            "emergency_alert_id": emergency_alert.alert_id,
            "next_steps": [
                "All AI operations suspended until next billing cycle",
                "Review and optimize usage patterns",
                "Consider budget increase if business-critical",
                "Implement stricter daily limits"
            ]
        }
        
    def _initialize_budget_state(self) -> Dict[str, Any]:
        """Initialize budget tracking state"""
        return {
            "monthly_start_date": datetime.now().replace(day=1).isoformat(),
            "total_monthly_cost": 0.0,
            "daily_costs": {},
            "last_reset": datetime.now().isoformat(),
            "budget_alerts_triggered": []
        }
        
    def _setup_default_alerts(self) -> None:
        """Setup default budget alert thresholds"""
        default_alerts = [
            BudgetAlert("daily_50", AlertLevel.INFO, 50.0, self.daily_budget * 0.5, 
                       "Daily budget 50% utilized"),
            BudgetAlert("daily_80", AlertLevel.WARNING, 80.0, self.daily_budget * 0.8,
                       "Daily budget 80% utilized - consider optimization"),
            BudgetAlert("monthly_50", AlertLevel.INFO, 50.0, self.monthly_budget * 0.5,
                       "Monthly budget 50% utilized"),
            BudgetAlert("monthly_70", AlertLevel.WARNING, 70.0, self.monthly_budget * 0.7,
                       "Monthly budget 70% utilized - monitor closely"),
            BudgetAlert("monthly_85", AlertLevel.CRITICAL, 85.0, self.monthly_budget * 0.85,
                       "Monthly budget 85% utilized - implement restrictions"),
            BudgetAlert("monthly_95", AlertLevel.EMERGENCY, 95.0, self.monthly_budget * 0.95,
                       "Monthly budget 95% utilized - emergency protocols activated")
        ]
        
        # Only add alerts that don't already exist
        existing_ids = {alert.alert_id for alert in self.active_alerts}
        for alert in default_alerts:
            if alert.alert_id not in existing_ids:
                self.active_alerts.append(alert)
                
    def _check_budget_thresholds(self) -> None:
        """Check if any budget thresholds have been crossed"""
        
        status = self.get_current_budget_status()
        daily_cost = status["current_usage"]["daily_cost"]
        monthly_cost = status["current_usage"]["monthly_cost"]
        
        for alert in self.active_alerts:
            if alert.triggered_at or alert.acknowledged:
                continue  # Skip already triggered or acknowledged alerts
                
            should_trigger = False
            
            if "daily" in alert.alert_id:
                should_trigger = daily_cost >= alert.threshold_amount
            elif "monthly" in alert.alert_id:
                should_trigger = monthly_cost >= alert.threshold_amount
                
            if should_trigger:
                alert.triggered_at = datetime.now().isoformat()
                logger.warning(f"Budget alert triggered: {alert.message}")
                
                # For emergency alerts, also log critical
                if alert.level == AlertLevel.EMERGENCY:
                    logger.critical(f"EMERGENCY BUDGET ALERT: {alert.message}")
                    
    def _get_period_cost(self, date) -> float:
        """Get total cost for a specific date"""
        date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
        return sum(
            usage.total_cost for usage in self.current_usage
            if usage.timestamp.startswith(date_str)
        )
        
    def _get_weekly_cost(self) -> float:
        """Get total cost for the current week"""
        week_start = datetime.now() - timedelta(days=7)
        return sum(
            usage.total_cost for usage in self.current_usage
            if datetime.fromisoformat(usage.timestamp) >= week_start
        )
        
    def _get_monthly_cost(self) -> float:
        """Get total cost for the current month"""
        month_start = datetime.now().replace(day=1)
        return sum(
            usage.total_cost for usage in self.current_usage
            if datetime.fromisoformat(usage.timestamp) >= month_start
        )
        
    def _get_recent_usage(self, days: int = 7) -> List[TokenUsage]:
        """Get usage records from the last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            usage for usage in self.current_usage
            if datetime.fromisoformat(usage.timestamp) >= cutoff
        ]
        
    def _get_budget_status_level(self, utilization_percentage: float) -> str:
        """Get budget status level based on utilization"""
        if utilization_percentage >= 95:
            return "EMERGENCY"
        elif utilization_percentage >= 85:
            return "CRITICAL"
        elif utilization_percentage >= 70:
            return "WARNING"
        elif utilization_percentage >= 50:
            return "CAUTION"
        else:
            return "HEALTHY"
            
    def _generate_optimization_recommendations(self, model_stats: Dict, total_cost: float, expensive_calls: List) -> List[str]:
        """Generate optimization recommendations based on usage patterns"""
        
        recommendations = []
        
        # Check for premium model overuse
        premium_cost = sum(
            stats["cost"] for model, stats in model_stats.items()
            if model in ["claude-4", "claude-3-opus"]
        )
        
        if premium_cost / total_cost > 0.3:  # >30% on premium models
            recommendations.append(
                "Consider using claude-4-sonnet for routine tasks to reduce costs by 80%"
            )
            
        # Check for expensive individual calls
        if len(expensive_calls) > len(self.current_usage) * 0.1:  # >10% expensive calls
            recommendations.append(
                "Optimize prompt engineering to reduce token usage per call"
            )
            
        # Check for high-frequency usage
        if len(self.current_usage) > 50:  # >50 calls in recent period
            recommendations.append(
                "Implement prompt caching and batch processing to reduce API calls"
            )
            
        # General recommendations
        recommendations.extend([
            "Monitor daily budget utilization and switch models when approaching limits",
            "Use claude-3-haiku for simple data processing tasks",
            "Implement automatic model selection based on task complexity",
            "Set up daily cost alerts to prevent budget overruns"
        ])
        
        return recommendations
        
    def _update_budget_state(self, cost: float) -> None:
        """Update budget state with new cost"""
        self.budget_state["total_monthly_cost"] += cost
        
        today = datetime.now().date().isoformat()
        if today not in self.budget_state["daily_costs"]:
            self.budget_state["daily_costs"][today] = 0.0
        self.budget_state["daily_costs"][today] += cost
        
    def _load_usage_history(self) -> None:
        """Load usage history from file"""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    data = json.load(f)
                    self.current_usage = [
                        TokenUsage(**usage_data) for usage_data in data.get("usage_records", [])
                    ]
                logger.info(f"Loaded {len(self.current_usage)} usage records")
            except Exception as e:
                logger.error(f"Failed to load usage history: {e}")
                
    def _load_budget_state(self) -> None:
        """Load budget state from file"""
        if self.budget_file.exists():
            try:
                with open(self.budget_file, 'r') as f:
                    self.budget_state = json.load(f)
                logger.info("Loaded budget state")
            except Exception as e:
                logger.error(f"Failed to load budget state: {e}")
                
    def _persist_usage(self) -> None:
        """Persist usage records to file"""
        try:
            data = {
                "usage_records": [asdict(usage) for usage in self.current_usage],
                "last_updated": datetime.now().isoformat()
            }
            with open(self.usage_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist usage data: {e}")
            
    def _persist_budget_state(self) -> None:
        """Persist budget state to file"""
        try:
            self.budget_state["last_updated"] = datetime.now().isoformat()
            with open(self.budget_file, 'w') as f:
                json.dump(self.budget_state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist budget state: {e}")

# Global monitor instance
_token_monitor = None

def get_claude_token_monitor() -> ClaudeTokenBudgetMonitor:
    """Get the global Claude token budget monitor instance"""
    global _token_monitor
    if _token_monitor is None:
        _token_monitor = ClaudeTokenBudgetMonitor()
    return _token_monitor

# Convenience functions
def track_claude_api_call(model: str, input_tokens: int, output_tokens: int, 
                         operation_type: str = "general") -> float:
    """Track a Claude API call and return cost"""
    monitor = get_claude_token_monitor()
    return monitor.track_api_call(model, input_tokens, output_tokens, operation_type)

def get_budget_status() -> Dict[str, Any]:
    """Get current budget status"""
    monitor = get_claude_token_monitor()
    return monitor.get_current_budget_status()

def get_model_recommendation() -> str:
    """Get recommended Claude model based on current budget"""
    monitor = get_claude_token_monitor()
    recommendations = monitor.get_model_recommendations()
    return recommendations["recommended_model"]