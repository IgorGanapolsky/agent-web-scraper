#!/usr/bin/env python3
"""Simple Slack webhook test"""

import requests
import os
from dotenv import load_dotenv

load_dotenv("../../.env")

webhook_url = os.getenv("SLACK_WEBHOOK_URL")
print(f"Testing webhook: {webhook_url[:50]}...")

if webhook_url:
    test_message = {
        "text": "🧪 SLACK TEST: If you see this, the webhook is working!",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "✅ *Slack Integration Test*\n📱 Your newsletter pipeline can send notifications!"
                }
            }
        ]
    }
    
    try:
        response = requests.post(webhook_url, json=test_message)
        print(f"Response: {response.status_code}")
        print(f"Text: {response.text}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Check your #chatgpt channel!")
        else:
            print(f"❌ FAILED: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
else:
    print("❌ No webhook URL found")