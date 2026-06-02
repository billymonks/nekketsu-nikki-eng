#!/usr/bin/env python3
"""
Check available extra bytes for each translation in 1ST_READ.BIN.

For each Japanese string from the translation CSVs, finds it in the binary
and reports how many trailing null bytes exist after it. Extra nulls (beyond
the 1 required terminator) can be used to fit longer English translations.

Also shows whether the English translation currently fits, needs the extra
space, or still doesn't fit even with it.
"""

import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DISC_DIR = PROJECT_DIR / "extracted-disc"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"


def load_translations_from_csv(csv_path: Path) -> dict:
    translations = {}
    if not csv_path.exists():
        print(f"WARNING: Translation file not found: {csv_path}")
        return translations
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = row.get('Japanese', row.get('japanese', ''))
            en = row.get('English', row.get('english', ''))
            if jp and en:
                translations[jp] = en
    return translations


def check_available_bytes(binary_path: Path, replacements: dict, label: str = ""):
    with open(binary_path, 'rb') as f:
        data = f.read()

    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

    results = []

    for jp_text, en_text in sorted_replacements:
        jp_bytes = jp_text.encode('shift_jis')
        en_bytes = en_text.encode('shift_jis')

        jp_len = len(jp_bytes)
        en_len = len(en_bytes)
        diff = en_len - jp_len  # positive = English is longer

        # Find all occurrences
        pos = 0
        occurrences = []
        while True:
            idx = data.find(jp_bytes, pos)
            if idx == -1:
                break

            # Count trailing null bytes
            text_end = idx + jp_len
            null_count = 0
            while text_end + null_count < len(data) and data[text_end + null_count] == 0x00:
                null_count += 1

            extra = max(0, null_count - 1)  # usable extra bytes (keep 1 null)
            available = jp_len + extra

            occurrences.append({
                'offset': idx,
                'null_count': null_count,
                'extra': extra,
                'available': available,
            })

            pos = idx + jp_len

        if not occurrences:
            results.append({
                'japanese': jp_text,
                'english': en_text,
                'jp_len': jp_len,
                'en_len': en_len,
                'diff': diff,
                'status': 'NOT FOUND',
                'extra': 0,
                'available': 0,
                'null_count': 0,
                'occurrences': 0,
            })
            continue

        for occ in occurrences:
            if en_len <= jp_len:
                status = 'FITS'
            elif en_len <= occ['available']:
                status = 'FITS (using extra nulls)'
            else:
                status = f"TOO LONG by {en_len - occ['available']}B"

            results.append({
                'japanese': jp_text,
                'english': en_text,
                'jp_len': jp_len,
                'en_len': en_len,
                'diff': diff,
                'status': status,
                'extra': occ['extra'],
                'available': occ['available'],
                'null_count': occ['null_count'],
                'offset': occ['offset'],
                'occurrences': len(occurrences),
            })

    return results


def main():
    binary_path = EXTRACTED_DISC_DIR / "1ST_READ.BIN"
    if not binary_path.exists():
        print(f"ERROR: {binary_path} not found")
        return

    # Load translations from both CSVs
    strings_csv = TRANSLATIONS_DIR / "1st_read_strings.csv"
    dangerous_csv = TRANSLATIONS_DIR / "1st_read_dangerous.csv"

    all_results = []

    for csv_path, label in [(strings_csv, "strings"), (dangerous_csv, "dangerous")]:
        translations = load_translations_from_csv(csv_path)
        if translations:
            print(f"Loaded {len(translations)} translations from {csv_path.name}")
            results = check_available_bytes(binary_path, translations, label)
            for r in results:
                r['source'] = label
            all_results.extend(results)

    # Build per-string summary: for strings with multiple occurrences,
    # use the MINIMUM extra across all occurrences (the real expansion limit)
    per_string = {}
    for r in all_results:
        key = (r['japanese'], r['english'])
        if key not in per_string:
            per_string[key] = {
                'japanese': r['japanese'],
                'english': r['english'],
                'jp_len': r['jp_len'],
                'en_len': r['en_len'],
                'min_extra': r['extra'],
                'min_available': r['available'],
                'status': r['status'],
                'occurrences': [],
            }
        entry = per_string[key]
        entry['min_extra'] = min(entry['min_extra'], r['extra'])
        entry['min_available'] = min(entry['min_available'], r['available'])
        entry['occurrences'].append(r)

    # Categorize per-string entries
    fits_normal = [r for r in all_results if r['status'] == 'FITS']
    fits_extra = [r for r in all_results if r['status'] == 'FITS (using extra nulls)']
    too_long = [r for r in all_results if r['status'].startswith('TOO LONG')]
    not_found = [r for r in all_results if r['status'] == 'NOT FOUND']

    # Expandable: English fits within JP length, but there's extra null space
    expandable = []
    for key, entry in per_string.items():
        if entry['en_len'] <= entry['jp_len'] and entry['min_extra'] > 0:
            spare = entry['min_available'] - entry['en_len']
            entry['spare'] = spare
            expandable.append(entry)
    expandable.sort(key=lambda x: x['spare'], reverse=True)

    # Print summary to console
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"  Fits normally:          {len(fits_normal)}")
    print(f"  Fits using extra nulls: {len(fits_extra)}")
    print(f"  Still too long:         {len(too_long)}")
    print(f"  Not found:              {len(not_found)}")
    print(f"  Could be expanded:      {len(expandable)} unique strings")

    # Write detailed report to file
    report_path = TRANSLATIONS_DIR / "available_bytes_report.txt"
    with open(report_path, 'w', encoding='utf-8') as out:
        out.write("=" * 70 + "\n")
        out.write("AVAILABLE BYTES REPORT FOR 1ST_READ.BIN\n")
        out.write("=" * 70 + "\n\n")
        out.write(f"Fits normally:          {len(fits_normal)}\n")
        out.write(f"Fits using extra nulls: {len(fits_extra)}\n")
        out.write(f"Still too long:         {len(too_long)}\n")
        out.write(f"Not found:              {len(not_found)}\n")
        out.write(f"Could be expanded:      {len(expandable)} unique strings\n")

        out.write(f"\n{'=' * 70}\n")
        out.write(f"COULD BE EXPANDED ({len(expandable)} strings with extra null space)\n")
        out.write(f"  'spare' = how many more bytes the English could grow.\n")
        out.write(f"  'avail' = min available across all occurrences (the real limit).\n")
        out.write(f"{'=' * 70}\n\n")
        for e in expandable:
            occ_count = len(e['occurrences'])
            extras = [o['extra'] for o in e['occurrences']]
            extra_range = f"{min(extras)}-{max(extras)}" if min(extras) != max(extras) else str(min(extras))
            out.write(f"  EN({e['en_len']}B) / JP({e['jp_len']}B) / avail({e['min_available']}B) = +{e['spare']}B spare  [{occ_count} occ, extra nulls: {extra_range}]\n")
            out.write(f"    JP: {e['japanese']}\n")
            out.write(f"    EN: {e['english']}\n\n")

        out.write(f"\n{'=' * 70}\n")
        out.write(f"FITS USING EXTRA NULLS ({len(fits_extra)} occurrences - would have been truncated before)\n")
        out.write(f"{'=' * 70}\n\n")
        for r in fits_extra:
            out.write(f"  JP({r['jp_len']}B) EN({r['en_len']}B) +{r['extra']}B extra nulls = {r['available']}B available\n")
            out.write(f"    JP: {r['japanese']}\n")
            out.write(f"    EN: {r['english']}\n\n")

        out.write(f"\n{'=' * 70}\n")
        out.write(f"STILL TOO LONG ({len(too_long)} occurrences - even with extra nulls)\n")
        out.write(f"{'=' * 70}\n\n")
        for r in too_long:
            over = r['en_len'] - r['available']
            out.write(f"  JP({r['jp_len']}B) EN({r['en_len']}B) +{r['extra']}B extra nulls = {r['available']}B available | {over}B over\n")
            out.write(f"    JP: {r['japanese']}\n")
            out.write(f"    EN: {r['english']}\n\n")

        out.write(f"\n{'=' * 70}\n")
        out.write(f"NOT FOUND IN BINARY ({len(not_found)} strings)\n")
        out.write(f"{'=' * 70}\n\n")
        for r in not_found:
            out.write(f"  {r['japanese']}\n")

    print(f"\nDetailed report written to: {report_path}")


if __name__ == '__main__':
    main()
