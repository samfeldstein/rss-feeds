import re
from pathlib import Path
from xml.etree.ElementTree import parse

ROOT = Path(__file__).parent.parent
FEEDS = ROOT / "feeds"
README = ROOT / "README.md"
INDEX = ROOT / "index.html"

SITE = "https://samfeldstein.github.io/rss-feeds"

START = "<!-- feeds:start -->"
END = "<!-- feeds:end -->"


def get_title(feed):
    try:
        root = parse(feed).getroot()
        return root.findtext("./channel/title") or feed.stem
    except Exception:
        return feed.stem


def replace_feed_list(text, lines):
    generated = START + "\n" + "\n".join(lines) + "\n" + END

    pattern = rf"{re.escape(START)}.*?{re.escape(END)}"

    if not re.search(pattern, text, flags=re.DOTALL):
        raise RuntimeError("Feed markers not found.")

    return re.sub(
        pattern,
        generated,
        text,
        flags=re.DOTALL,
    )


feeds = sorted(
    FEEDS.glob("*.xml"),
    key=lambda feed: get_title(feed).lower(),
)


# README

readme_lines = [
    f"- [{get_title(feed)}]({SITE}/feeds/{feed.name})"
    for feed in feeds
]

README.write_text(
    replace_feed_list(
        README.read_text(),
        readme_lines,
    )
)


# Homepage

index_lines = [
    f'<li><a href="{SITE}/feeds/{feed.name}">{get_title(feed)}</a></li>'
    for feed in feeds
]

INDEX.write_text(
    replace_feed_list(
        INDEX.read_text(),
        index_lines,
    )
)


print(
    f"Updated README and homepage with {len(feeds)} feeds."
)