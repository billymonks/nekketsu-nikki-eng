#!/usr/bin/env python3
"""
Text Replacement Script for Nekketsu Nikki Translation
Reads translations from CSV files and applies them to game script files
"""

import csv
import os
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_DIR / "extracted-afs"
MODIFIED_AFS_DIR = PROJECT_DIR / "modified-afs-contents"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"


def load_translations_from_csv(csv_path: Path) -> dict:
    """
    Load translations from a CSV file.
    
    CSV format: japanese,english,context,notes
    
    Returns dict of {japanese_text: english_text}
    """
    translations = {}
    
    if not csv_path.exists():
        print(f"WARNING: Translation file not found: {csv_path}")
        return translations
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = row.get('japanese', '').strip()
            en = row.get('english', '').strip()
            if jp and en:
                translations[jp] = en
    
    print(f"Loaded {len(translations)} translations from {csv_path.name}")
    return translations


def load_all_translations(target_file: str) -> dict:
    """
    Load all translation CSV files for a target file.
    
    Naming convention: {target}_{category}.csv
    Example: mgdata_62_dialog.csv, mgdata_62_player_select.csv
    """
    all_translations = {}
    
    # Find all CSVs matching the target pattern
    pattern = target_file.lower().replace('/', '_').replace('\\', '_')
    
    for csv_file in TRANSLATIONS_DIR.glob("*.csv"):
        if csv_file.stem.startswith(pattern) or pattern in csv_file.stem:
            translations = load_translations_from_csv(csv_file)
            all_translations.update(translations)
    
    return all_translations


def replace_text_in_file(input_file: Path, output_file: Path, replacements: dict, pad_to_length=True):
    """
    Replace text in a binary file using Shift-JIS encoding.
    Pads English text with spaces to match Japanese byte length.
    """
    with open(input_file, 'rb') as f:
        data = f.read()
    
    modified = data
    replaced_count = 0
    
    for jp_text, en_text in replacements.items():
        jp_bytes = jp_text.encode('shift_jis')
        en_bytes = en_text.encode('shift_jis')
        
        if jp_bytes in modified:
            if pad_to_length:
                if len(en_bytes) < len(jp_bytes):
                    padding = len(jp_bytes) - len(en_bytes)
                    en_bytes = en_bytes + b' ' * padding
                elif len(en_bytes) > len(jp_bytes):
                    print(f"WARNING: English is {len(en_bytes) - len(jp_bytes)} bytes LONGER - truncating!")
                    en_bytes = en_bytes[:len(jp_bytes)]
            
            modified = modified.replace(jp_bytes, en_bytes)
            replaced_count += 1
            print(f"  [{replaced_count}] {jp_text[:25]}... -> {en_text[:25]}...")
        else:
            print(f"  NOT FOUND: {jp_text[:40]}...")
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'wb') as f:
        f.write(modified)
    
    return replaced_count


def process_mgdata_62():
    """Process MGDATA file 00000062 (female protagonist scripts)"""
    print("\n" + "=" * 60)
    print("Processing MGDATA/00000062")
    print("=" * 60)
    
    # Load translations from all relevant CSVs
    translations = {}
    for csv_file in TRANSLATIONS_DIR.glob("mgdata_62_*.csv"):
        translations.update(load_translations_from_csv(csv_file))
    
    if not translations:
        print("No translations found!")
        return 0
    
    target_file = MODIFIED_AFS_DIR / "MGDATA" / "00000062"
    count = replace_text_in_file(target_file, target_file, translations)
    
    print(f"\nReplaced {count} strings in {target_file.name}")
    return count


def main():
    """
    Translation Format Reference:
    =============================
    
    LINE BREAKS:
        Use 、/ (Japanese comma + slash) for line breaks
        Example: "Line 1、/Line 2、/Line 3"
    
    COLOR CODES:
        !c01 = pink/magenta
        !c02 = green  
        !c03 = blue
        !c04 = orange/red
        !c05 = pink
        !c07 = white (default)
    
    IMPORTANT: The ! character must be at an EVEN byte position!
        - Use fullwidth space (　) which is 2 bytes to maintain alignment
        - "1 Human " (8 bytes) + !c07 = ! at position 12 (even) ✓
        - "1 Human" (7 bytes) + !c07 = ! at position 11 (odd) ✗
    """
    
    print("Nekketsu Nikki Translation Tool")
    print("=" * 60)
    print(f"Translations folder: {TRANSLATIONS_DIR}")
    print(f"Modified AFS folder: {MODIFIED_AFS_DIR}")
    
    # List available translation files
    csv_files = list(TRANSLATIONS_DIR.glob("*.csv"))
    print(f"\nFound {len(csv_files)} translation file(s):")
    for f in csv_files:
        print(f"  - {f.name}")
    
    # Process files
    total = 0
    total += process_mgdata_62()
    
    print("\n" + "=" * 60)
    print(f"Total replacements: {total}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run scripts\\rebuild.bat to rebuild the disc")
    print("2. Test translated-disc\\disc.gdi in emulator")


if __name__ == '__main__':
    main()
