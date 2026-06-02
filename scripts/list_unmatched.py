#!/usr/bin/env python3
"""Generate a file listing all unmatched (no English) rows from MGDATA CSVs."""

import csv
from pathlib import Path

TRANSLATIONS_DIR = Path(__file__).parent.parent / "translations"

TARGET_FILES = [
    TRANSLATIONS_DIR / "MGDATA_00000062.csv",
    TRANSLATIONS_DIR / "MGDATA_00000063.csv",
]
OUTPUT_FILE = TRANSLATIONS_DIR / "unmatched_strings.csv"

with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as out:
    writer = csv.writer(out, quoting=csv.QUOTE_ALL, doublequote=True)
    writer.writerow(["File", "Row", "Japanese", "English", "offset"])

    for target_path in TARGET_FILES:
        with open(target_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if row['English'] == '':
                    writer.writerow([
                        target_path.name,
                        i + 2,  # 1-indexed + header
                        row['Japanese'],
                        "",
                        row['offset'],
                    ])

print(f"Written to {OUTPUT_FILE}")
