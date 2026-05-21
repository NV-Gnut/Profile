from __future__ import annotations

import json
import re
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


def parse_first_int(value: str) -> int | None:
    match = re.search(r"\d+", value)
    return int(match.group(0)) if match else None


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def find_year(value: str) -> str | None:
    return next((year for year in YEARS if re.search(rf"\b{year}\b", value)), None)


def is_year_marker(value: str) -> bool:
    text = clean_text(value)
    if not text or len(text) > 80:
        return False

    return find_year(text) is not None


def table_header_map(table) -> dict[str, int]:
    headers = [clean_text(cell.get_text(" ", strip=True)).lower() for cell in table.find_all("th")]

    if not headers:
        first_row = table.find("tr")
        if first_row:
            headers = [
                clean_text(cell.get_text(" ", strip=True)).lower()
                for cell in first_row.find_all(["th", "td"])
            ]

    indexes: dict[str, int] = {}
    for index, header in enumerate(headers):
        if "place" in header and "place" not in indexes:
            indexes["place"] = index
        elif "event" in header and "event" not in indexes:
            indexes["event"] = index
        elif "rating" in header and "rating" not in indexes:
            indexes["rating"] = index
        elif "ctf" in header and ("point" in header or "pts" in header) and "ctf" not in indexes:
            indexes["ctf"] = index

    return indexes


def is_result_table(table) -> bool:
    headers = table_header_map(table)
    if {"place", "event"}.issubset(headers):
        return True

    first_rows = table.find_all("tr", limit=4)
    text = clean_text(" ".join(row.get_text(" ", strip=True) for row in first_rows)).lower()
    return "place" in text and "event" in text and ("rating" in text or "ctf" in text)


def infer_table_year(table) -> str | None:
    text = clean_text(table.get_text(" ", strip=True))
    counts = {
        year: len(re.findall(rf"\b{year}\b", text))
        for year in YEARS
    }
    year, count = max(counts.items(), key=lambda item: item[1])
    return year if count > 0 else None


def row_cells(row) -> list:
    return row.find_all(["td", "th"])


def parse_result_row(row, headers: dict[str, int]) -> dict[str, str | int] | None:
    cells = row_cells(row)
    texts = [clean_text(cell.get_text(" ", strip=True)) for cell in cells]

    if not cells or all(not text for text in texts):
        return None

    if "place" in headers and "event" in headers:
        header_offset = 0
        if headers["place"] < len(texts) and not texts[headers["place"]]:
            header_offset = 1

        place_index = headers["place"] + header_offset
        event_index = headers["event"] + header_offset

        if place_index >= len(cells) or event_index >= len(cells):
            return None

        place = parse_first_int(texts[place_index])
        event_cell = cells[event_index]
        event_name = texts[event_index]
        ctf_index = headers.get("ctf", len(cells)) + header_offset
        rating_index = headers.get("rating", len(cells)) + header_offset
        ctf_points = texts[ctf_index] if ctf_index < len(cells) else "-"
        rating_points = (
            texts[rating_index] if rating_index < len(cells) else "-"
        )
    else:
        pairs = [(cell, text) for cell, text in zip(cells, texts) if text]
        if len(pairs) < 3:
            return None

        place_pair_index = next(
            (
                index
                for index, (_, text) in enumerate(pairs[:-1])
                if (place := parse_first_int(text)) is not None and 1 <= place <= MAX_PLACE
            ),
            None,
        )
        if place_pair_index is None:
            return None

        place = parse_first_int(pairs[place_pair_index][1])
        event_cell, event_name = pairs[place_pair_index + 1]
        ctf_points = pairs[place_pair_index + 2][1] if place_pair_index + 2 < len(pairs) else "-"
        rating_points = pairs[place_pair_index + 3][1] if place_pair_index + 3 < len(pairs) else "-"

    if place is None or place < 1 or place > MAX_PLACE or not event_name:
        return None

    event_link = event_cell.find("a", href=True) if event_cell else None
    event_url = ""
    if event_link:
        href = event_link["href"]
        event_url = href if href.startswith("http") else f"https://ctftime.org{href}"

    return {
        "place": place,
        "event": event_name,
        "ctfPoints": ctf_points,
        "ratingPoints": rating_points,
        "url": event_url,
    }


def parse_results(html: str) -> dict[str, list[dict[str, str | int]]]:
    soup = BeautifulSoup(html, "html.parser")
    results: dict[str, list[dict[str, str | int]]] = {year: [] for year in YEARS}
    current_year: str | None = None
    fallback_year_index = 0

    for node in soup.find_all(True):
        if node.name != "table":
            if node.find("table"):
                continue

            text = node.get_text(" ", strip=True)
            if is_year_marker(text):
                current_year = find_year(text)
            continue

        if not is_result_table(node):
            continue

        year = infer_table_year(node) or (current_year if current_year in YEARS else None)
        if year is None and fallback_year_index < len(YEARS):
            year = YEARS[fallback_year_index]
        fallback_year_index += 1

        if year not in YEARS:
            continue

        headers = table_header_map(node)
        seen: set[tuple[int, str]] = set()
        for row in node.find_all("tr"):
            item = parse_result_row(row, headers)
            if item is None:
                continue

            unique_key = (int(item["place"]), str(item["event"]).lower())
            if unique_key in seen:
                continue
            seen.add(unique_key)

            results[year].append(item)

    for year in YEARS:
        results[year].sort(key=lambda item: int(item["place"]))

    return results


def parse_rankings(html: str) -> dict[str, int | None]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    rankings: dict[str, int | None] = {"world": None, "vietnam": None}

    compact_text = " ".join(lines)
    world_patterns = (
        r"(?:Overall|Current)\s+rating\s+place\s*:?\s*#?\s*(\d+)",
        r"(?:Overall|World)\s+place\s*:?\s*#?\s*(\d+)",
        r"\bRating\s+place\s*:?\s*#?\s*(\d+)",
    )
    country_patterns = (
        r"(?:Country|Vietnam|Viet\s+Nam)\s+place\s*:?\s*#?\s*(\d+)",
        r"(?:Country|Vietnam|Viet\s+Nam)\s+rating\s+place\s*:?\s*#?\s*(\d+)",
    )
    world_match = next(
        (re.search(pattern, compact_text, re.I) for pattern in world_patterns if re.search(pattern, compact_text, re.I)),
        None,
    )
    country_match = next(
        (
            re.search(pattern, compact_text, re.I)
            for pattern in country_patterns
            if re.search(pattern, compact_text, re.I)
        ),
        None,
    )

    if world_match:
        rankings["world"] = int(world_match.group(1))

    if country_match:
        rankings["vietnam"] = int(country_match.group(1))

    for index, line in enumerate(lines):
        lower = line.lower()
        nearby = " ".join(lines[index : index + 3])

        if rankings["world"] is None and "overall" in lower and "place" in lower:
            rankings["world"] = parse_first_int(nearby)

        if rankings["vietnam"] is None and (
            "vietnam" in lower or "viet nam" in lower or "country" in lower
        ):
            rankings["vietnam"] = parse_first_int(nearby)

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
