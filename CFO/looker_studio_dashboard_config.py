#!/usr/bin/env python3
"""
CFO Looker Studio Dashboard Configuration
24-Hour Implementation: Firebase Analytics → BigQuery → Looker Studio
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.config.logging import get_logger

logger = get_logger(__name__)


class LookerStudioDashboardBuilder:
    """
    CFO Business Intelligence Dashboard Builder
    Integrates Firebase Analytics with Looker Studio for real-time revenue tracking
    """
    
    def __init__(self):
        self.project_id = "cfo-bi-dashboard"
        self.dataset_id = "revenue_analytics"
        self.dashboard_config = self._initialize_dashboard_config()
        
    def _initialize_dashboard_config(self) -> Dict[str, Any]:
        """Initialize Looker Studio dashboard configuration"""
        
        return {
            "dashboard_title": "CFO Executive Business Intelligence - $300/Day Revenue Tracking",
            "refresh_interval": "5_minutes",
            "mobile_responsive": True,
            "theme": "executive_dark",
            "panels": self._get_dashboard_panels(),
            "filters": self._get_dashboard_filters(),
            "alerts": self._get_alert_configuration()
        }
    
    def _get_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Define dashboard panels for revenue and business intelligence"""
        
        return [
            {
                "panel_id": "revenue_performance",
                "title": "Revenue Performance",
                "position": {"row": 1, "col": 1, "width": 6, "height": 4},
                "charts": [
                    {
                        "type": "scorecard",
                        "title": "Daily Revenue vs Target",
                        "metric": "daily_revenue",
                        "target": 300,
                        "format": "currency_usd",
                        "thresholds": {
                            "red": {"min": 0, "max": 150},
                            "yellow": {"min": 150, "max": 250},
                            "green": {"min": 250, "max": 500}
                        }
                    },
                    {
                        "type": "line_chart",
                        "title": "Revenue Trend (Last 30 Days)",
                        "x_axis": "date",
                        "y_axis": "daily_revenue",
                        "target_line": 300,
                        "smoothing": "7_day_average"
                    }
                ]
            },
            {
                "panel_id": "conversion_funnel",
                "title": "Conversion Funnel Analysis", 
                "position": {"row": 1, "col": 7, "width": 6, "height": 4},
                "charts": [
                    {
                        "type": "funnel_chart",
                        "title": "Customer Acquisition Funnel",
                        "stages": [
                            {"name": "Trial Signups", "metric": "trial_signup_count"},
                            {"name": "Diagnostic Sessions", "metric": "diagnostic_session_booked_count"},
                            {"name": "Pilot Conversions", "metric": "pilot_customer_converted_count"}
                        ],
                        "conversion_rates": True,
                        "time_period": "last_30_days"
                    },
                    {
                        "type": "table",
                        "title": "Conversion Rates by Stage",
                        "columns": ["stage", "count", "conversion_rate", "improvement"],
                        "data_source": "funnel_analysis"
                    }
                ]
            },
            {
                "panel_id": "customer_acquisition",
                "title": "Customer Acquisition",
                "position": {"row": 5, "col": 1, "width": 4, "height": 3},
                "charts": [
                    {
                        "type": "line_chart",
                        "title": "Daily New Signups",
                        "x_axis": "date",
                        "y_axis": "trial_signup_count",
                        "target_line": 10,
                        "color": "blue"
                    },
                    {
                        "type": "pie_chart",
                        "title": "Signup Sources",
                        "metric": "trial_signup_source",
                        "categories": ["organic", "paid", "referral", "direct"]
                    }
                ]
            },
            {
                "panel_id": "revenue_breakdown",
                "title": "Revenue by Tier",
                "position": {"row": 5, "col": 5, "width": 4, "height": 3},
                "charts": [
                    {
                        "type": "donut_chart", 
                        "title": "Revenue Distribution",
                        "metric": "revenue_by_tier",
                        "categories": ["pilot_99", "professional_299", "enterprise_1199"],
                        "colors": ["#4CAF50", "#2196F3", "#FF9800"]
                    },
                    {
                        "type": "bar_chart",
                        "title": "Customer Count by Tier",
                        "x_axis": "tier",
                        "y_axis": "customer_count",
                        "horizontal": True
                    }
                ]
            },
            {
                "panel_id": "business_health",
                "title": "Business Health Indicators",
                "position": {"row": 5, "col": 9, "width": 4, "height": 3},
                "charts": [
                    {
                        "type": "gauge",
                        "title": "Monthly Recurring Revenue",
                        "metric": "mrr",
                        "min": 0,
                        "max": 10000,
                        "target": 9000,
                        "format": "currency_usd"
                    },
                    {
                        "type": "scorecard",
                        "title": "Customer Lifetime Value",
                        "metric": "avg_ltv",
                        "format": "currency_usd",
                        "comparison": "previous_month"
                    }
                ]
            }
        ]
    
    def _get_dashboard_filters(self) -> List[Dict[str, Any]]:
        """Define dashboard filters for data segmentation"""
        
        return [
            {
                "filter_id": "date_range",
                "type": "date_range_picker",
                "label": "Date Range",
                "default": "last_30_days",
                "options": ["today", "yesterday", "last_7_days", "last_30_days", "last_90_days", "custom"]
            },
            {
                "filter_id": "customer_tier",
                "type": "multi_select",
                "label": "Customer Tier",
                "options": ["pilot", "professional", "enterprise"],
                "default": ["pilot", "professional", "enterprise"]
            },
            {
                "filter_id": "signup_source",
                "type": "dropdown",
                "label": "Signup Source",
                "options": ["all", "organic", "paid", "referral", "direct"],
                "default": "all"
            }
        ]
    
    def _get_alert_configuration(self) -> List[Dict[str, Any]]:
        """Configure automated alerts for business metrics"""
        
        return [
            {
                "alert_id": "daily_revenue_low",
                "title": "Daily Revenue Below Target",
                "metric": "daily_revenue",
                "condition": "less_than",
                "threshold": 250,
                "frequency": "real_time",
                "channels": ["slack", "email"],
                "recipients": ["ceo@company.com", "cfo@company.com"]
            },
            {
                "alert_id": "conversion_rate_drop",
                "title": "Conversion Rate Below Threshold",
                "metric": "trial_to_pilot_conversion_rate",
                "condition": "less_than",
                "threshold": 15,
                "frequency": "daily",
                "channels": ["slack"]
            },
            {
                "alert_id": "signup_volume_low",
                "title": "Low Signup Volume Alert",
                "metric": "daily_trial_signups",
                "condition": "less_than",
                "threshold": 10,
                "frequency": "daily",
                "channels": ["slack", "email"]
            },
            {
                "alert_id": "revenue_target_achieved",
                "title": "Daily Revenue Target Achieved!",
                "metric": "daily_revenue",
                "condition": "greater_than_or_equal",
                "threshold": 300,
                "frequency": "immediate",
                "channels": ["slack"],
                "celebration": True
            }
        ]
    
    def generate_bigquery_schema(self) -> Dict[str, Any]:
        """Generate BigQuery schema for Firebase Analytics data"""
        
        return {
            "tables": {
                "events": {
                    "description": "Firebase Analytics events for conversion tracking",
                    "schema": [
                        {"name": "event_timestamp", "type": "TIMESTAMP", "description": "Event occurrence time"},
                        {"name": "user_id", "type": "STRING", "description": "Unique user identifier"},
                        {"name": "event_name", "type": "STRING", "description": "Event type name"},
                        {"name": "event_params", "type": "RECORD", "mode": "REPEATED", "description": "Event parameters"},
                        {"name": "user_properties", "type": "RECORD", "mode": "REPEATED", "description": "User properties"},
                        {"name": "geo", "type": "RECORD", "description": "Geographic information"},
                        {"name": "device", "type": "RECORD", "description": "Device information"},
                        {"name": "traffic_source", "type": "RECORD", "description": "Traffic source data"}
                    ]
                },
                "revenue": {
                    "description": "Revenue data from Stripe integration",
                    "schema": [
                        {"name": "transaction_id", "type": "STRING", "description": "Stripe transaction ID"},
                        {"name": "user_id", "type": "STRING", "description": "Customer user ID"},
                        {"name": "amount", "type": "NUMERIC", "description": "Transaction amount in USD"},
                        {"name": "tier", "type": "STRING", "description": "Customer tier"},
                        {"name": "transaction_timestamp", "type": "TIMESTAMP", "description": "Payment timestamp"},
                        {"name": "subscription_id", "type": "STRING", "description": "Stripe subscription ID"},
                        {"name": "payment_method", "type": "STRING", "description": "Payment method used"}
                    ]
                },
                "customer_metrics": {
                    "description": "Aggregated customer and business metrics",
                    "schema": [
                        {"name": "date", "type": "DATE", "description": "Metric date"},
                        {"name": "daily_revenue", "type": "NUMERIC", "description": "Total daily revenue"},
                        {"name": "new_customers", "type": "INTEGER", "description": "New customers acquired"},
                        {"name": "trial_signups", "type": "INTEGER", "description": "Trial signups count"},
                        {"name": "diagnostic_sessions", "type": "INTEGER", "description": "Diagnostic sessions booked"},
                        {"name": "pilot_conversions", "type": "INTEGER", "description": "Pilot tier conversions"},
                        {"name": "mrr", "type": "NUMERIC", "description": "Monthly recurring revenue"},
                        {"name": "churn_rate", "type": "NUMERIC", "description": "Customer churn rate"}
                    ]
                }
            }
        }
    
    def create_looker_studio_config(self) -> str:
        """Create Looker Studio dashboard JSON configuration"""
        
        config = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "created_by": "CFO_AI_Agent",
            "dashboard": self.dashboard_config,
            "data_sources": {
                "bigquery": {
                    "project_id": self.project_id,
                    "dataset_id": self.dataset_id,
                    "connection_type": "bigquery_direct",
                    "refresh_rate": "5_minutes"
                }
            },
            "deployment": {
                "environment": "production",
                "access_control": "executive_team",
                "mobile_optimized": True,
                "performance_monitoring": True
            }
        }
        
        return json.dumps(config, indent=2)
    
    def generate_sql_queries(self) -> Dict[str, str]:
        """Generate SQL queries for dashboard data sources"""
        
        return {
            "daily_revenue": """
                SELECT 
                    DATE(transaction_timestamp) as date,
                    SUM(amount) as daily_revenue,
                    COUNT(DISTINCT user_id) as paying_customers,
                    AVG(amount) as avg_transaction_value
                FROM `{project}.{dataset}.revenue`
                WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
                GROUP BY DATE(transaction_timestamp)
                ORDER BY date DESC
            """.format(project=self.project_id, dataset=self.dataset_id),
            
            "conversion_funnel": """
                WITH funnel_data AS (
                    SELECT 
                        user_id,
                        MIN(CASE WHEN event_name = 'trial_signup' THEN event_timestamp END) as trial_signup_time,
                        MIN(CASE WHEN event_name = 'diagnostic_session_booked' THEN event_timestamp END) as diagnostic_time,
                        MIN(CASE WHEN event_name = 'pilot_customer_converted' THEN event_timestamp END) as conversion_time
                    FROM `{project}.{dataset}.events`
                    WHERE event_name IN ('trial_signup', 'diagnostic_session_booked', 'pilot_customer_converted')
                    AND DATE(event_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                    GROUP BY user_id
                )
                SELECT 
                    COUNT(*) as trial_signups,
                    COUNT(diagnostic_time) as diagnostic_sessions,
                    COUNT(conversion_time) as pilot_conversions,
                    ROUND(COUNT(diagnostic_time) / COUNT(*) * 100, 2) as signup_to_diagnostic_rate,
                    ROUND(COUNT(conversion_time) / COUNT(diagnostic_time) * 100, 2) as diagnostic_to_conversion_rate,
                    ROUND(COUNT(conversion_time) / COUNT(*) * 100, 2) as overall_conversion_rate
                FROM funnel_data
            """.format(project=self.project_id, dataset=self.dataset_id),
            
            "revenue_by_tier": """
                SELECT 
                    tier,
                    COUNT(DISTINCT user_id) as customer_count,
                    SUM(amount) as total_revenue,
                    AVG(amount) as avg_revenue_per_customer,
                    SUM(amount) / (SELECT SUM(amount) FROM `{project}.{dataset}.revenue` 
                                  WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)) * 100 as revenue_percentage
                FROM `{project}.{dataset}.revenue`
                WHERE DATE(transaction_timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
                GROUP BY tier
                ORDER BY total_revenue DESC
            """.format(project=self.project_id, dataset=self.dataset_id)
        }


def main():
    """Generate CFO Looker Studio dashboard configuration"""
    
    print("🚀 CFO Looker Studio Dashboard Configuration Generator")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    try:
        # Initialize dashboard builder
        builder = LookerStudioDashboardBuilder()
        
        # Generate configuration files
        print("📊 Generating dashboard configuration...")
        looker_config = builder.create_looker_studio_config()
        
        print("📋 Generating BigQuery schema...")
        bigquery_schema = builder.generate_bigquery_schema()
        
        print("🔍 Generating SQL queries...")
        sql_queries = builder.generate_sql_queries()
        
        # Save configuration files
        config_dir = "data/looker_studio_config"
        os.makedirs(config_dir, exist_ok=True)
        
        with open(f"{config_dir}/dashboard_config.json", 'w') as f:
            f.write(looker_config)
            
        with open(f"{config_dir}/bigquery_schema.json", 'w') as f:
            json.dump(bigquery_schema, f, indent=2)
            
        with open(f"{config_dir}/sql_queries.sql", 'w') as f:
            for query_name, query in sql_queries.items():
                f.write(f"-- {query_name.upper()}\n{query}\n\n")
        
        print("✅ Configuration files generated successfully!")
        print(f"📁 Files saved to: {config_dir}")
        print("\n📊 Dashboard Features:")
        print("   - Real-time revenue tracking toward $300/day")
        print("   - Conversion funnel visualization")
        print("   - Customer acquisition analytics")
        print("   - Business health indicators")
        print("   - Automated alert system")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration generation failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎯 CFO Status: Dashboard configuration ready for Looker Studio deployment")
    else:
        print("\n❌ CFO Status: Configuration generation failed - review and retry")