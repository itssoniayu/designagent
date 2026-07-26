import os
import json
import hashlib
import re
from datetime import datetime
from tavily import TavilyClient

SEARCHES = [
    # Big tech internships
    ("Apple hardware product design internship summer 2027 apply", "internship"),
    ("Google industrial design internship 2027 application open", "internship"),
    ("Microsoft design internship 2027 undergraduate", "internship"),
    ("Meta product design internship 2027 apply now", "internship"),
    ("Amazon design internship summer 2027", "internship"),
    ("Samsung design internship 2027", "internship"),
    ("Dyson design internship 2027", "internship"),
    # AI design
    ("AI design UX internship summer 2027 tech company apply", "internship"),
    ("artificial intelligence product design internship 2027", "internship"),
    # Remote / school year
    ("remote product design internship fall 2026 undergraduate apply", "internship"),
    ("remote branding design internship 2026 part time student", "internship"),
    # Events near Cornell
    ("design events Ithaca New York 2026", "event"),
    ("product design conference New York 2026 student", "event"),
    ("IDSA industrial design events 2026", "event"),
    ("design week New York 2026", "event"),
    # Courses
    ("material science online certificate course 2026 design", "course"),
    ("AI design certificate online course 2026", "course"),
    ("product design Coursera certificate 2026", "course"),
    ("industrial design online learning certificate", "course"),
]

DATA_FILE = "data/opportunities.json"
NEW_FILE = "data/new_items.json"


def load_data():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except Exception:
        return {"opportunities": [], "last_updated": None}


def save_data(data):
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def make_id(url, title):
    return hashlib.md5(f"{url}{title}".encode()).hexdigest()[:12]


def extract_deadline(content):
    patterns = [
        r"deadline[:\s]+([A-Za-z]+ \d{1,2},?\s*\d{4})",
        r"apply by[:\s]+([A-Za-z]+ \d{1,2},?\s*\d{4})",
        r"due[:\s]+([A-Za-z]+ \d{1,2},?\s*\d{4})",
        r"closes[:\s]+([A-Za-z]+ \d{1,2},?\s*\d{4})",
        r"applications?\s+(?:close|due|open)[:\s]+([A-Za-z]+ \d{1,2},?\s*\d{4})",
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return "Check website"


def extract_requirements(content):
    keywords = ["degree", "GPA", "portfolio", "major", "coursework", "skills", "experience", "undergraduate", "junior", "senior"]
    sentences = [s.strip() for s in re.split(r"[.!?]", content) if s.strip()]
    reqs = [s for s in sentences if any(kw.lower() in s.lower() for kw in keywords)]
    return ". ".join(reqs[:2]) + "." if reqs else "See listing for details."


def run_search():
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    data = load_data()
    existing_ids = {opp["id"] for opp in data["opportunities"]}
    new_items = []

    for query, category in SEARCHES:
        try:
            results = client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
            )
            for result in results.get("results", []):
                title = result.get("title", "").strip()
                url = result.get("url", "").strip()
                content = result.get("content", "")

                if not title or not url:
                    continue

                item_id = make_id(url, title)
                if item_id in existing_ids:
                    continue

                opp = {
                    "id": item_id,
                    "title": title,
                    "url": url,
                    "description": content[:400].strip(),
                    "type": category,
                    "deadline": extract_deadline(content),
                    "requirements": extract_requirements(content),
                    "found_date": datetime.now().strftime("%Y-%m-%d"),
                    "notified": False,
                }

                data["opportunities"].append(opp)
                existing_ids.add(item_id)
                new_items.append(opp)
                print(f"  NEW [{category}]: {title[:60]}")

        except Exception as e:
            print(f"  Error on '{query}': {e}")

    data["last_updated"] = datetime.now().isoformat()
    save_data(data)

    os.makedirs("data", exist_ok=True)
    with open(NEW_FILE, "w") as f:
        json.dump(new_items, f, indent=2, default=str)

    print(f"\nDone. {len(new_items)} new opportunities found.")
    return new_items


if __name__ == "__main__":
    run_search()
