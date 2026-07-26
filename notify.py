import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

DATA_FILE = "data/opportunities.json"
NEW_FILE = "data/new_items.json"


def send_sms(new_items):
    if not new_items:
        print("No new items — skipping SMS.")
        return

    from twilio.rest import Client
    client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    to_number = os.environ["TO_PHONE_NUMBER"]
    from_number = os.environ["TWILIO_PHONE_NUMBER"]

    icons = {"internship": "💼", "event": "📅", "course": "📚"}

    for item in new_items[:5]:
        icon = icons.get(item["type"], "🔔")
        body = (
            f"{icon} NEW {item['type'].upper()}\n"
            f"{item['title'][:80]}\n\n"
            f"Deadline: {item.get('deadline', 'See site')}\n"
            f"{item['url'][:100]}"
        )
        client.messages.create(body=body, from_=from_number, to=to_number)
        print(f"  SMS sent: {item['title'][:50]}")


def send_weekly_digest():
    try:
        with open(DATA_FILE) as f:
            data = json.load(f)
    except Exception:
        print("No data file — skipping digest.")
        return

    opps = data.get("opportunities", [])
    internships = [o for o in opps if o["type"] == "internship"]
    events = [o for o in opps if o["type"] == "event"]
    courses = [o for o in opps if o["type"] == "course"]

    html = build_email_html(internships, events, courses)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Design Opportunities — Week of {date.today().strftime('%B %d, %Y')}"
    msg["From"] = os.environ["GMAIL_ADDRESS"]
    msg["To"] = os.environ["TO_EMAIL"]
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["GMAIL_ADDRESS"], os.environ["GMAIL_APP_PASSWORD"])
        server.sendmail(os.environ["GMAIL_ADDRESS"], os.environ["TO_EMAIL"], msg.as_string())

    print(f"Weekly digest sent — {len(internships)} internships, {len(events)} events, {len(courses)} courses")


def build_email_html(internships, events, courses):
    dashboard_url = os.environ.get("DASHBOARD_URL", "#")

    def rows(items):
        out = ""
        for o in items[:15]:
            out += f"""
            <tr>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;">
                <a href="{o['url']}" style="font-weight:600;color:#1d1d1f;text-decoration:none;">{o['title']}</a><br>
                <span style="font-size:13px;color:#6e6e73;">{o['description'][:120]}...</span>
              </td>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;white-space:nowrap;font-size:13px;color:#444;">{o.get('deadline','—')}</td>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;font-size:12px;color:#555;">{o.get('requirements','—')[:80]}</td>
              <td style="padding:12px 16px;border-bottom:1px solid #eee;">
                <a href="{o['url']}" style="background:#0071e3;color:white;padding:6px 14px;border-radius:6px;text-decoration:none;font-size:12px;font-weight:500;">Apply →</a>
              </td>
            </tr>"""
        return out

    def section(title, items, color):
        if not items:
            return ""
        return f"""
        <h2 style="margin:32px 0 12px;color:{color};font-size:18px;">{title} <span style="font-weight:400;font-size:14px;color:#6e6e73;">({len(items)} found)</span></h2>
        <table style="width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;box-shadow:0 1px 4px rgba(0,0,0,0.08);">
          <thead style="background:{color};">
            <tr>
              <th style="padding:10px 16px;text-align:left;color:white;font-size:13px;">Opportunity</th>
              <th style="padding:10px 16px;text-align:left;color:white;font-size:13px;">Deadline</th>
              <th style="padding:10px 16px;text-align:left;color:white;font-size:13px;">Requirements</th>
              <th style="padding:10px 16px;text-align:left;color:white;font-size:13px;"></th>
            </tr>
          </thead>
          <tbody>{rows(items)}</tbody>
        </table>"""

    today = date.today().strftime("%B %d, %Y")
    total = len(internships) + len(events) + len(courses)

    return f"""
    <html><body style="margin:0;padding:0;background:#f5f5f7;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
      <div style="max-width:860px;margin:32px auto;padding:0 16px;">
        <div style="background:white;border-radius:16px;padding:40px;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
          <h1 style="margin:0 0 4px;font-size:28px;color:#1d1d1f;">Design Opportunities</h1>
          <p style="margin:0 0 8px;color:#6e6e73;">Week of {today} · {total} total opportunities tracked</p>
          <a href="{dashboard_url}" style="display:inline-block;background:#0071e3;color:white;padding:8px 18px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:500;">View Full Dashboard →</a>
          {section("💼 Internships", internships, "#0071e3")}
          {section("📅 Events", events, "#7c3aed")}
          {section("📚 Courses & Certificates", courses, "#059669")}
          <p style="margin-top:40px;color:#999;font-size:12px;text-align:center;">Searches run daily · Sourced from LinkedIn, Handshake, company sites, Google, and more</p>
        </div>
      </div>
    </body></html>"""


if __name__ == "__main__":
    # SMS for new items
    try:
        with open(NEW_FILE) as f:
            new_items = json.load(f)
        send_sms(new_items)
    except Exception as e:
        print(f"SMS step: {e}")

    # Weekly digest on Sundays
    if date.today().weekday() == 6:
        send_weekly_digest()
    else:
        print(f"Not Sunday — skipping digest (today is weekday {date.today().weekday()})")
