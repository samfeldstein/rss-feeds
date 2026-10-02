from datetime import datetime, timezone
from email.utils import format_datetime
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import urljoin
from urllib.request import Request, urlopen
from xml.etree.ElementTree import Element, SubElement, ElementTree, indent


BASE_URL = "https://darioamodei.com/"
OUTPUT = Path(__file__).resolve().parents[1] / "feeds" / "dario-amodei.xml"

MONTH_YEAR = re.compile(
    r"\b("
    r"January|February|March|April|May|June|"
    r"July|August|September|October|November|December"
    r")\s+(\d{4})\b"
)


def fetch(url):
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 RSS feed generator"},
    )

    with urlopen(request) as response:
        return response.read().decode("utf-8")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            title = " ".join("".join(self.text).split())

            if title:
                self.links.append((self.href, title))

            self.href = None
            self.text = []


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []

    def handle_data(self, data):
        self.text.append(data)


def get_articles():
    parser = LinkParser()
    parser.feed(fetch(BASE_URL))

    articles = []
    seen = set()

    for href, title in parser.links:
        url = urljoin(BASE_URL, href)

        if not (
            url.startswith(f"{BASE_URL}essay/")
            or url.startswith(f"{BASE_URL}post/")
        ):
            continue

        if url in seen:
            continue

        seen.add(url)

        article_parser = TextParser()
        article_parser.feed(fetch(url))

        text = " ".join(article_parser.text)
        match = MONTH_YEAR.search(text)

        published = None

        if match:
            published = datetime.strptime(
                match.group(0), "%B %Y"
            ).replace(tzinfo=timezone.utc)

        articles.append(
            {
                "title": title,
                "url": url,
                "published": published,
            }
        )

    articles.sort(
        key=lambda article: article["published"]
        or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    return articles


def build_feed(articles):
    rss = Element("rss", version="2.0")
    channel = SubElement(rss, "channel")

    SubElement(channel, "title").text = "Dario Amodei"
    SubElement(channel, "link").text = BASE_URL
    SubElement(channel, "description").text = (
        "Essays and short posts by Dario Amodei."
    )

    for article in articles:
        item = SubElement(channel, "item")

        SubElement(item, "title").text = article["title"]
        SubElement(item, "link").text = article["url"]

        guid = SubElement(item, "guid", isPermaLink="true")
        guid.text = article["url"]

        if article["published"]:
            SubElement(item, "pubDate").text = format_datetime(
                article["published"]
            )

    indent(rss)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(rss).write(
        OUTPUT,
        encoding="utf-8",
        xml_declaration=True,
    )


if __name__ == "__main__":
    build_feed(get_articles())
    print(f"Wrote {OUTPUT}")