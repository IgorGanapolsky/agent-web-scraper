#!/usr/bin/env python3
"""
Test script for Stripe revenue Slack notifications
Tests the CFO's revenue monitoring system with sample payments
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.api.stripe_webhooks import send_revenue_slack_notification


async def test_revenue_notifications():
    """Test different types of revenue notifications"""
    
    print("🧪 Testing CFO Revenue Slack Notifications...\n")
    
    # Test case 1: Basic payment
    print("📝 Test 1: Basic payment ($19)")
    basic_payment = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_email": "test.customer@example.com",
        "amount": 19.00,
        "currency": "USD",
        "tier": "basic",
        "trial_conversion": False,
        "mrr_impact": 19.00
    }
    
    success1 = await send_revenue_slack_notification(basic_payment)
    print(f"✅ Basic payment notification: {'Sent' if success1 else 'Failed'}\n")
    
    await asyncio.sleep(2)  # Avoid rate limiting
    
    # Test case 2: Trial conversion
    print("📝 Test 2: Trial conversion ($29)")
    trial_conversion = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_email": "trial.convert@example.com", 
        "amount": 29.00,
        "currency": "USD",
        "tier": "professional",
        "trial_conversion": True,
        "mrr_impact": 29.00
    }
    
    success2 = await send_revenue_slack_notification(trial_conversion)
    print(f"✅ Trial conversion notification: {'Sent' if success2 else 'Failed'}\n")
    
    await asyncio.sleep(2)
    
    # Test case 3: High-value enterprise payment
    print("📝 Test 3: Enterprise payment ($49)")
    enterprise_payment = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_email": "enterprise.customer@bigcorp.com",
        "amount": 49.00,
        "currency": "USD", 
        "tier": "enterprise",
        "trial_conversion": False,
        "mrr_impact": 49.00
    }
    
    success3 = await send_revenue_slack_notification(enterprise_payment)
    print(f"✅ Enterprise payment notification: {'Sent' if success3 else 'Failed'}\n")
    
    await asyncio.sleep(2)
    
    # Test case 4: Large annual payment
    print("📝 Test 4: Annual subscription ($348)")
    annual_payment = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_email": "annual.customer@startup.io",
        "amount": 348.00,  # $29 x 12 months
        "currency": "USD",
        "tier": "professional_annual",
        "trial_conversion": True,
        "mrr_impact": 29.00  # Monthly MRR impact
    }
    
    success4 = await send_revenue_slack_notification(annual_payment)
    print(f"✅ Annual payment notification: {'Sent' if success4 else 'Failed'}\n")
    
    # Summary
    total_tests = 4
    successful_tests = sum([success1, success2, success3, success4])
    
    print(f"🎯 Test Summary:")
    print(f"   Total tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Success rate: {(successful_tests/total_tests)*100:.1f}%")
    
    if successful_tests == total_tests:
        print(f"\n🎉 All tests passed! CFO revenue notifications are working!")
        print(f"💰 Slack will now notify you every time money is made!")
    else:
        print(f"\n⚠️  Some tests failed. Check Slack webhook configuration.")
        print(f"   Make sure SLACK_WEBHOOK_CHATGPT environment variable is set.")
        
    return successful_tests == total_tests


async def test_daily_progress_tracking():
    """Test daily progress tracking toward $300/day goal"""
    
    print(f"\n📊 Testing Daily Progress Tracking...\n")
    
    # Simulate a series of payments throughout the day
    daily_payments = [
        {"amount": 29.00, "customer": "morning_customer@email.com", "tier": "pro"},
        {"amount": 19.00, "customer": "lunch_customer@email.com", "tier": "basic"},
        {"amount": 49.00, "customer": "afternoon_customer@email.com", "tier": "enterprise"},
        {"amount": 29.00, "customer": "evening_customer@email.com", "tier": "pro"},
    ]
    
    total_daily_revenue = 0
    
    for i, payment in enumerate(daily_payments, 1):
        total_daily_revenue += payment["amount"]
        
        payment_data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "customer_email": payment["customer"],
            "amount": payment["amount"],
            "currency": "USD",
            "tier": payment["tier"],
            "trial_conversion": False,
            "mrr_impact": payment["amount"]
        }
        
        print(f"💰 Payment {i}: ${payment['amount']:.2f} (Daily total: ${total_daily_revenue:.2f})")
        
        success = await send_revenue_slack_notification(payment_data)
        if not success:
            print(f"   ❌ Failed to send notification")
        else:
            print(f"   ✅ Notification sent")
            
        await asyncio.sleep(1)  # Brief pause between notifications
        
    # Calculate progress toward $300/day goal
    progress_percentage = (total_daily_revenue / 300.0) * 100
    print(f"\n📈 Daily Progress Summary:")
    print(f"   Revenue: ${total_daily_revenue:.2f}")
    print(f"   Target: $300.00")
    print(f"   Progress: {progress_percentage:.1f}%")
    print(f"   Remaining: ${300.0 - total_daily_revenue:.2f}")
    
    if total_daily_revenue >= 300:
        print(f"   🎯 DAILY TARGET ACHIEVED! 🎉")
    else:
        print(f"   📊 {300.0 - total_daily_revenue:.0f} more dollars needed to hit target")


if __name__ == "__main__":
    print("🚀 CFO Revenue Slack Notification Test Suite\n")
    print("=" * 50)
    
    try:
        # Run basic notification tests
        success = asyncio.run(test_revenue_notifications())
        
        if success:
            # Run daily progress tests if basic tests pass
            asyncio.run(test_daily_progress_tracking())
            
        print("\n" + "=" * 50)
        print("🏁 Test suite completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")