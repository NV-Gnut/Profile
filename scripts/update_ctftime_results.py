from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


TEAM_ID = 410831
YEARS = ("2026", "2025")
MAX_PLACE = 150
ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "data" / "ctftime-results.json"
TEAM_URL = f"https://ctftime.org/team/{TEAM_ID}"


def fetch_team_page() -> str:
    request = Request(
        TEAM_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; Lighth0useProfileBot/1.0)",
        },
    )

    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_place(value: str) -> int | None:
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


def parse_results(html: str) -> dict[str, list[dict[str, str | int]]]:
    soup = BeautifulSoup(html, "html.parser")
    results: dict[str, list[dict[str, str | int]]] = {year: [] for year in YEARS}
    current_year: str | None = None

    for node in soup.find_all(["h2", "h3", "h4", "table"]):
        text = node.get_text(" ", strip=True)

        if node.name in {"h2", "h3", "h4"}:
            matched_year = next((year for year in YEARS if year in text), None)
            if matched_year:
                current_year = matched_year
            continue

        if node.name != "table" or current_year not in YEARS:
            continue

        for row in node.find_all("tr"):
            cells = row.find_all(["td", "th"])
            values = [cell.get_text(" ", strip=True) for cell in cells]

            if len(values) < 4 or values[0].lower() == "place":
                continue

            place = parse_place(values[0])
            if place is None or place > MAX_PLACE:
                continue

            event_link = cells[1].find("a", href=True)
            event_url = ""
            if event_link:
                href = event_link["href"]
                event_url = href if href.startswith("http") else f"https://ctftime.org{href}"

            results[current_year].append(
                {
                    "place": place,
                    "event": values[1],
                    "ctfPoints": values[2],
                    "ratingPoints": values[3],
                    "url": event_url,
                },
            )

    for year in YEARS:
        results[year].sort(key=lambda item: int(item["place"]))

    return results


def parse_rankings(html: str) -> dict[str, int | None]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rankings: dict[str, int | None] = {"world": None, "vietnam": None}

    for index, line in enumerate(lines):
        lower = line.lower()
        nearby = " ".join(lines[index : index + 3])

        if rankings["world"] is None and "world" in lower and "place" in lower:
            rankings["world"] = parse_place(nearby)

        if rankings["vietnam"] is None and (
            "vietnam" in lower or "viet nam" in lower or "country" in lower
        ):
            rankings["vietnam"] = parse_place(nearby)

    return rankings


def main() -> None:
    html = fetch_team_page()
    data = {
        "teamId": TEAM_ID,
        "teamUrl": TEAM_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "rankings": parse_rankings(html),
        "years": parse_results(html),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
