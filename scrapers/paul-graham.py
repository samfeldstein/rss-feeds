from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import urlopen
from xml.etree.ElementTree import Element, ElementTree, SubElement

SOURCE = "https://www.paulgraham.com/articles.html"
OUTPUT = Path(__file__).parent.parent / "feeds" / "paul-graham.xml"


class EssayParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            title = "".join(self.text).strip()

            if title and self.href.endswith(".html"):
                self.links.append((title, urljoin(SOURCE, self.href)))

            self.href = None
            self.text = []


with urlopen(SOURCE) as response:
    html = response.read().decode("utf-8")

parser = EssayParser()
parser.feed(html)

rss = Element("rss", version="2.0")
channel = SubElement(rss, "channel")

SubElement(channel, "title").text = "Paul Graham Essays"
SubElement(channel, "link").text = SOURCE
SubElement(channel, "description").text = "Essays by Paul Graham"
SubElement(channel, "lastBuildDate").text = datetime.now(timezone.utc).strftime(
    "%a, %d %b %Y %H:%M:%S +0000"
)

for title, url in parser.links:
    item = SubElement(channel, "item")
    SubElement(item, "title").text = title
    SubElement(item, "link").text = url
    SubElement(item, "guid").text = url

OUTPUT.parent.mkdir(exist_ok=True)
ElementTree(rss).write(OUTPUT, encoding="utf-8", xml_declaration=True)
