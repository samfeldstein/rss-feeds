import re
from pathlib import Path
from xml.etree.ElementTree import parse

ROOT = Path(__file__).parent.parent
FEEDS = ROOT / "feeds"
README = ROOT / "README.md"

START = "<!-- feeds:start -->"
END = "<!-- feeds:end -->"


def get_title(feed):
    try:
        root = parse(feed).getroot()
        return root.findtext("./channel/title") or feed.stem
    except Exception:
        return feed.stem


feeds = sorted(
    FEEDS.glob("*.xml"),
    key=lambda feed: get_title(feed).lower(),
)

lines = [
    f"- [{get_title(feed)}](feeds/{feed.name})"
    for feed in feeds
]

generated = f"{START}\n" + "\n".join(lines) + f"\n{END}"

text = README.read_text()

pattern = rf"{re.escape(START)}.*?{re.escape(END)}"

if re.search(pattern, text, flags=re.DOTALL):
    text = re.sub(pattern, generated, text, flags=re.DOTALL)
else:
    text = text.rstrip() + "\n\n## Feeds\n\n" + generated + "\n"

README.write_text(text)

print(f"Updated README with {len(feeds)} feeds.")