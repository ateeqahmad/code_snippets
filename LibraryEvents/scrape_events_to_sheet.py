import requests
from bs4 import BeautifulSoup
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from collections import defaultdict

# URL for the monthly events calendar of the Colonie Town Library
# Update the query string if you need to fetch a different branch or month
LIBRARY_EVENTS_URL = (
    "https://uhls.librarycalendar.com/events/month?branches%5B81%5D=81"
)

# Path to your Google service account credentials JSON file
GOOGLE_CREDENTIALS_FILE = 'path/to/credentials.json'

# The name of the spreadsheet to create or update
SPREADSHEET_NAME = 'Library Events'


def fetch_events(url):
    """Fetch the events page and extract event data.

    The selectors in this function are based on the HTML structure used by the
    Library Market calendar platform. If the site changes, these selectors may
    need to be updated.
    """

    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    events = []
    for item in soup.select("div.event-item"):
        title_el = item.select_one(".event-title")
        date_el = item.select_one("time")
        cat_el = item.select_one(".event-category")

        if not title_el or not date_el:
            # Skip malformed entries
            continue

        title = title_el.get_text(strip=True)
        date = date_el.get_text(strip=True)
        category = cat_el.get_text(strip=True) if cat_el else "Uncategorized"

        events.append({"title": title, "date": date, "category": category})

    return events


def group_by_category(events):
    """Group events by their category name."""

    grouped = defaultdict(list)
    for event in events:
        grouped[event["category"]].append(event)
    return grouped


def write_to_google_sheet(grouped_events):
    """Upload grouped events to Google Sheets."""

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_CREDENTIALS_FILE, scope
    )
    client = gspread.authorize(creds)

    sheet = client.open(SPREADSHEET_NAME).sheet1
    sheet.clear()
    sheet.append_row(['Date', 'Title', 'Category'])

    for category, events in grouped_events.items():
        for event in events:
            sheet.append_row([event['date'], event['title'], category])


def main():
    """Fetch events, group them, and upload to Google Sheets."""

    events = fetch_events(LIBRARY_EVENTS_URL)
    grouped_events = group_by_category(events)
    write_to_google_sheet(grouped_events)


if __name__ == '__main__':
    main()
