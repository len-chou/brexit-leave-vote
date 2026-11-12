"""
Data for the Brexit Streamlit app.

This file has no Streamlit or Plotly code. It loads the clean table and
recomputes the numbers of the Tableau dashboard with the same formulas:
  - Leave share of a group of areas -> SUM(leave_votes) / SUM(valid_votes)
  - gap -> areas are sorted by a measure and cut into five equal groups
           (20% of areas each); gap = Leave share of the top 20% minus the
           bottom 20%, like the KPI sheets in Tableau and notebook 02.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

def _find_data_dir() -> Path:
    """
    Find the folder that holds gb_areas_clean.csv, wherever app.py sits:
    a data/ folder next to this file, a data/ folder one level up (repo root),
    or the same folder as this file.
    """
    here = Path(__file__).resolve().parent
    for folder in (here / "data", here.parent / "data", here):
        if (folder / "gb_areas_clean.csv").exists():
            return folder
    raise FileNotFoundError(
        "gb_areas_clean.csv not found. Put it in a 'data' folder next to app.py "
        f"(looked in {here / 'data'}, {here.parent / 'data'} and {here})."
    )


DATA_DIR = _find_data_dir()

# Readable names for every measure (the CSV column -> the label shown in the app)
MEASURES = {
    "pct_degree": "Graduates",
    "pct_noqual": "No qualifications",
    "pct_ab": "Social grade AB",
    "pct_de": "Social grade DE",
    "pct_65plus": "Aged 65+",
    "pct_18_29": "Aged 18-29",
    "median_weekly_pay": "Median weekly pay",
    "claimant_rate": "Claimant rate",
    "child_poverty_pct": "Child poverty",
    "ukip_2014_pct": "UKIP vote 2014",
}
UNITS = {"median_weekly_pay": "£"}  # every other measure is a percentage

# The six gaps shown in the Tableau "KPI gaps" sheet
TABLEAU_KPIS = ["pct_degree", "pct_ab", "median_weekly_pay", "pct_65plus", "claimant_rate", "ukip_2014_pct"]


def fmt_measure(col: str, value: float) -> str:
    """Write a value with its unit: '£495' or '17.6%'."""
    if pd.isna(value):
        return "n/a"
    return f"£{value:,.0f}" if UNITS.get(col) == "£" else f"{value:.1f}%"


def weighted_leave(df: pd.DataFrame) -> float:
    """Leave share of all valid votes in a group of areas (big areas count more)."""
    valid = df["valid_votes"].sum()
    return float("nan") if valid == 0 else 100 * df["leave_votes"].sum() / valid


def load_areas(path: Path = DATA_DIR / "gb_areas_clean.csv") -> pd.DataFrame:
    """The 380 Great Britain areas, plus the Leave share of each area's region."""
    areas = pd.read_csv(path)
    totals = areas.groupby("region")[["leave_votes", "valid_votes"]].transform("sum")
    areas["region_leave_pct"] = 100 * totals["leave_votes"] / totals["valid_votes"]
    return areas


def load_boundaries(path: Path = DATA_DIR / "gb_areas_boundaries.geojson") -> tuple[dict, pd.DataFrame]:
    """Area outlines, plus one label point per area (centre of its largest polygon)."""
    with open(path, encoding="utf-8") as f:
        geo = json.load(f)
    points = []
    for feat in geo["features"]:
        g = feat["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        ring = np.array(max((p[0] for p in polys), key=len))
        points.append({"code": feat["properties"]["code"], "lon": ring[:, 0].mean(), "lat": ring[:, 1].mean()})
    return geo, pd.DataFrame(points)


def band_shares(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """
    Sort the areas by one measure, cut them into five equal groups (20% of
    areas each) and give the Leave share of each group. Groups are cut inside
    df, so a filtered selection is split into its own five groups.
    """
    d = df.dropna(subset=[col])
    band = pd.qcut(d[col], 5, labels=[1, 2, 3, 4, 5]).astype("float")
    rows = []
    for b in range(1, 6):
        part = d[band == b]
        rows.append({"band": b, "leave": weighted_leave(part), "areas": len(part),
                     "low": part[col].min(), "high": part[col].max()})
    return pd.DataFrame(rows)


def gap(df: pd.DataFrame, col: str) -> float:
    """Leave share of the top 20% of areas minus the bottom 20%, in points."""
    s = band_shares(df, col).set_index("band")["leave"]
    return float(s[5] - s[1])


def gap_table(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """One row per measure: bottom 20% share, top 20% share, gap and r."""
    rows = []
    for col in cols:
        s = band_shares(df, col).set_index("band")["leave"]
        rows.append({"col": col, "measure": MEASURES[col], "bottom": s[1], "top": s[5],
                     "gap": s[5] - s[1], "r": df[col].corr(df["leave_pct"])})
    return pd.DataFrame(rows).sort_values("gap")


def kpis(df: pd.DataFrame) -> dict:
    """Headline figures (same formulas as the Tableau KPI sheets)."""
    return {
        "leave_share": weighted_leave(df),
        "areas": len(df),
        "leave_areas": int((df["leave_pct"] > 50).sum()),
        "turnout": 100 * df["votes_cast"].sum() / df["electorate"].sum(),
        "graduate_gap": gap(df, "pct_degree"),
    }
