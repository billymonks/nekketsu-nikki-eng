#!/usr/bin/env python3
"""
Merge existing translation CSV files into the extracted files.
"""

import csv
import io
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_DIR / "translations"


def load_translations(csv_path: Path) -> dict:
    """Load translations from a CSV file."""
    translations = {}
    if not csv_path.exists():
        return translations
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')  # Remove NUL chars
    
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        jp = row.get('japanese', '').strip()
        en = row.get('english', '').strip()
        if jp and en:
            translations[jp] = {
                'english': en,
                'context': row.get('context', ''),
                'notes': row.get('notes', '')
            }
    
    return translations


def merge_into_extracted(extracted_path: Path, existing_translations: dict):
    """Merge existing translations into the extracted file."""
    
    # Read extracted file
    with open(extracted_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = []
    updated = 0
    reader = csv.DictReader(io.StringIO(content))
    
    for row in reader:
        jp = row.get('japanese', '')
        if jp in existing_translations:
            row['english'] = existing_translations[jp]['english']
            if existing_translations[jp].get('context'):
                row['context'] = existing_translations[jp]['context']
            if existing_translations[jp].get('notes'):
                row['notes'] = existing_translations[jp]['notes']
            updated += 1
        rows.append(row)
    
    # Write back
    with open(extracted_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['japanese', 'english', 'context', 'notes'], 
                                quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    return updated, len(rows)


def main():
    print("Merging existing translations into extracted files...")
    print("=" * 60)
    
    # For mgdata_62
    existing = {}
    
    # Load from dialog.csv
    dialog_path = TRANSLATIONS_DIR / "mgdata_62_dialog.csv"
    if dialog_path.exists():
        trans = load_translations(dialog_path)
        existing.update(trans)
        print(f"Loaded {len(trans)} from {dialog_path.name}")
    
    # Load from player_select.csv
    player_path = TRANSLATIONS_DIR / "mgdata_62_player_select.csv"
    if player_path.exists():
        trans = load_translations(player_path)
        existing.update(trans)
        print(f"Loaded {len(trans)} from {player_path.name}")
    
    print(f"Total existing translations: {len(existing)}")
    
    # Merge into extracted file
    extracted_path = TRANSLATIONS_DIR / "mgdata_62_extracted.csv"
    if extracted_path.exists():
        updated, total = merge_into_extracted(extracted_path, existing)
        print(f"\nMerged {updated} translations into {extracted_path.name}")
        print(f"Total strings in file: {total}")
    
    # Clean up old files (optional - just rename them)
    print("\n" + "=" * 60)
    print("Done! You can now delete or archive the old files:")
    print(f"  - {dialog_path.name}")
    print(f"  - {player_path.name}")
    print(f"\nWork with: {extracted_path.name}")


if __name__ == '__main__':
    main()
