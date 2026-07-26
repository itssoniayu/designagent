import json
import os
from datetime import datetime

DATA_FILE = "data/opportunities.json"
OUT_FILE = "docs/index.html"


def load_data():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {"opportunities": [], "last_updated": None}


def build():
    data = load_data()
    opps = data.get("opportunities", [])
    last_updated = data.get("last_updated", "")
    if last_updated:
        try:
            last_updated = datetime.fromisoformat(last_updated).strftime("%B %d, %Y at %I:%M %p UTC")
        except Exception:
            pass

    internships = [o for o in opps if o["type"] == "internship"]
    events = [o for o in opps if o["type"] == "event"]
    courses = [o for o in opps if o["type"] == "course"]

    def card(o):
        type_colors = {
            "internship": ("#e8f0fe", "#1a73e8", "💼"),
            "event": ("#f3e8ff", "#7c3aed", "📅"),
            "course": ("#e6f4ea", "#137333", "📚"),
        }
        bg, color, icon = type_colors.get(o["type"], ("#f5f5f5", "#333", "🔔"))
        return f"""
        <div class="card" data-type="{o['type']}">
          <div class="card-header" style="background:{bg};">
            <span class="tag" style="background:{color};">{icon} {o['type'].upper()}</span>
            <span class="date">Found {o.get('found_date','')}</span>
          </div>
          <div class="card-body">
            <h3><a href="{o['url']}" target="_blank">{o['title']}</a></h3>
            <p class="desc">{o.get('description','')[:200]}...</p>
            <div class="meta">
              <div class="meta-item">
                <span class="meta-label">Deadline</span>
                <span class="meta-value deadline">{o.get('deadline','Check website')}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">Requirements</span>
                <span class="meta-value">{o.get('requirements','See listing.')[:120]}</span>
              </div>
            </div>
          </div>
          <div class="card-footer">
            <a href="{o['url']}" target="_blank" class="apply-btn" style="background:{color};">Apply / View →</a>
          </div>
        </div>"""

    all_cards = "".join(card(o) for o in sorted(opps, key=lambda x: x.get("found_date",""), reverse=True))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sonia's Design Opportunities</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f7; color: #1d1d1f; }}

  header {{ background: white; padding: 24px 32px; border-bottom: 1px solid #e5e5e5; position: sticky; top: 0; z-index: 10; }}
  .header-top {{ display: flex; align-items: baseline; gap: 16px; margin-bottom: 16px; }}
  h1 {{ font-size: 24px; font-weight: 700; }}
  .subtitle {{ color: #6e6e73; font-size: 14px; }}
  .stats {{ display: flex; gap: 24px; flex-wrap: wrap; }}
  .stat {{ display: flex; align-items: center; gap: 8px; }}
  .stat-num {{ font-size: 22px; font-weight: 700; }}
  .stat-label {{ font-size: 13px; color: #6e6e73; }}

  .filters {{ display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }}
  .filter-btn {{ padding: 6px 16px; border-radius: 20px; border: 1px solid #d2d2d7; background: white; cursor: pointer; font-size: 13px; transition: all 0.15s; }}
  .filter-btn:hover, .filter-btn.active {{ background: #1d1d1f; color: white; border-color: #1d1d1f; }}

  main {{ max-width: 1100px; margin: 32px auto; padding: 0 24px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }}

  .card {{ background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); transition: box-shadow 0.2s; }}
  .card:hover {{ box-shadow: 0 4px 16px rgba(0,0,0,0.12); }}
  .card.hidden {{ display: none; }}

  .card-header {{ padding: 12px 16px; display: flex; justify-content: space-between; align-items: center; }}
  .tag {{ font-size: 11px; font-weight: 600; color: white; padding: 3px 10px; border-radius: 20px; letter-spacing: 0.5px; }}
  .date {{ font-size: 12px; color: #6e6e73; }}

  .card-body {{ padding: 16px; }}
  .card-body h3 {{ font-size: 15px; font-weight: 600; margin-bottom: 8px; line-height: 1.4; }}
  .card-body h3 a {{ color: #1d1d1f; text-decoration: none; }}
  .card-body h3 a:hover {{ color: #0071e3; }}
  .desc {{ font-size: 13px; color: #6e6e73; line-height: 1.5; margin-bottom: 14px; }}

  .meta {{ display: flex; flex-direction: column; gap: 8px; }}
  .meta-item {{ display: flex; flex-direction: column; gap: 2px; }}
  .meta-label {{ font-size: 11px; font-weight: 600; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }}
  .meta-value {{ font-size: 13px; color: #444; }}
  .deadline {{ font-weight: 600; color: #d93025; }}

  .card-footer {{ padding: 12px 16px; border-top: 1px solid #f0f0f0; }}
  .apply-btn {{ display: inline-block; color: white; padding: 8px 18px; border-radius: 8px; text-decoration: none; font-size: 13px; font-weight: 500; }}

  .empty {{ text-align: center; padding: 64px; color: #6e6e73; grid-column: 1/-1; }}
  footer {{ text-align: center; padding: 32px; color: #999; font-size: 13px; }}
</style>
</head>
<body>

<header>
  <div class="header-top">
    <h1>Design Opportunities</h1>
    <span class="subtitle">Last updated: {last_updated}</span>
  </div>
  <div class="stats">
    <div class="stat"><span class="stat-num" style="color:#1a73e8;">{len(internships)}</span><span class="stat-label">Internships</span></div>
    <div class="stat"><span class="stat-num" style="color:#7c3aed;">{len(events)}</span><span class="stat-label">Events</span></div>
    <div class="stat"><span class="stat-num" style="color:#137333;">{len(courses)}</span><span class="stat-label">Courses</span></div>
  </div>
  <div class="filters">
    <button class="filter-btn active" onclick="filter('all')">All ({len(opps)})</button>
    <button class="filter-btn" onclick="filter('internship')">💼 Internships ({len(internships)})</button>
    <button class="filter-btn" onclick="filter('event')">📅 Events ({len(events)})</button>
    <button class="filter-btn" onclick="filter('course')">📚 Courses ({len(courses)})</button>
  </div>
</header>

<main>
  <div class="grid" id="grid">
    {all_cards if all_cards else '<div class="empty"><h3>No opportunities yet</h3><p>Run the search agent to populate this dashboard.</p></div>'}
  </div>
</main>

<footer>Searches run daily across LinkedIn, Handshake, company career sites, Google, and more · Built for Sonia Yu</footer>

<script>
  function filter(type) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    event.target.classList.add('active');
    document.querySelectorAll('.card').forEach(card => {{
      if (type === 'all' || card.dataset.type === type) {{
        card.classList.remove('hidden');
      }} else {{
        card.classList.add('hidden');
      }}
    }});
  }}
</script>
</body>
</html>"""

    os.makedirs("docs", exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard built → {OUT_FILE} ({len(opps)} opportunities)")


if __name__ == "__main__":
    build()
