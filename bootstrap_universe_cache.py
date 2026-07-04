"""
One-time bootstrap: seed nse_universe_cache.csv
=================================================
Run this ONCE from Google Colab or Termux on your phone, then commit the
resulting nse_universe_cache.csv file to your repo. This gives the
GitHub Actions workflow a fallback list on day one, instead of gambling
on NSE's site cooperating with the very first live fetch.

Usage (Colab or Termux):
    pip install requests pandas
    python bootstrap_universe_cache.py

Then commit the generated nse_universe_cache.csv into the repo root
(same folder as multibagger_hunter.py).
"""

import io
import csv
import sys
import requests
import pandas as pd

NSE_EQUITY_LIST_URL = "https://archives.nseindia.com/content/equity/EQUITY_L.csv"
OUTPUT_PATH = "nse_universe_cache.csv"


def main():
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/csv,application/csv,*/*",
    }
    session = requests.Session()
    session.headers.update(headers)

    print("Warming up session with NSE...")
    session.get("https://www.nseindia.com", timeout=10)

    print("Fetching equity list...")
    resp = session.get(NSE_EQUITY_LIST_URL, timeout=15)
    resp.raise_for_status()

    reader = csv.DictReader(io.StringIO(resp.text))
    symbols = [
        row["SYMBOL"].strip() + ".NS"
        for row in reader
        if row.get("SERIES", "").strip() == "EQ" and row.get("SYMBOL")
    ]

    if len(symbols) < 500:
        print(f"ERROR: Only got {len(symbols)} symbols, expected 1500+. "
              "NSE may have blocked this request. Try again from a different network, "
              "or run this from Colab instead of Termux (or vice versa).")
        sys.exit(1)

    pd.Series(symbols, name="ticker").to_csv(OUTPUT_PATH, index=False)
    print(f"Success: wrote {len(symbols)} symbols to {OUTPUT_PATH}")
    print("Now commit this file into your repo root alongside multibagger_hunter.py")


if __name__ == "__main__":
    main()
