# ucdenver_events_poll.py
# Runs forever: fetches UC Denver CampusLabs RSS every 8 hours and overwrites CSV.

import time
import feedparser
from bs4 import BeautifulSoup
import pandas as pd
import requests
import re
from datetime import datetime

FEED_URL = "https://ucdenver.campuslabs.com/engage/events.rss"
CSV_PATH = "ucdenver_events.csv"
INTERVAL_SECONDS = 8 * 60 * 60  # 8 hours

HEADERS = {"User-Agent": "ucd-rss-bot/1.0 (+python)"}

MONTHS = {
    "January": "01", "February": "02", "March": "03", "April": "04",
    "May": "05", "June": "06", "July": "07", "August": "08",
    "September": "09", "October": "10", "November": "11", "December": "12"
}

def fetch_bytes(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.content

def extract_date_from_text(text):
    """
    Try to extract a date like 'Tuesday, October 27, 2025' or 'October 27, 2025'
    and convert to ISO format YYYY-MM-DD.
    """
    match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(\d{4})", text)
    if not match:
        return ""
    month_name, day, year = match.groups()
    month_num = MONTHS.get(month_name, "00")
    try:
        return f"{year}-{month_num}-{int(day):02d}"
    except ValueError:
        return ""

def scrape_once():
    content = fetch_bytes(FEED_URL)
    feed = feedparser.parse(content)
    events = []

    for entry in feed.entries:
        title = entry.title
        link = entry.link
        summary_html = entry.summary

        soup = BeautifulSoup(summary_html, "html.parser")

        # Clean description
        description = soup.find(class_="p-description")
        description_text = description.get_text(" ", strip=True) if description else ""

        # Times (prefer visible text)
        start_tag = soup.find("time", class_="dt-start") or soup.find("time", class_="dtstart")
        end_tag = soup.find("time", class_="dt-end") or soup.find("time", class_="dtend")
        loc_tag = soup.find(class_="p-location") or soup.find(class_="location")

        start_text = start_tag.get_text(" ", strip=True) if start_tag else ""
        end_text = (end_tag.get_text(" ", strip=True) if end_tag else "")
        location = loc_tag.get_text(" ", strip=True) if loc_tag else ""

        # Extract date
        date_str = extract_date_from_text(start_text)
        date_str = date_str.split("-")[1]+date_str.split("-")[2]

        events.append({
            "Title": title,
            "Link": link,
            "Date": date_str,
            "Start": start_text,
            "End": end_text,
            "Location": location,
            "Summary": description_text,
        })

    df = pd.DataFrame(events)
    df.to_csv(CSV_PATH, index=False, encoding="utf-8")  # overwrite each run
    return len(df)

def main():
    while True:
        try:
            n = scrape_once()
            print(f"[OK] Saved {n} events to {CSV_PATH}")
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    main()
