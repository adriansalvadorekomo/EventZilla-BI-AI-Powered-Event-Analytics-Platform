"""backend/reports is the copy the Vercel deployment ships; it must match ml/reports (`mise run ml` refreshes both)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_bundled_reports_match_the_source():
    source = {p.name: p.read_bytes() for p in (ROOT / "ml" / "reports").glob("*.json")}
    bundled = {p.name: p.read_bytes() for p in (ROOT / "backend" / "reports").glob("*.json")}
    assert source and source == bundled
