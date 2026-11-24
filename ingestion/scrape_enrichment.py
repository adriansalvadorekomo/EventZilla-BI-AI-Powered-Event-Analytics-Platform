"""Enrichment: scrape public reference data with Firecrawl and land it next to the workbook.

    FIRECRAWL_KEY=... python ingestion/scrape_enrichment.py [--out DIR] [--s3]

Two entities, both joined to the star by dbt:
  tn_governorate  Tunisia's 24 governorates (population 2024, area, region), from Wikipedia. The providers' cities
                  are exactly these 24, so every reservation gets a region (dim_geography).
  tn_holiday      2022-2025 holidays for dim_date: the fixed national holidays (Wikipedia) and the Islamic ones,
                  computed with the Umm al-Qura calendar and checked against every date the Wikipedia articles give.
                  Tunisia fixes Islamic holidays by moon sighting, so a date can differ by one day.
Every row carries its source URL and the scrape date. Wikipedia text is CC BY-SA 4.0.
"""

import argparse
import csv
import datetime as dt
import io
import os
import re
from pathlib import Path

import requests
from hijridate import Hijri

API = "https://api.firecrawl.dev/v2/scrape"
WIKI = "https://en.wikipedia.org/wiki/"
YEARS = range(2022, 2026)
SCRAPED_AT = dt.date.today().isoformat()
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
MONTHS = {m: i for i, m in enumerate(["January", "February", "March", "April", "May", "June", "July", "August",
                                      "September", "October", "November", "December"], 1)}
# (name, Hijri month, Hijri day, days observed in Tunisia, Wikipedia article that lists dates by year)
ISLAMIC = [("Ramadan begins", 9, 1, 1, "Ramadan"), ("Eid al-Fitr", 10, 1, 2, "Eid_al-Fitr"),
           ("Eid al-Adha", 12, 10, 2, "Eid_al-Adha"), ("Islamic New Year", 1, 1, 1, "Islamic_New_Year"),
           ("Mawlid", 3, 12, 1, "Mawlid")]


def scrape(page: str) -> str:
    """Markdown of a Wikipedia article, through Firecrawl."""
    r = requests.post(API, timeout=120, headers={"Authorization": f"Bearer {os.environ['FIRECRAWL_KEY']}"},
                      json={"url": WIKI + page, "formats": ["markdown"], "onlyMainContent": True})
    r.raise_for_status()
    return r.json()["data"]["markdown"]


def clean(cell: str) -> str:
    return re.sub(r"\[\\\[\d+\\\]\]\([^)]*\)", "", LINK.sub(r"\1", cell)).replace("<br>", " ").strip()


def governorates() -> list[dict]:
    rows = []
    for line in scrape("Governorates_of_Tunisia").splitlines():
        if re.match(r"^\| \d+ \| ", line):
            _, _, name, pop, area, _, region, _ = [clean(c) for c in line.split("|")]
            rows.append({"governorate": name, "population_2024": pop.replace(",", ""),
                         "area_km2": area.replace(",", ""), "region": region,
                         "source_url": WIKI + "Governorates_of_Tunisia", "scraped_at": SCRAPED_AT})
    assert len(rows) == 24, f"expected 24 governorates, parsed {len(rows)}"
    return rows


def wikipedia_dates(article: str, markdown: str) -> set[dt.date]:
    """Every '<day> <Month> <year>' date in the article's tables, for the cross-check."""
    found = set()
    for line in markdown.splitlines():
        if line.startswith("|"):
            for d, m, y in re.findall(r"(\d{1,2}) (" + "|".join(MONTHS) + r") (\d{4})", clean(line)):
                if int(y) in YEARS:
                    found.add(dt.date(int(y), MONTHS[m], int(d)))
    return found


def holidays() -> tuple[list[dict], list[str]]:
    rows, report = [], []
    page = "Public_holidays_in_Tunisia"
    # national holidays only (Gregorian months); the page also lists the Islamic ones by Hijri month
    national = r"^- (" + "|".join(MONTHS) + r") (\d{1,2}): \[([^\]]+)\]"
    for month, day, name in re.findall(national, scrape(page), re.M):
        for year in YEARS:
            rows.append({"date": dt.date(year, MONTHS[month], int(day)).isoformat(), "holiday": name,
                         "kind": "national", "source_url": WIKI + page, "wikipedia_check": "", "scraped_at": SCRAPED_AT})
    for name, hm, hd, length, article in ISLAMIC:
        listed = wikipedia_dates(article, scrape(article))
        for hijri_year in range(1443, 1448):
            first = Hijri(hijri_year, hm, hd).to_gregorian()
            if first.year not in YEARS:
                continue
            near = [d for d in listed if abs((d - first).days) <= 1]
            check = ("same day as Wikipedia" if first in listed else
                     f"Wikipedia gives {near[0].isoformat()}" if near else "not listed on Wikipedia")
            report.append(f"{name} {first.year}: {first.isoformat()} · {check}")
            for offset in range(length):
                rows.append({"date": (first + dt.timedelta(days=offset)).isoformat(), "holiday": name,
                             "kind": "religious", "source_url": WIKI + article,
                             "wikipedia_check": check, "scraped_at": SCRAPED_AT})
    return rows, report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--out", help="also write the CSVs to this folder")
    parser.add_argument("--s3", action="store_true", help="upload to the landing bucket")
    args = parser.parse_args()
    if not os.environ.get("FIRECRAWL_KEY"):
        print("FIRECRAWL_KEY not set: the enrichment landed by the last run is kept")
        return

    holiday_rows, report = holidays()
    entities = {"tn_governorate": governorates(), "tn_holiday": holiday_rows}
    s3 = None
    if args.s3:
        import boto3

        s3 = boto3.client("s3", endpoint_url=os.environ["S3_ENDPOINT"],
                          aws_access_key_id=os.environ["S3_ACCESS_KEY"],
                          aws_secret_access_key=os.environ["S3_SECRET_KEY"])
    for entity, rows in entities.items():
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        data = buf.getvalue().encode()
        if args.out:
            Path(args.out).mkdir(parents=True, exist_ok=True)
            (Path(args.out) / f"{entity}.csv").write_bytes(data)
        if s3:
            s3.upload_fileobj(io.BytesIO(data), os.environ.get("LANDING_BUCKET", "landing"),
                              f"eventzilla/{entity}/{entity}.csv")
        print(f"{entity:18} {len(rows):>6} rows")
    print("\n".join(report))


if __name__ == "__main__":
    main()
