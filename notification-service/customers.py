import csv
import os
from pathlib import Path

FILE = Path(os.getenv("CUSTOMERS_FILE") or Path(__file__).resolve().parent.parent / "data" / "customers.csv")


def load():
    if not FILE.exists():
        return {}
    with open(FILE, encoding="utf-8", newline="") as f:
        return {row["code"].strip().upper(): row for row in csv.DictReader(f) if row.get("code")}
