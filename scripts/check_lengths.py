#!/usr/bin/env python3
"""
Check for translations where English is longer than Japanese (in Shift-JIS bytes).
These will be truncated during replacement and may cause issues.

Works with MGDATA_00000062.csv and MGDATA_00000063.csv.
Outputs a _toolong.csv file for each file with issues.
"""
import csv
from pathlib import Path


def get_byte_length(text: str) -> int:
    """Get the byte length of text in Shift-JIS encoding.

    Note: '/' is a line break control character in the game's script format
    and doesn't count toward displayed text length, so we exclude it.
    """
    text = text.replace('/', '')

    try:
        return len(text.encode('shift_jis'))
    except UnicodeEncodeError:
        length = 0
        for char in text:
            if ord(char) < 128:
                length += 1
            else:
                length += 2
        return length


def check_csv(csv_path: Path) -> list:
    """Check a CSV file for translations that are too long."""
    issues = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for line_num, row in enumerate(reader, start=2):
            jp = row['Japanese']
            en = row['English']
            offset = row['offset']

            if not jp or not en:
                continue

            jp_bytes = get_byte_length(jp)
            if jp_bytes % 2:
                jp_bytes -= 1
            en_bytes = get_byte_length(en)

            if en_bytes > jp_bytes:
                overflow = en_bytes - jp_bytes
                issues.append({
                    'line': line_num,
                    'Japanese': jp,
                    'English': en,
                    'offset': offset,
                    'jp_bytes': jp_bytes,
                    'en_bytes': en_bytes,
                    'overflow': overflow,
                })

    return issues


def write_issues_csv(source_path: Path, issues: list, output_dir: Path) -> Path:
    """Write issues to a CSV file."""
    output_name = source_path.stem + "_toolong.csv"
    output_path = output_dir / output_name

    issues.sort(key=lambda x: x['overflow'], reverse=True)

    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, doublequote=True)
        writer.writerow(['Japanese', 'English', 'offset', 'jp_bytes', 'en_bytes', 'overflow'])

        for issue in issues:
            writer.writerow([
                issue['Japanese'],
                issue['English'],
                issue['offset'],
                issue['jp_bytes'],
                issue['en_bytes'],
                issue['overflow'],
            ])

    return output_path


def main():
    project_dir = Path(__file__).parent.parent
    translations_dir = project_dir / "translations"
    output_dir = translations_dir / "toolong_reports"

    target_files = [
        translations_dir / "MGDATA_00000062.csv",
        translations_dir / "MGDATA_00000063.csv",
    ]

    output_dir.mkdir(parents=True, exist_ok=True)

    print("Checking translation lengths...")
    print("=" * 80)

    total_issues = 0
    files_with_issues = 0

    for target_path in target_files:
        if not target_path.exists():
            print(f"  WARNING: {target_path.name} not found, skipping.")
            continue

        issues = check_csv(target_path)

        if issues:
            output_path = write_issues_csv(target_path, issues, output_dir)
            print(f"  {target_path.name}: {len(issues)} issues -> {output_path.name}")
            total_issues += len(issues)
            files_with_issues += 1
        else:
            # Remove stale report if it exists
            report_path = output_dir / (target_path.stem + "_toolong.csv")
            if report_path.exists():
                report_path.unlink()
                print(f"  {target_path.name}: All fixed! Removed {report_path.name}")
            else:
                print(f"  {target_path.name}: No issues")

    print("=" * 80)

    if total_issues == 0:
        print("All translations fit within byte limits!")
        return 0

    print(f"\nFound {total_issues} translations that are TOO LONG")
    print(f"across {files_with_issues} file(s)")
    print(f"\nReports written to: {output_dir}")
    print("\nEach report CSV contains:")
    print("  - Japanese/English: The strings (edit English to shorten)")
    print("  - offset: Hex offset in original binary")
    print("  - jp_bytes/en_bytes: Byte lengths")
    print("  - overflow: How many bytes to cut")

    return 1


if __name__ == '__main__':
    exit(main())
