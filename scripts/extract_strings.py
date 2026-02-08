#!/usr/bin/env python3
"""
Extract all @-terminated strings from MGDATA/00000062 and MGDATA/00000063.

String table format:
- Starts at offset 0x4748 in both files
- Each string begins with a portrait code like !p0100!e00
- Strings are encoded in Shift-JIS
- Each string is terminated by @ (0x40 as a standalone ASCII byte)
- Between strings there may be 0 or more null (0x00) padding bytes
- Important: 0x40 can also appear as a trail byte in Shift-JIS double-byte
  characters, so we must parse Shift-JIS properly to find real @ terminators.

Outputs:
- translations/MGDATA_00000062.csv
- translations/MGDATA_00000063.csv

Columns: Japanese, English (blank), offset (hex)
"""

import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_DIR / "extracted-afs" / "MGDATA"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"

STRING_TABLE_START = 0x4748

FILES = [
    ("00000062", "MGDATA_00000062.csv"),
    ("00000063", "MGDATA_00000063.csv"),
]


def is_sjis_lead(b: int) -> bool:
    """Check if byte is a Shift-JIS lead byte (starts a 2-byte character)."""
    return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF)


def extract_strings(data: bytes, start_offset: int) -> list:
    """
    Extract all @-terminated strings from binary data starting at start_offset.

    Uses proper Shift-JIS awareness: when a lead byte (0x81-0x9F or 0xE0-0xEF)
    is encountered, the next byte is a trail byte and is skipped -- even if it
    happens to be 0x40. Only a standalone 0x40 counts as the @ terminator.

    Returns a list of dicts: { 'japanese': str, 'offset': str }
    """
    strings = []
    pos = start_offset
    string_start = pos

    while pos < len(data):
        b = data[pos]

        # Shift-JIS double-byte character: skip lead + trail
        if is_sjis_lead(b) and pos + 1 < len(data):
            pos += 2
            continue

        # Standalone @ terminator
        if b == 0x40:
            raw = data[string_start:pos]  # everything before the @
            if len(raw) > 0:
                text = raw.decode('shift_jis', errors='replace')
                # Strip any stray NUL bytes that occasionally appear mid-string
                text = text.replace('\x00', '')
                strings.append({
                    'japanese': text,
                    'offset': f"0x{string_start:X}",
                })
            pos += 1
            # Skip null padding bytes between strings
            while pos < len(data) and data[pos] == 0x00:
                pos += 1
            string_start = pos
            continue

        pos += 1

    return strings


def write_csv(strings: list, output_path: Path):
    """Write extracted strings to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, doublequote=True)
        writer.writerow(["Japanese", "English", "offset"])
        for s in strings:
            writer.writerow([s['japanese'], "", s['offset']])

    print(f"  Wrote {len(strings)} strings to {output_path}")


def main():
    print("Nekketsu Nikki String Extractor")
    print("=" * 60)

    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, csv_name in FILES:
        filepath = EXTRACTED_DIR / filename
        if not filepath.exists():
            print(f"  WARNING: {filepath} not found, skipping.")
            continue

        print(f"\nProcessing {filepath}...")
        with open(filepath, 'rb') as f:
            data = f.read()

        print(f"  File size: {len(data)} bytes (0x{len(data):X})")
        print(f"  String table starts at: 0x{STRING_TABLE_START:X}")

        strings = extract_strings(data, STRING_TABLE_START)
        print(f"  Found {len(strings)} strings")

        output_path = TRANSLATIONS_DIR / csv_name
        write_csv(strings, output_path)

    print("\n" + "=" * 60)
    print("Done!")


if __name__ == '__main__':
    main()
