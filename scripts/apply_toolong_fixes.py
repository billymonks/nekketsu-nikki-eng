#!/usr/bin/env python3
"""
Apply shortened translations from toolong reports back to MGDATA CSV files.

Reads each *_toolong.csv file from translations/toolong_reports/
and updates the corresponding MGDATA CSV with the shortened English translations.
"""
import csv
from pathlib import Path


def load_toolong_fixes(toolong_path: Path) -> dict:
    """Load fixes from a toolong CSV. Returns dict mapping Japanese -> new English."""
    fixes = {}

    with open(toolong_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = row.get('Japanese', '')
            en = row.get('English', '')
            if jp and en:
                fixes[jp] = en

    return fixes


def apply_fixes_to_csv(csv_path: Path, fixes: dict) -> tuple:
    """
    Apply fixes to a MGDATA CSV file.
    Returns (number of fixes applied, list of unmatched Japanese texts).
    """
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    matched_jp = set()
    fixes_applied = 0

    for row in rows:
        jp = row['Japanese']
        if jp in fixes:
            old_en = row['English']
            new_en = fixes[jp]
            if old_en != new_en:
                row['English'] = new_en
                fixes_applied += 1
            matched_jp.add(jp)

    unmatched = [jp for jp in fixes.keys() if jp not in matched_jp]

    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, doublequote=True)
        writer.writerow(['Japanese', 'English', 'offset'])
        for row in rows:
            writer.writerow([row['Japanese'], row['English'], row['offset']])

    return fixes_applied, unmatched


def main():
    project_dir = Path(__file__).parent.parent
    translations_dir = project_dir / "translations"
    toolong_dir = translations_dir / "toolong_reports"

    target_files = {
        "MGDATA_00000062_toolong.csv": translations_dir / "MGDATA_00000062.csv",
        "MGDATA_00000063_toolong.csv": translations_dir / "MGDATA_00000063.csv",
    }

    if not toolong_dir.exists():
        print(f"ERROR: Toolong reports directory not found: {toolong_dir}")
        return 1

    toolong_files = sorted(toolong_dir.glob("MGDATA_*_toolong.csv"))

    if not toolong_files:
        print("No toolong CSV files found.")
        return 0

    print(f"Found {len(toolong_files)} toolong report file(s)")
    print("=" * 80)

    total_fixes = 0
    all_unmatched = []

    for toolong_path in toolong_files:
        csv_path = target_files.get(toolong_path.name)
        if csv_path is None:
            # Derive from name: MGDATA_00000062_toolong.csv -> MGDATA_00000062.csv
            csv_name = toolong_path.stem.replace("_toolong", "") + ".csv"
            csv_path = translations_dir / csv_name

        if not csv_path.exists():
            print(f"WARNING: Target CSV not found: {csv_path}")
            continue

        fixes = load_toolong_fixes(toolong_path)

        if not fixes:
            continue

        fixes_applied, unmatched = apply_fixes_to_csv(csv_path, fixes)

        if fixes_applied > 0 or unmatched:
            print(f"  {csv_path.name}: {fixes_applied} fixes applied", end="")
            if unmatched:
                print(f", {len(unmatched)} unmatched")
                for jp in unmatched:
                    all_unmatched.append((csv_path.name, jp))
            else:
                print()

        total_fixes += fixes_applied

    print("=" * 80)
    print(f"Total fixes applied: {total_fixes}")

    if all_unmatched:
        print(f"\n{len(all_unmatched)} Japanese texts not found in target CSVs:")
        for csv_name, jp in all_unmatched:
            print(f"  [{csv_name}] {jp[:60]}{'...' if len(jp) > 60 else ''}")
    else:
        print("\nAll Japanese texts matched successfully!")

    return 0


if __name__ == '__main__':
    exit(main())
