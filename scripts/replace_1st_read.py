#!/usr/bin/env python3
"""
1ST_READ.BIN Text Replacement Script for Nekketsu Nikki Translation
Reads translations from CSV and applies them to the main executable.

This handles menu labels, UI text, and other strings stored in 1ST_READ.BIN
"""

import csv
import shutil
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_DIR / "extracted-disc"
MODIFIED_DIR = PROJECT_DIR / "modified-disc-files"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"

INPUT_FILE = EXTRACTED_DIR / "1ST_READ.BIN"
OUTPUT_FILE = MODIFIED_DIR / "1ST_READ.BIN"
CSV_FILE = TRANSLATIONS_DIR / "1st_read_menu.csv"


def load_translations(csv_path: Path) -> list:
    """
    Load translations from CSV file.
    
    Returns list of (japanese, english) tuples sorted by length (longest first)
    to prevent substring corruption during replacement.
    """
    translations = []
    
    if not csv_path.exists():
        print(f"ERROR: Translation file not found: {csv_path}")
        return translations
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = row.get('japanese', '').strip()
            en = row.get('english', '').strip()
            if jp and en:
                translations.append((jp, en))
    
    # Sort by Japanese text length (longest first) to prevent substring issues
    translations.sort(key=lambda x: len(x[0]), reverse=True)
    
    print(f"Loaded {len(translations)} translations from {csv_path.name}")
    return translations


def replace_text(input_path: Path, output_path: Path, translations: list) -> int:
    """
    Replace Japanese text with English in a binary file.
    
    Pads English text with spaces to match Japanese byte length.
    Returns count of successful replacements.
    """
    print(f"\nReading: {input_path}")
    with open(input_path, 'rb') as f:
        data = f.read()
    
    modified = data
    replaced_count = 0
    skipped_count = 0
    
    print(f"\nApplying {len(translations)} translations...")
    print("-" * 60)
    
    for jp_text, en_text in translations:
        try:
            jp_bytes = jp_text.encode('shift_jis')
            en_bytes = en_text.encode('shift_jis')
        except UnicodeEncodeError as e:
            print(f"  SKIP (encode error): {jp_text} -> {en_text}")
            skipped_count += 1
            continue
        
        if jp_bytes not in modified:
            print(f"  NOT FOUND: {jp_text}")
            skipped_count += 1
            continue
        
        # Pad English to match Japanese byte length
        if len(en_bytes) < len(jp_bytes):
            padding = len(jp_bytes) - len(en_bytes)
            en_bytes = en_bytes + b' ' * padding
        elif len(en_bytes) > len(jp_bytes):
            print(f"  WARNING: {jp_text} -> {en_text} is {len(en_bytes) - len(jp_bytes)} bytes too long! Truncating.")
            en_bytes = en_bytes[:len(jp_bytes)]
        
        # Count occurrences before replacement
        occurrences = modified.count(jp_bytes)
        
        # Replace all occurrences
        modified = modified.replace(jp_bytes, en_bytes)
        replaced_count += 1
        
        print(f"  [{replaced_count:2d}] {jp_text:12} -> {en_text:12} (x{occurrences})")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write modified file
    print(f"\nWriting: {output_path}")
    with open(output_path, 'wb') as f:
        f.write(modified)
    
    return replaced_count, skipped_count


def main():
    print("=" * 60)
    print("1ST_READ.BIN Translation Tool")
    print("=" * 60)
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"CSV:    {CSV_FILE}")
    
    # Check input file exists
    if not INPUT_FILE.exists():
        print(f"\nERROR: Input file not found: {INPUT_FILE}")
        print("Make sure you have extracted the disc files to extracted-disc/")
        return 1
    
    # Load translations
    translations = load_translations(CSV_FILE)
    if not translations:
        print("\nNo translations loaded. Exiting.")
        return 1
    
    # Apply translations
    replaced, skipped = replace_text(INPUT_FILE, OUTPUT_FILE, translations)
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Translations loaded: {len(translations)}")
    print(f"Successfully replaced: {replaced}")
    print(f"Skipped/not found: {skipped}")
    print(f"\nOutput file: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size:,} bytes")
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("=" * 60)
    print("1. Run scripts\\rebuild.bat to rebuild the disc image")
    print("2. Test translated-disc\\disc.gdi in emulator")
    
    return 0


if __name__ == '__main__':
    exit(main())
