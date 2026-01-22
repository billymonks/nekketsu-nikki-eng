#!/usr/bin/env python3
"""
Text Replacement Script for Nekketsu Nikki Translation
Reads translations from CSV files and applies them to game script files.

Handles:
- MGDATA files (00000062, 00000063) - main game dialogue
- 1ST_READ.BIN - menu labels and UI text
"""

import csv
import shutil
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_AFS_DIR = PROJECT_DIR / "extracted-afs"
EXTRACTED_DISC_DIR = PROJECT_DIR / "extracted-disc"
MODIFIED_AFS_DIR = PROJECT_DIR / "modified-afs-contents"
MODIFIED_DISC_DIR = PROJECT_DIR / "modified-disc-files"
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
    
    IMPORTANT: Replacements are sorted by length (longest first) to prevent
    shorter substrings from corrupting longer strings during replacement.
    """
    with open(input_file, 'rb') as f:
        data = f.read()
    
    modified = data
    replaced_count = 0
    
    # Sort by Japanese text length (longest first) to prevent substring corruption
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    for jp_text, en_text in sorted_replacements:
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


def copy_original_files():
    """Copy original files from extracted-afs to modified-afs-contents for modification."""
    files_to_copy = [
        ("MGDATA", "00000062"),
        ("MGDATA", "00000063"),
    ]
    
    for archive, file_num in files_to_copy:
        src = EXTRACTED_AFS_DIR / archive / file_num
        dst = MODIFIED_AFS_DIR / archive / file_num
        
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied {archive}/{file_num} to modified-afs-contents/")
        else:
            print(f"WARNING: Source file not found: {src}")
    
    # Also copy the metadata JSON
    json_src = EXTRACTED_AFS_DIR / "MGDATA.json"
    json_dst = MODIFIED_AFS_DIR / "MGDATA.json"
    if json_src.exists():
        shutil.copy2(json_src, json_dst)
        print("Copied MGDATA.json")


def process_mgdata():
    """Process MGDATA files 00000062 and 00000063 (female & male protagonist scripts)"""
    
    # First, copy fresh originals
    print("\n" + "=" * 60)
    print("Copying original files from extracted-afs/")
    print("=" * 60)
    copy_original_files()
    
    # Load shared translations first
    shared_translations = {}
    shared_file = TRANSLATIONS_DIR / "mgdata_62_63.csv"
    if shared_file.exists():
        shared_translations.update(load_translations_from_csv(shared_file))
    
    # Load file-specific translations (these override shared)
    translations_62 = {}
    only_62_file = TRANSLATIONS_DIR / "mgdata_62_only.csv"
    if only_62_file.exists():
        translations_62.update(load_translations_from_csv(only_62_file))
    
    translations_63 = {}
    only_63_file = TRANSLATIONS_DIR / "mgdata_63_only.csv"
    if only_63_file.exists():
        translations_63.update(load_translations_from_csv(only_63_file))
    
    if not shared_translations and not translations_62 and not translations_63:
        print("No translations found!")
        return 0
    
    total = 0
    
    # Process file 62 (female protagonist) - shared + 62-specific
    print("\n" + "=" * 60)
    print("Processing MGDATA/00000062 (female protagonist)")
    print("=" * 60)
    target_62 = MODIFIED_AFS_DIR / "MGDATA" / "00000062"
    if target_62.exists():
        trans_62 = {**shared_translations, **translations_62}  # 62-specific overrides shared
        count = replace_text_in_file(target_62, target_62, trans_62)
        print(f"\nReplaced {count} strings in {target_62.name}")
        total += count
    
    # Process file 63 (male protagonist) - shared + 63-specific
    print("\n" + "=" * 60)
    print("Processing MGDATA/00000063 (male protagonist)")
    print("=" * 60)
    target_63 = MODIFIED_AFS_DIR / "MGDATA" / "00000063"
    if target_63.exists():
        trans_63 = {**shared_translations, **translations_63}  # 63-specific overrides shared
        count = replace_text_in_file(target_63, target_63, trans_63)
        print(f"\nReplaced {count} strings in {target_63.name}")
        total += count
    
    return total


def process_1st_read():
    """Process 1ST_READ.BIN (main executable with menu/UI text)"""
    
    input_file = EXTRACTED_DISC_DIR / "1ST_READ.BIN"
    output_file = MODIFIED_DISC_DIR / "1ST_READ.BIN"
    csv_file = TRANSLATIONS_DIR / "1st_read_menu.csv"
    
    print("\n" + "=" * 60)
    print("Processing 1ST_READ.BIN (menu/UI text)")
    print("=" * 60)
    
    if not input_file.exists():
        print(f"WARNING: Input file not found: {input_file}")
        print("Skipping 1ST_READ.BIN processing.")
        return 0
    
    if not csv_file.exists():
        print(f"WARNING: Translation file not found: {csv_file}")
        print("Skipping 1ST_READ.BIN processing.")
        return 0
    
    # Copy original file first
    output_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_file, output_file)
    print(f"Copied 1ST_READ.BIN to modified-disc-files/")
    
    # Load translations
    translations = load_translations_from_csv(csv_file)
    
    if not translations:
        print("No translations loaded for 1ST_READ.BIN")
        return 0
    
    # Apply translations
    count = replace_text_in_file(output_file, output_file, translations)
    print(f"\nReplaced {count} strings in 1ST_READ.BIN")
    
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
    print(f"Modified disc folder: {MODIFIED_DISC_DIR}")
    
    # List available translation files
    csv_files = list(TRANSLATIONS_DIR.glob("*.csv"))
    print(f"\nFound {len(csv_files)} translation file(s):")
    for f in csv_files:
        print(f"  - {f.name}")
    
    # Process files
    total = 0
    total += process_mgdata()
    total += process_1st_read()
    
    print("\n" + "=" * 60)
    print(f"Total replacements: {total}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run scripts\\rebuild.bat to rebuild the disc")
    print("2. Test translated-disc\\disc.gdi in emulator")


if __name__ == '__main__':
    main()
