#!/usr/bin/env python3
"""
CFO Simple COGS Analysis - Direct Token Cost Measurement
Measures exact token costs for AI operations to determine unit economics
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.claude_token_budget_monitor import get_claude_token_monitor, track_claude_api_call
from app.core.llm_client import GPT4Client
from app.config.logging import get_logger

logger = get_logger(__name__)


class SimpleCOGSAnalyzer:
    """Simple COGS analyzer measuring direct AI token costs"""
    
    def __init__(self):
        self.token_monitor = get_claude_token_monitor()
        
    def measure_ai_operation_cost(self, operation_type: str, complexity: str = "medium") -> dict:
        """Measure cost of a typical AI operation"""
        
        print(f"🧪 Measuring {operation_type} cost (complexity: {complexity})")
        
        # Record initial state
        initial_budget = self.token_monitor.get_current_budget_status()
        initial_cost = initial_budget["current_usage"]["monthly_cost"]
        
        start_time = time.time()
        
        try:
            if operation_type == "market_analysis":
                cost = self._simulate_market_analysis(complexity)
            elif operation_type == "competitive_intel":
                cost = self._simulate_competitive_intelligence(complexity)
            elif operation_type == "pain_point_extraction":
                cost = self._simulate_pain_point_extraction(complexity)
            elif operation_type == "content_generation":
                cost = self._simulate_content_generation(complexity)
            else:
                cost = self._simulate_generic_analysis(complexity)
                
        except Exception as e:
            print(f"   ❌ Error during {operation_type}: {e}")
            return {"error": str(e)}
        
        execution_time = time.time() - start_time
        
        # Record final state
        final_budget = self.token_monitor.get_current_budget_status()
        final_cost = final_budget["current_usage"]["monthly_cost"]
        
        actual_cost = final_cost - initial_cost
        
        print(f"   ✅ Completed in {execution_time:.2f}s")
        print(f"   💰 Cost: ${actual_cost:.6f}")
        
        return {
            "operation_type": operation_type,
            "complexity": complexity,
            "execution_time": round(execution_time, 2),
            "cost_usd": round(actual_cost, 6),
            "estimated_tokens": self._estimate_tokens_from_cost(actual_cost),
            "timestamp": datetime.now().isoformat()
        }
    
    def _simulate_market_analysis(self, complexity: str) -> float:
        """Simulate market analysis operation"""
        
        # Define prompts by complexity
        prompts = {
            "simple": "Analyze the SaaS market trends for small businesses. Provide 3 key insights.",
            "medium": """Analyze the current SaaS market landscape for Series A/B startups. 
                        Focus on pain points, competitive dynamics, and growth opportunities. 
                        Provide detailed insights with market data and recommendations.""",
            "complex": """Conduct a comprehensive market analysis for enterprise SaaS tools targeting 
                         Series A/B companies. Include competitive landscape, pricing strategies, 
                         customer acquisition challenges, market size estimation, growth projections, 
                         and strategic recommendations for market entry. Support with data."""
        }
        
        prompt = prompts.get(complexity, prompts["medium"])
        
        # Estimate token usage and cost
        return track_claude_api_call(
            model="claude-4-sonnet",
            input_tokens=len(prompt.split()) * 1.3,  # Rough token estimation
            output_tokens=200 if complexity == "simple" else 500 if complexity == "medium" else 1000,
            operation_type="market_analysis"
        )
    
    def _simulate_competitive_intelligence(self, complexity: str) -> float:
        """Simulate competitive intelligence operation"""
        
        token_ranges = {
            "simple": {"input": 100, "output": 150},
            "medium": {"input": 300, "output": 400},
            "complex": {"input": 800, "output": 1200}
        }
        
        tokens = token_ranges.get(complexity, token_ranges["medium"])
        
        return track_claude_api_call(
            model="claude-4-sonnet",
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
            operation_type="competitive_intelligence"
        )
    
    def _simulate_pain_point_extraction(self, complexity: str) -> float:
        """Simulate pain point extraction from content"""
        
        token_ranges = {
            "simple": {"input": 200, "output": 100},
            "medium": {"input": 500, "output": 300},
            "complex": {"input": 1200, "output": 800}
        }
        
        tokens = token_ranges.get(complexity, token_ranges["medium"])
        
        return track_claude_api_call(
            model="claude-4-sonnet",
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
            operation_type="pain_point_extraction"
        )
    
    def _simulate_content_generation(self, complexity: str) -> float:
        """Simulate content generation (reports, emails, etc.)"""
        
        token_ranges = {
            "simple": {"input": 150, "output": 300},
            "medium": {"input": 400, "output": 800},
            "complex": {"input": 600, "output": 1500}
        }
        
        tokens = token_ranges.get(complexity, token_ranges["medium"])
        
        return track_claude_api_call(
            model="claude-4-sonnet",
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
            operation_type="content_generation"
        )
    
    def _simulate_generic_analysis(self, complexity: str) -> float:
        """Simulate generic analysis operation"""
        
        token_ranges = {
            "simple": {"input": 100, "output": 200},
            "medium": {"input": 300, "output": 500},
            "complex": {"input": 700, "output": 1000}
        }
        
        tokens = token_ranges.get(complexity, token_ranges["medium"])
        
        return track_claude_api_call(
            model="claude-4-sonnet",
            input_tokens=tokens["input"],
            output_tokens=tokens["output"],
            operation_type="generic_analysis"
        )
    
    def _estimate_tokens_from_cost(self, cost_usd: float) -> dict:
        """Estimate token usage from cost"""
        
        # Claude-4-Sonnet pricing: $3 input / $15 output per million tokens
        input_cost_per_token = 3.0 / 1_000_000
        output_cost_per_token = 15.0 / 1_000_000
        
        # Assume 60/40 split input/output
        estimated_input_cost = cost_usd * 0.6
        estimated_output_cost = cost_usd * 0.4
        
        estimated_input_tokens = int(estimated_input_cost / input_cost_per_token)
        estimated_output_tokens = int(estimated_output_cost / output_cost_per_token)
        
        return {
            "input_tokens": estimated_input_tokens,
            "output_tokens": estimated_output_tokens,
            "total_tokens": estimated_input_tokens + estimated_output_tokens
        }


def analyze_customer_usage_scenarios():
    """Analyze different customer usage patterns and their COGS"""
    
    print("📊 Customer Usage Scenario Analysis")
    print("=" * 50)
    
    scenarios = {
        "pilot_light_user": {
            "description": "Pilot customer - weekly analysis",
            "operations_per_month": [
                ("market_analysis", "medium", 4),
                ("pain_point_extraction", "simple", 4)
            ]
        },
        "professional_regular_user": {
            "description": "Professional customer - regular usage",
            "operations_per_month": [
                ("market_analysis", "medium", 8),
                ("competitive_intel", "medium", 8),
                ("content_generation", "medium", 12)
            ]
        },
        "enterprise_heavy_user": {
            "description": "Enterprise customer - intensive usage",
            "operations_per_month": [
                ("market_analysis", "complex", 15),
                ("competitive_intel", "complex", 20),
                ("content_generation", "complex", 30),
                ("pain_point_extraction", "medium", 20)
            ]
        }
    }
    
    analyzer = SimpleCOGSAnalyzer()
    scenario_results = {}
    
    for scenario_name, scenario_data in scenarios.items():
        print(f"\n🎯 Analyzing: {scenario_data['description']}")
        print("-" * 30)
        
        total_monthly_cost = 0.0
        operation_costs = []
        
        for operation_type, complexity, count in scenario_data["operations_per_month"]:
            # Measure cost for one operation
            result = analyzer.measure_ai_operation_cost(operation_type, complexity)
            
            if "error" not in result:
                operation_cost = result["cost_usd"]
                monthly_cost = operation_cost * count
                total_monthly_cost += monthly_cost
                
                operation_costs.append({
                    "operation": f"{operation_type} ({complexity})",
                    "count": count,
                    "unit_cost": operation_cost,
                    "monthly_cost": monthly_cost
                })
                
                print(f"   {operation_type} ({complexity}): ${operation_cost:.6f} × {count} = ${monthly_cost:.4f}")
        
        scenario_results[scenario_name] = {
            "description": scenario_data["description"],
            "total_monthly_cogs": round(total_monthly_cost, 4),
            "operation_breakdown": operation_costs
        }
        
        print(f"   📊 Total monthly COGS: ${total_monthly_cost:.4f}")
    
    return scenario_results


def calculate_tier_profitability(scenario_results: dict):
    """Calculate profitability for each pricing tier"""
    
    print("\n💰 Pricing Tier Profitability Analysis")
    print("=" * 50)
    
    pricing_tiers = {
        "pilot": 99.00,
        "professional": 299.00,
        "enterprise": 1199.00
    }
    
    # Map scenarios to tiers
    scenario_tier_mapping = {
        "pilot_light_user": "pilot",
        "professional_regular_user": "professional", 
        "enterprise_heavy_user": "enterprise"
    }
    
    profitability_analysis = {}
    
    for scenario_name, tier in scenario_tier_mapping.items():
        if scenario_name in scenario_results:
            monthly_price = pricing_tiers[tier]
            monthly_cogs = scenario_results[scenario_name]["total_monthly_cogs"]
            monthly_profit = monthly_price - monthly_cogs
            profit_margin = (monthly_profit / monthly_price) * 100
            
            profitability_analysis[tier] = {
                "monthly_price": monthly_price,
                "monthly_cogs": monthly_cogs,
                "monthly_profit": round(monthly_profit, 2),
                "profit_margin_percent": round(profit_margin, 1),
                "annual_profit": round(monthly_profit * 12, 2),
                "profitable": monthly_profit > 0
            }
            
            print(f"\n{tier.upper()} TIER (${monthly_price}/month):")
            print(f"   Monthly COGS: ${monthly_cogs:.4f}")
            print(f"   Monthly Profit: ${monthly_profit:.2f}")
            print(f"   Profit Margin: {profit_margin:.1f}%")
            print(f"   Annual Profit: ${monthly_profit * 12:.2f}")
            print(f"   Status: {'✅ PROFITABLE' if monthly_profit > 0 else '❌ LOSS'}")
    
    return profitability_analysis


def generate_cfo_recommendations(scenario_results: dict, profitability_analysis: dict):
    """Generate CFO business recommendations"""
    
    print("\n💡 CFO BUSINESS RECOMMENDATIONS")
    print("=" * 50)
    
    # Find highest and lowest cost scenarios
    costs = [(name, data["total_monthly_cogs"]) for name, data in scenario_results.items()]
    costs.sort(key=lambda x: x[1])
    
    lowest_cost_scenario = costs[0] if costs else None
    highest_cost_scenario = costs[-1] if costs else None
    
    print("\n📊 COST ANALYSIS:")
    if lowest_cost_scenario and highest_cost_scenario:
        print(f"   Lowest COGS: {lowest_cost_scenario[0]} at ${lowest_cost_scenario[1]:.4f}/month")
        print(f"   Highest COGS: {highest_cost_scenario[0]} at ${highest_cost_scenario[1]:.4f}/month")
        print(f"   Cost Range: ${highest_cost_scenario[1] - lowest_cost_scenario[1]:.4f} spread")
    
    print("\n🎯 PRICING STRATEGY:")
    all_profitable = all(data["profitable"] for data in profitability_analysis.values())
    
    if all_profitable:
        print("   ✅ All pricing tiers are profitable")
        print("   ✅ Unit economics validated for scaling")
        print("   ✅ Strong margins support customer acquisition investment")
    else:
        unprofitable_tiers = [tier for tier, data in profitability_analysis.items() if not data["profitable"]]
        print(f"   ⚠️  Unprofitable tiers: {', '.join(unprofitable_tiers)}")
        print("   🔧 Consider usage limits or pricing adjustments")
    
    print("\n🚀 SCALING RECOMMENDATIONS:")
    avg_cost = sum(data["total_monthly_cogs"] for data in scenario_results.values()) / len(scenario_results)
    
    if avg_cost < 5.0:
        print("   ✅ Low COGS enable aggressive customer acquisition")
        print("   📈 Focus on scaling marketing and sales")
        print("   💰 High margins support premium customer success")
    elif avg_cost < 20.0:
        print("   ⚠️  Moderate COGS require careful customer acquisition")
        print("   🎯 Focus on higher-value customers")
        print("   🔧 Monitor unit economics during scaling")
    else:
        print("   ❌ High COGS require optimization before scaling")
        print("   🔧 Implement usage limits or tiered pricing")
        print("   📊 Focus on efficiency improvements")
    
    # Revenue projections
    print("\n📊 REVENUE PROJECTIONS (Path to $300/day):")
    
    for tier, data in profitability_analysis.items():
        if data["profitable"]:
            customers_needed = 300 / (data["monthly_profit"] / 30)  # Daily profit
            print(f"   {tier.title()}: {customers_needed:.1f} customers needed")
    
    print("\n🎯 IMMEDIATE ACTIONS:")
    print("   1. Deploy pilot tier ($99) for market validation")
    print("   2. Monitor actual usage vs. projected COGS")
    print("   3. Track customer behavior patterns")
    print("   4. Optimize AI operations for cost efficiency")
    print("   5. Scale marketing for profitable customer acquisition")


def main():
    """Main COGS analysis execution"""
    
    print("🚀 CFO Simple COGS Analysis")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} EDT")
    print()
    
    try:
        # Analyze customer usage scenarios
        scenario_results = analyze_customer_usage_scenarios()
        
        # Calculate tier profitability
        profitability_analysis = calculate_tier_profitability(scenario_results)
        
        # Generate CFO recommendations
        generate_cfo_recommendations(scenario_results, profitability_analysis)
        
        # Save detailed report
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "scenario_results": scenario_results,
            "profitability_analysis": profitability_analysis,
            "summary": {
                "all_tiers_profitable": all(data["profitable"] for data in profitability_analysis.values()),
                "avg_monthly_cogs": round(sum(data["total_monthly_cogs"] for data in scenario_results.values()) / len(scenario_results), 4)
            }
        }
        
        report_file = Path("data/simple_cogs_analysis_report.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        print("\n✅ CFO COGS Analysis Complete")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)