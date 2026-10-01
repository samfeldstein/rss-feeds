from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent, parse

OUTPUT = Path(__file__).parent.parent / "feeds" / "gwern-newsletter.xml"
BASE = "https://gwern.net/newsletter"
HEADERS = {"User-Agent": "Mozilla/5.0"}

START_YEAR = 2013
START_MONTH = 8


def exists(url):
    request = Request(url, headers=HEADERS)

    try:
        with urlopen(request) as response:
            return response.status == 200
    except HTTPError as error:
        if error.code == 404:
            return False
        raise


def load_existing():
    newsletters = {}

    if not OUTPUT.exists():
        return newsletters

    try:
        root = parse(OUTPUT).getroot()

        for item in root.findall("./channel/item"):
            url = item.findtext("guid")
            title = item.findtext("title")
            pub_date = item.findtext("pubDate")

            if not url or not title or not pub_date:
                continue

            date = datetime.strptime(
                pub_date,
                "%a, %d %b %Y %H:%M:%S %z",
            )

            newsletters[url] = (date, title, url)

    except Exception as error:
        print(f"Warning: could not read existing feed: {error}")

    return newsletters


newsletters = load_existing()

if newsletters:
    newest_date = max(item[0] for item in newsletters.values())

    year = newest_date.year
    month = newest_date.month + 1

    if month == 13:
        month = 1
        year += 1
else:
    year = START_YEAR
    month = START_MONTH


now = datetime.now(timezone.utc)

while (year, month) <= (now.year, now.month):
    url = f"{BASE}/{year}/{month:02d}"

    print(f"Checking {url}")

    if exists(url):
        date = datetime(year, month, 1, tzinfo=timezone.utc)

        newsletters[url] = (
            date,
            date.strftime("%B %Y News"),
            url,
        )

    month += 1

    if month == 13:
        month = 1
        year += 1


items = sorted(
    newsletters.values(),
    key=lambda item: item[0],
    reverse=True,
)

if not items:
    raise RuntimeError("No newsletters found.")


rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "Gwern Newsletter"
SubElement(channel, "link").text = BASE
SubElement(channel, "description").text = "Monthly newsletters from Gwern.net"

for date, title, url in items:
    item = SubElement(channel, "item")

    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid", isPermaLink="true").text = url
    SubElement(item, "pubDate").text = format_datetime(date)


indent(rss)

OUTPUT.parent.mkdir(exist_ok=True)

ElementTree(rss).write(
    OUTPUT,
    encoding="utf-8",
    xml_declaration=True,
)

print(
    f"Generated {OUTPUT} with "
    f"{len(items)} newsletters."
)