from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element, ElementTree, SubElement, indent

SOURCE = "https://www.paulgraham.com/articles.html"
OUTPUT = Path(__file__).parent.parent / "feeds" / "paul-graham.xml"


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


request = Request(SOURCE, headers={"User-Agent": "Mozilla/5.0"})

with urlopen(request) as response:
    html = response.read().decode("utf-8", errors="replace")

parser = EssayParser()
parser.feed(html)

# The page contains introductory links to recommended essays before
# the chronological list. Keep each essay's final occurrence, which
# corresponds to its position in the main list.
last_occurrence = {}

for i, (title, url) in enumerate(parser.links):
    last_occurrence[url] = (i, title, url)

essays = [
    (title, url)
    for _, title, url in sorted(last_occurrence.values())
]

if not essays:
    raise RuntimeError("No essays found.")

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

indent(rss)

OUTPUT.parent.mkdir(exist_ok=True)

ElementTree(rss).write(
    OUTPUT,
    encoding="utf-8",
    xml_declaration=True,
)

print(f"Generated {OUTPUT} with {len(essays)} essays.")