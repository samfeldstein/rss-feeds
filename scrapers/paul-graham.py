import re
import time
from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent, parse

SOURCE = "https://www.paulgraham.com/articles.html"
OUTPUT = Path(__file__).parent.parent / "feeds" / "paul-graham.xml"

HEADERS = {"User-Agent": "Mozilla/5.0"}

MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}


class EssayParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a" and self.href is None:
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            title = "".join(self.text).strip()
            url = urljoin(SOURCE, self.href)
            parsed = urlparse(url)

            if (
                title
                and parsed.hostname in ("paulgraham.com", "www.paulgraham.com")
                and parsed.path.endswith(".html")
                and parsed.path not in ("/index.html", "/articles.html")
            ):
                self.links.append((title, url))

            self.href = None
            self.text = []


def fetch(url):
    request = Request(url, headers=HEADERS)

    with urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def load_cached_dates():
    dates = {}

    if not OUTPUT.exists():
        return dates

    try:
        root = parse(OUTPUT).getroot()

        for item in root.findall("./channel/item"):
            guid = item.findtext("guid")
            pub_date = item.findtext("pubDate")

            if guid and pub_date:
                dates[guid] = pub_date

    except Exception:
        pass

    return dates


def extract_date(html):
    # Strip tags so we're searching visible page text.
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text)

    # Paul Graham generally dates essays as "September 2026".
    pattern = (
        r"\b("
        + "|".join(MONTHS)
        + r")\s+(19|20)\d{2}\b"
    )

    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    month_name = match.group(1).lower()
    year = int(match.group(0).split()[-1])

    # PG usually supplies only month/year. Use the first of the month.
    date = datetime(
        year,
        MONTHS[month_name],
        1,
        tzinfo=timezone.utc,
    )

    return format_datetime(date)


html = fetch(SOURCE)

parser = EssayParser()
parser.feed(html)

# Keep the final occurrence of each URL. This removes introductory
# links while preserving the chronological essay-list position.
last_occurrence = {}

for i, (title, url) in enumerate(parser.links):
    last_occurrence[url] = (i, title, url)

essays = [
    (title, url)
    for _, title, url in sorted(last_occurrence.values())
]

if not essays:
    raise RuntimeError("No essays found.")

cached_dates = load_cached_dates()
dates = {}

for title, url in essays:
    if url in cached_dates:
        dates[url] = cached_dates[url]
        continue

    print(f"Fetching date: {title}")

    try:
        essay_html = fetch(url)
        pub_date = extract_date(essay_html)

        if pub_date:
            dates[url] = pub_date
        else:
            print(f"  Warning: no date found for {url}")

    except Exception as error:
        print(f"  Warning: {error}")

    # Be polite to the server during the initial import.
    time.sleep(0.1)


rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "Paul Graham Essays"
SubElement(channel, "link").text = SOURCE
SubElement(channel, "description").text = "Essays by Paul Graham"

for title, url in essays:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid", isPermaLink="true").text = url

    if url in dates:
        SubElement(item, "pubDate").text = dates[url]

indent(rss)

OUTPUT.parent.mkdir(exist_ok=True)

ElementTree(rss).write(
    OUTPUT,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    f"Generated {OUTPUT} with {len(essays)} essays "
    f"and {len(dates)} publication dates."
)