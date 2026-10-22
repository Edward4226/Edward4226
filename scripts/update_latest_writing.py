from __future__ import annotations

import html
import re
import sys
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from xml.etree import ElementTree


FEED_URL = "https://edward4226.github.io/rss.xml"
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START_MARKER = "<!-- LATEST-WRITING:START -->"
END_MARKER = "<!-- LATEST-WRITING:END -->"
MAX_ITEMS = 3


def escape_markdown(value: str) -> str:
    return value.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def parse_date(value: str | None) -> str:
    if not value:
        return "undated"
    try:
        return parsedate_to_datetime(value).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return "undated"


def fetch_items() -> list[str]:
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "Edward4226-profile-readme/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = response.read()

    root = ElementTree.fromstring(payload)
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS channel not found")

    lines: list[str] = []
    for item in channel.findall("item")[:MAX_ITEMS]:
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        published = parse_date(item.findtext("pubDate"))
        if title and link:
            lines.append(f"- [{escape_markdown(title)}]({link}) · `{published}`")

    if not lines:
        raise RuntimeError("No publishable RSS items found")
    return lines


def update_readme(lines: list[str]) -> bool:
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"({re.escape(START_MARKER)})(.*?)({re.escape(END_MARKER)})",
        flags=re.DOTALL,
    )
    if not pattern.search(content):
        raise RuntimeError("README latest-writing markers not found")

    replacement = "\n".join([r"\1", *lines, r"\3"])
    updated = pattern.sub(replacement, content, count=1)
    if updated == content:
        return False

    README_PATH.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    try:
        changed = update_readme(fetch_items())
    except Exception as exc:
        print(f"update_latest_writing: {exc}", file=sys.stderr)
        return 1
    print("README updated" if changed else "README already current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
