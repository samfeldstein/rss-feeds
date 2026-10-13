# RSS Feeds

RSS feeds for sites that don't publish one, or whose feeds aren't usable. Small Python scrapers build the feeds, GitHub Actions keeps them current, and GitHub Pages hosts them at [samfeldstein.github.io/rss-feeds](https://samfeldstein.github.io/rss-feeds/).

## Feeds

To subscribe, copy a feed's URL into your RSS reader.

<!-- feeds:start -->
- [Dario Amodei](https://samfeldstein.github.io/rss-feeds/feeds/dario-amodei.xml)
- [Gwern Newsletter](https://samfeldstein.github.io/rss-feeds/feeds/gwern-newsletter.xml)
- [Paul Graham Essays](https://samfeldstein.github.io/rss-feeds/feeds/paul-graham.xml)
<!-- feeds:end -->

| Feed | Source | What's in it |
| --- | --- | --- |
| Dario Amodei | [darioamodei.com](https://darioamodei.com/) | Essays and posts linked from the homepage |
| Gwern Newsletter | [gwern.net/newsletter](https://gwern.net/newsletter) | Every monthly newsletter since August 2013 |
| Paul Graham Essays | [paulgraham.com/articles.html](https://www.paulgraham.com/articles.html) | Every essay on the articles page |

### About the dates

For sites that don't give an exact publication date, each item is dated the first of the month it was published. Your reader will sort items in the right order, but the day it shows may be wrong.

The feeds update once a week, so a new post can take up to a week to show up in your reader.

## How it works

```
scrapers/*.py ──► feeds/*.xml ──► scripts/update-site.py ──► README.md + index.html
```

1. **Scrapers.** Each file in `scrapers/` fetches one site, finds its articles, and writes an RSS 2.0 feed to `feeds/`.
   - **Dario Amodei:** collects the `/essay/` and `/post/` links on the homepage, then opens each one to find its date.
   - **Gwern Newsletter:** the newsletters live at predictable URLs (`/newsletter/YYYY/MM`), so the scraper checks each month after the newest one already in the feed.
   - **Paul Graham:** reads the essay list from the articles page and opens each new essay to find its date. Dates already in the feed are reused, so only new essays are fetched.
2. **Site update.** `scripts/update-site.py` reads every feed's title and rewrites the feed list in this README and in `index.html`. The list sits between a pair of `feeds:start` and `feeds:end` HTML comments.
3. **Automation.** The [Update RSS feeds](.github/workflows/update-feeds.yml) workflow runs every Monday at 12:00 UTC, on pushes to `main` that change `scrapers/`, and on manual dispatch. It runs every scraper and the site update, then commits any changes.

## Running locally

The code uses only the Python standard library, so there's nothing to install. The workflow uses Python 3.13.

Build one feed:

```bash
python scrapers/paul-graham.py
```

Build every feed and refresh the feed list:

```bash
for scraper in scrapers/*.py; do python "$scraper"; done && python scripts/update-site.py
```

## Adding a feed

1. Add a scraper to `scrapers/` that writes `feeds/<name>.xml`. The existing scrapers are good templates.
2. Push to `main`. The workflow builds the feed and adds it to the list.

The feed list is generated, so don't edit it by hand. Keep the markers in place, or `update-site.py` will fail.

## Note

This is a personal project. The feeds are public and you're welcome to subscribe, but I'm not taking requests for new feeds. I'm not affiliated with any of the authors; all content belongs to them, and the feeds only link to it.
