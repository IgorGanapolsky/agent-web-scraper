import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_daily_digest_email(
    query: str, top_3: list[dict], leads: int, replies: int, revenue: float
):
    today = datetime.now().strftime("%B %d, %Y")

    # Generate the HTML body
    html = f"""
    <h2>📬 Daily AI Digest — {today}</h2>
    <p><strong>Query Used:</strong> {query}</p>
    <h3>🔥 Top 3 Pain Points</h3>
    <ol>
    """
    for insight in top_3:
        html += f"""
        <li>
            <strong>{insight['pain_point_label']}</strong><br/>
            <em>{insight['explanation']}</em><br/>
            <a href="{insight['gsheet_link']}">🔗 View in Google Sheet</a>
        </li>
        """

    html += f"""
    </ol>
    <hr/>
    <h3>📊 Metrics Summary</h3>
    <ul>
        <li><strong>Leads:</strong> {leads}</li>
        <li><strong>Replies:</strong> {replies}</li>
        <li><strong>Revenue:</strong> ${revenue:.2f}</li>
    </ul>
    <p><a href="https://docs.google.com/spreadsheets/d/1KJYQCX-cJsEkUPh7GKwigI71CODun504VOdC4NfNLfY/edit">📈 Open Metrics Sheet</a></p>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📈 Daily SaaS Insights — {today}"
    msg["From"] = "support@saasgrowthdispatch.com"
    msg["To"] = "support@saasgrowthdispatch.com"

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.zoho.com", 465) as server:
        server.login("support@saasgrowthdispatch.com", os.getenv("ZOHO_APP_PASSWORD"))
        server.sendmail(msg["From"], msg["To"], msg.as_string())
        print("✅ Email digest sent.")
