#!/usr/bin/env python3
"""
Move dangerous short strings (4 bytes or less in Shift-JIS) from regular CSV files
to 1st_read_dangerous.csv for safe null-terminated replacement.

Short strings can accidentally match binary data (pointers, code) and cause crashes.
"""

import csv
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_DIR / "translations"

# Files to scan for dangerous short strings
SOURCE_FILES = [
    "1st_read_strings.csv",
    "1st_read_menu.csv", 
    "1st_read_moves.csv",
]

DANGEROUS_FILE = "1st_read_dangerous.csv"
MAX_SAFE_BYTES = 4  # Strings 4 bytes or less are considered dangerous


def get_shift_jis_length(text: str) -> int:
    """Get the byte length of text when encoded in Shift-JIS."""
    try:
        return len(text.encode('shift_jis'))
    except UnicodeEncodeError:
        return len(text.encode('utf-8'))  # Fallback


def load_csv(filepath: Path) -> tuple[list[dict], list[str]]:
    """Load CSV and return rows and fieldnames."""
    if not filepath.exists():
        return [], []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    
    return rows, fieldnames


def save_csv(filepath: Path, rows: list[dict], fieldnames: list[str]):
    """Save rows to CSV file."""
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)


def main():
    print("=" * 60)
    print("Moving dangerous short strings to 1st_read_dangerous.csv")
    print(f"Threshold: {MAX_SAFE_BYTES} bytes or less = dangerous")
    print("=" * 60)
    
    # Load existing dangerous file
    dangerous_path = TRANSLATIONS_DIR / DANGEROUS_FILE
    existing_dangerous, _ = load_csv(dangerous_path)
    
    # Track existing Japanese strings to avoid duplicates
    existing_jp = {row.get('japanese', '') for row in existing_dangerous}
    
    # Standard fieldnames for dangerous file
    dangerous_fieldnames = ['japanese', 'english', 'context', 'notes']
    
    # Collect all dangerous entries
    new_dangerous = []
    
    for source_file in SOURCE_FILES:
        source_path = TRANSLATIONS_DIR / source_file
        if not source_path.exists():
            print(f"\nSkipping {source_file} (not found)")
            continue
        
        print(f"\n{'='*40}")
        print(f"Processing {source_file}")
        print('='*40)
        
        rows, fieldnames = load_csv(source_path)
        
        safe_rows = []
        dangerous_rows = []
        removed_count = 0
        
        for row in rows:
            jp_text = row.get('japanese', '')
            if not jp_text:
                safe_rows.append(row)
                continue
            
            byte_len = get_shift_jis_length(jp_text)
            
            if byte_len <= MAX_SAFE_BYTES:
                # This is a dangerous short string - always remove from source
                if jp_text not in existing_jp:
                    # Create entry for dangerous file
                    dangerous_entry = {
                        'japanese': jp_text,
                        'english': row.get('english', ''),
                        'context': row.get('context', ''),
                        'notes': f"JP:{byte_len} - moved from {source_file}",
                    }
                    dangerous_rows.append(dangerous_entry)
                    existing_jp.add(jp_text)
                    print(f"  MOVE: {jp_text} ({byte_len} bytes) -> {row.get('english', '')}")
                else:
                    print(f"  REMOVE (already in dangerous): {jp_text}")
                # Don't add to safe_rows - remove from source file either way
                removed_count += 1
            else:
                # Safe to keep in original file
                safe_rows.append(row)
        
        # Save updated source file (without dangerous entries)
        if removed_count > 0:
            save_csv(source_path, safe_rows, fieldnames)
            print(f"\n  Removed {removed_count} dangerous entries from {source_file}")
            print(f"  Added {len(dangerous_rows)} new entries to dangerous file")
            print(f"  Remaining safe entries: {len(safe_rows)}")
            new_dangerous.extend(dangerous_rows)
        else:
            print(f"\n  No dangerous entries found in {source_file}")
    
    # Save dangerous file with all entries
    if new_dangerous:
        all_dangerous = existing_dangerous + new_dangerous
        save_csv(dangerous_path, all_dangerous, dangerous_fieldnames)
        print(f"\n{'='*60}")
        print(f"Added {len(new_dangerous)} new entries to {DANGEROUS_FILE}")
        print(f"Total dangerous entries: {len(all_dangerous)}")
    else:
        print(f"\n{'='*60}")
        print("No new dangerous entries found")
    
    print("=" * 60)
    print("\nDone! Remember to run replace_text.py to apply translations.")


if __name__ == '__main__':
    main()
