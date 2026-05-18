import anthropic
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ── Configuration (set these as GitHub Secrets) ──────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
GMAIL_ADDRESS     = os.environ["GMAIL_ADDRESS"]      # your Gmail address
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"] # Gmail App Password (not your real password)
RECIPIENT_EMAIL   = os.environ["RECIPIENT_EMAIL"]    # where to send the briefing (can be same as above)
# ─────────────────────────────────────────────────────────────────────────────

def get_news_briefing() -> str:
    """Call Claude API with web search to pull today's top headlines."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""Today is {today}. Please search the web and pull the most important national news headlines right now.
Prioritize stories that appear across multiple outlets, especially Associated Press, Reuters, Fox News, and the Wall Street Journal.

For each major story:
- Give it a clear headline
- Write 2-3 sentences summarizing what's happening
- Note which outlets are covering it

Format the response as clean HTML suitable for an email, with:
- A header showing today's date
- Each story in its own clearly separated section with a bold headline
- Keep the total length digestible (5-7 top stories)

Do not include any markdown code fences — just plain HTML."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}]
    )

    # Extract the text response from content blocks
    result_text = ""
    for block in response.content:
        if block.type == "text":
            result_text += block.text

    return result_text


def send_email(html_body: str):
    """Send the briefing via Gmail SMTP."""
    today_str = datetime.now().strftime("%A, %B %d, %Y")
    subject = f"📰 Your Daily News Briefing — {today_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_ADDRESS
    msg["To"]      = RECIPIENT_EMAIL

    # Plain text fallback
    plain_text = "Your daily news briefing is attached. Please view in an HTML-capable email client."
    msg.attach(MIMEText(plain_text, "plain"))

    # Wrap the Claude output in a clean email shell
    full_html = f"""
    <html>
    <body style="font-family: Georgia, serif; max-width: 650px; margin: auto; padding: 20px; color: #222;">
        <div style="border-bottom: 3px solid #333; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="font-size: 22px; margin: 0;">📰 Daily News Briefing</h1>
            <p style="color: #666; margin: 4px 0 0 0;">{today_str} · Powered by Claude + Web Search</p>
        </div>
        {html_body}
        <div style="border-top: 1px solid #ccc; margin-top: 30px; padding-top: 10px; font-size: 12px; color: #999;">
            This briefing was generated automatically using the Claude API.
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(full_html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, RECIPIENT_EMAIL, msg.as_string())
        print(f"✅ Briefing sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    print("Fetching today's news briefing...")
    briefing_html = get_news_briefing()
    print("Sending email...")
    send_email(briefing_html)
    print("Done.")
