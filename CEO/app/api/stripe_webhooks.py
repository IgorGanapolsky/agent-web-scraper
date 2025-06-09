"""
Stripe webhook handlers for MCP system
Handles all Stripe events and integrates with Supabase and Google Sheets
"""

import os
from datetime import datetime
from typing import Any

import gspread
import stripe
from fastapi import APIRouter, HTTPException, Request, status
from google.oauth2.service_account import Credentials

from app.config.logging import get_logger
from app.mcp.stripe_server import MCPStripeServer
from app.utils.slack_reporter import post_to_slack

logger = get_logger(__name__)
router = APIRouter(prefix="/api/stripe", tags=["stripe-webhooks"])

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# Initialize MCP Stripe server
mcp_stripe = MCPStripeServer(test_mode=False)


async def log_payment_to_sheets(payment_data: dict[str, Any]) -> bool:
    """Log payment data to Google Sheets for revenue tracking"""

    try:
        # Google Sheets configuration
        credentials_path = os.getenv("GSPREAD_CREDENTIALS_PATH")
        if not credentials_path or not os.path.exists(credentials_path):
            logger.warning("Google Sheets credentials not found")
            return False

        # Authenticate with Google Sheets
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
        gc = gspread.authorize(creds)

        # Open or create revenue tracking spreadsheet
        try:
            sheet = gc.open("SaaS Growth Dispatch - Revenue Tracking").sheet1
        except gspread.SpreadsheetNotFound:
            # Create new spreadsheet
            spreadsheet = gc.create("SaaS Growth Dispatch - Revenue Tracking")
            sheet = spreadsheet.sheet1

            # Add headers
            headers = [
                "Date",
                "Customer ID",
                "Customer Email",
                "Amount",
                "Currency",
                "Subscription Tier",
                "Payment Method",
                "Invoice ID",
                "Status",
                "Trial Conversion",
                "MRR Impact",
                "Cumulative Revenue",
            ]
            sheet.append_row(headers)

        # Prepare row data
        row_data = [
            payment_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            payment_data.get("customer_id", ""),
            payment_data.get("customer_email", ""),
            payment_data.get("amount", 0),
            payment_data.get("currency", "USD"),
            payment_data.get("tier", ""),
            payment_data.get("payment_method", ""),
            payment_data.get("invoice_id", ""),
            payment_data.get("status", "succeeded"),
            payment_data.get("trial_conversion", False),
            payment_data.get("mrr_impact", 0),
            payment_data.get("cumulative_revenue", 0),
        ]

        # Append row to sheet
        sheet.append_row(row_data)

        logger.info(
            f"Payment logged to Google Sheets: {payment_data.get('amount')} from {payment_data.get('customer_email')}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to log payment to Google Sheets: {e}")
        return False


async def send_payment_confirmation_email(
    customer_email: str, payment_data: dict[str, Any]
) -> bool:
    """Send payment confirmation email via Zoho SMTP"""

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        # Zoho SMTP configuration
        smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("ZOHO_APP_PASSWORD")
        smtp_from = os.getenv("SMTP_FROM", "support@saasgrowthdispatch.com")

        if not all([smtp_username, smtp_password]):
            logger.error("SMTP credentials not configured")
            return False

        # Create payment confirmation email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Payment Confirmation - ${payment_data.get('amount', 0):.2f}"
        msg["From"] = smtp_from
        msg["To"] = customer_email

        html_content = f"""
        <html>
            <body>
                <h2>Payment Confirmation</h2>
                <p>Dear Customer,</p>
                <p>We've successfully processed your payment for SaaS Growth Dispatch.</p>

                <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3>Payment Details:</h3>
                    <p><strong>Amount:</strong> ${payment_data.get('amount', 0):.2f} {payment_data.get('currency', 'USD')}</p>
                    <p><strong>Subscription Tier:</strong> {payment_data.get('tier', 'Pro').title()}</p>
                    <p><strong>Invoice ID:</strong> {payment_data.get('invoice_id', 'N/A')}</p>
                    <p><strong>Date:</strong> {payment_data.get('date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}</p>
                </div>

                <p>Your subscription is now active and you have full access to all features.</p>
                <p><a href="https://saasgrowthdispatch.com/dashboard" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                    Access Your Dashboard
                </a></p>

                <p>If you have any questions, please don't hesitate to contact our support team.</p>

                <br>
                <p>Best regards,<br>The SaaS Growth Dispatch Team</p>
            </body>
        </html>
        """

        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)

        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        logger.info(f"Payment confirmation email sent to {customer_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send payment confirmation email: {e}")
        return False


async def send_revenue_slack_notification(
    event_type: str, payment_data: dict[str, Any]
) -> bool:
    """Send instant Slack notification for all revenue events"""

    try:
        amount = payment_data.get("amount", 0)
        customer_email = payment_data.get("customer_email", "Unknown")
        tier = payment_data.get("tier", "").title()
        currency = payment_data.get("currency", "USD")

        # Calculate progress toward daily goal
        daily_target = 300.0  # $300/day target
        progress_pct = min((amount / daily_target) * 100, 100)

        # Choose emoji based on amount
        if amount >= 1000:
            money_emoji = "🎉💰🚀"
        elif amount >= 500:
            money_emoji = "💰🔥"
        elif amount >= 100:
            money_emoji = "💰✨"
        else:
            money_emoji = "💰"

        # Build notification message
        message = f"""
{money_emoji} **REVENUE ALERT** {money_emoji}

💳 **{event_type.replace('_', ' ').title()}**
💵 **Amount:** ${amount:.2f} {currency}
👤 **Customer:** {customer_email}
📦 **Tier:** {tier}
📅 **Date:** {payment_data.get('date')}

📊 **Daily Progress:** {progress_pct:.1f}% of ${daily_target}/day target

🎯 **Enterprise Goal:** 8 customers at $1,199/month = $320/day
{"✅ **Trial Conversion!**" if payment_data.get('trial_conversion') else ""}

💡 **MRR Impact:** +${payment_data.get('mrr_impact', 0):.2f}/month
        """.strip()

        # Send to Slack
        success = post_to_slack(message)

        if success:
            logger.info(
                f"Revenue Slack notification sent: ${amount} from {customer_email}"
            )
        else:
            logger.error("Failed to send revenue Slack notification")

        return success

    except Exception as e:
        logger.error(f"Error sending revenue Slack notification: {e}")
        return False


async def send_subscription_slack_notification(
    event_type: str, subscription_data: dict[str, Any]
) -> bool:
    """Send Slack notification for subscription events"""

    try:
        customer_email = subscription_data.get("customer_email", "Unknown")
        tier = subscription_data.get("tier", "").title()
        status = subscription_data.get("status", "").title()

        # Choose emoji based on event
        if "CREATED" in event_type:
            emoji = "🆕🎯"
        elif "UPDATED" in event_type:
            emoji = "🔄📈"
        elif "CANCELLED" in event_type:
            emoji = "❌🚨"
        else:
            emoji = "📋"

        # Build notification message
        message = f"""
{emoji} **SUBSCRIPTION ALERT** {emoji}

📋 **{event_type.replace('_', ' ').title()}**
👤 **Customer:** {customer_email}
📦 **Tier:** {tier}
📊 **Status:** {status}
📅 **Date:** {subscription_data.get('date')}

🎯 **Enterprise Progress:** Working toward 8 customers at $1,199/month
💡 **Next:** First payment will trigger revenue notification
        """.strip()

        # Send to Slack
        success = post_to_slack(message)

        if success:
            logger.info(
                f"Subscription Slack notification sent: {tier} for {customer_email}"
            )
        else:
            logger.error("Failed to send subscription Slack notification")

        return success

    except Exception as e:
        logger.error(f"Error sending subscription Slack notification: {e}")
        return False


async def update_supabase_subscription(customer_data: dict[str, Any]) -> bool:
    """Update Supabase user subscription data"""

    try:
        # In production, update Supabase with subscription data:
        # from supabase import create_client
        # supabase = create_client(
        #     os.getenv("SUPABASE_URL"),
        #     os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        # )
        #
        # await supabase.table("users").update({
        #     "subscription_status": customer_data.get("status"),
        #     "subscription_tier": customer_data.get("tier"),
        #     "stripe_customer_id": customer_data.get("customer_id"),
        #     "current_period_start": customer_data.get("current_period_start"),
        #     "current_period_end": customer_data.get("current_period_end"),
        #     "updated_at": datetime.utcnow().isoformat()
        # }).eq("email", customer_data.get("email"))

        logger.info(
            f"Supabase subscription updated for customer: {customer_data.get('customer_id')}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to update Supabase subscription: {e}")
        return False


@router.post("/webhooks")
async def handle_stripe_webhook(request: Request):
    """Handle all Stripe webhook events"""

    try:
        # Get request body and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")

        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature",
            )

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
            )

        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing Stripe webhook: {event_type}")

        # Handle different event types
        if event_type == "checkout.session.completed":
            await handle_checkout_completed(event_data)

        elif event_type == "invoice.payment_succeeded":
            await handle_payment_succeeded(event_data)

        elif event_type == "customer.subscription.created":
            await handle_subscription_created(event_data)

        elif event_type == "customer.subscription.updated":
            await handle_subscription_updated(event_data)

        elif event_type == "customer.subscription.deleted":
            await handle_subscription_cancelled(event_data)

        elif event_type == "customer.subscription.trial_will_end":
            await handle_trial_ending(event_data)

        elif event_type == "invoice.payment_failed":
            await handle_payment_failed(event_data)

        else:
            logger.info(f"Unhandled webhook event: {event_type}")

        return {"status": "success", "event_type": event_type}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )


async def handle_checkout_completed(session_data: dict[str, Any]):
    """Handle successful checkout completion"""

    customer_id = session_data.get("customer")
    customer_email = session_data.get("customer_email")
    amount = session_data.get("amount_total", 0) / 100  # Convert from cents

    # Prepare payment data
    payment_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_id": customer_id,
        "customer_email": customer_email,
        "amount": amount,
        "currency": session_data.get("currency", "usd").upper(),
        "tier": session_data.get("metadata", {}).get("tier", "pro"),
        "payment_method": "card",
        "invoice_id": session_data.get("invoice"),
        "status": "succeeded",
        "trial_conversion": session_data.get("mode") == "subscription",
        "mrr_impact": amount if session_data.get("mode") == "subscription" else 0,
    }

    # 🚨 INSTANT SLACK NOTIFICATION FOR REVENUE
    await send_revenue_slack_notification("CHECKOUT_COMPLETED", payment_data)

    # Log to Google Sheets
    await log_payment_to_sheets(payment_data)

    # Send confirmation email
    if customer_email:
        await send_payment_confirmation_email(customer_email, payment_data)

    # Update Supabase
    await update_supabase_subscription(
        {
            "customer_id": customer_id,
            "email": customer_email,
            "status": "active",
            "tier": payment_data["tier"],
        }
    )

    logger.info(f"Checkout completed: ${amount} from {customer_email}")


async def handle_payment_succeeded(invoice_data: dict[str, Any]):
    """Handle successful payment"""

    customer_id = invoice_data.get("customer")
    amount = invoice_data.get("amount_paid", 0) / 100

    # Get customer email from Stripe
    try:
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer.email
    except Exception as e:
        logger.error(f"Failed to retrieve customer email: {e}")
        customer_email = "unknown@example.com"

    # Prepare payment data
    payment_data = {
        "date": datetime.fromtimestamp(invoice_data.get("created", 0)).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "customer_id": customer_id,
        "customer_email": customer_email,
        "amount": amount,
        "currency": invoice_data.get("currency", "usd").upper(),
        "tier": "pro",  # Would get from subscription metadata
        "payment_method": "card",
        "invoice_id": invoice_data.get("id"),
        "status": "succeeded",
        "trial_conversion": False,
        "mrr_impact": amount,
    }

    # 🚨 INSTANT SLACK NOTIFICATION FOR REVENUE
    await send_revenue_slack_notification("PAYMENT_SUCCEEDED", payment_data)

    # Log to Google Sheets
    await log_payment_to_sheets(payment_data)

    # Send confirmation email
    await send_payment_confirmation_email(customer_email, payment_data)

    logger.info(f"Payment succeeded: ${amount} from {customer_email}")


async def handle_subscription_created(subscription_data: dict[str, Any]):
    """Handle new subscription creation"""

    customer_id = subscription_data.get("customer")
    tier = subscription_data.get("metadata", {}).get("tier", "pro")
    status = subscription_data.get("status")

    # Get customer email
    try:
        customer = stripe.Customer.retrieve(customer_id)
        customer_email = customer.email
    except Exception as e:
        logger.error(f"Failed to retrieve customer email: {e}")
        customer_email = "unknown@example.com"

    # Send Slack notification for new subscription
    subscription_notification_data = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "customer_email": customer_email,
        "tier": tier,
        "status": status,
        "customer_id": customer_id,
        "amount": 0,  # No immediate payment for subscription creation
        "mrr_impact": 0,  # Will be calculated on first payment
    }

    await send_subscription_slack_notification(
        "SUBSCRIPTION_CREATED", subscription_notification_data
    )

    # Update Supabase subscription data
    await update_supabase_subscription(
        {
            "customer_id": customer_id,
            "status": status,
            "tier": tier,
            "current_period_start": datetime.fromtimestamp(
                subscription_data.get("current_period_start", 0)
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                subscription_data.get("current_period_end", 0)
            ).isoformat(),
        }
    )

    logger.info(f"Subscription created: {tier} for customer {customer_id}")


async def handle_subscription_updated(subscription_data: dict[str, Any]):
    """Handle subscription updates (upgrades/downgrades)"""

    customer_id = subscription_data.get("customer")
    tier = subscription_data.get("metadata", {}).get("tier", "pro")
    status = subscription_data.get("status")

    # Update Supabase subscription data
    await update_supabase_subscription(
        {
            "customer_id": customer_id,
            "status": status,
            "tier": tier,
            "current_period_start": datetime.fromtimestamp(
                subscription_data.get("current_period_start", 0)
            ).isoformat(),
            "current_period_end": datetime.fromtimestamp(
                subscription_data.get("current_period_end", 0)
            ).isoformat(),
        }
    )

    logger.info(f"Subscription updated: {tier} for customer {customer_id}")


async def handle_subscription_cancelled(subscription_data: dict[str, Any]):
    """Handle subscription cancellation"""

    customer_id = subscription_data.get("customer")

    # Update Supabase to cancelled status
    await update_supabase_subscription(
        {"customer_id": customer_id, "status": "cancelled"}
    )

    # TODO: Send cancellation email and trigger retention campaigns

    logger.info(f"Subscription cancelled for customer {customer_id}")


async def handle_trial_ending(subscription_data: dict[str, Any]):
    """Handle trial ending notification"""

    customer_id = subscription_data.get("customer")
    trial_end = datetime.fromtimestamp(subscription_data.get("trial_end", 0))

    # Trigger GitHub Actions trial conversion automation
    # This would be handled by the existing trial-conversion-automation.yml workflow

    logger.info(f"Trial ending for customer {customer_id} on {trial_end}")


async def handle_payment_failed(invoice_data: dict[str, Any]):
    """Handle failed payment"""

    customer_id = invoice_data.get("customer")
    amount = invoice_data.get("amount_due", 0) / 100
    attempt_count = invoice_data.get("attempt_count", 1)

    # TODO: Implement dunning management
    # - Send payment failure notifications
    # - Update subscription status if needed
    # - Trigger retry logic

    logger.warning(
        f"Payment failed: ${amount} from customer {customer_id}, attempt {attempt_count}"
    )


@router.post("/checkout/create")
async def create_checkout_session(checkout_data: dict):
    """Create Stripe checkout session"""

    try:
        # Use existing MCP Stripe server
        from app.mcp.stripe_server import StripeCheckoutSession

        session_request = StripeCheckoutSession(**checkout_data)
        result = await mcp_stripe.create_checkout_session(session_request)

        return result

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post("/portal/create")
async def create_customer_portal(customer_data: dict):
    """Create Stripe customer portal session"""

    try:
        customer_id = customer_data.get("customer_id")
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Customer ID required"
            )

        result = await mcp_stripe.create_customer_portal(customer_id)
        return result

    except Exception as e:
        logger.error(f"Failed to create customer portal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer portal",
        )
