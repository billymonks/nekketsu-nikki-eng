#!/usr/bin/env python3
"""
Extract Japanese text from Nekketsu Nikki game files for translation.
Outputs CSV files ready for translators to fill in.
"""

import csv
import re
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_DIR / "extracted-afs"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"


def extract_dialog_strings(file_path: Path) -> list:
    """
    Extract dialog strings from a game script file.
    
    Dialog format:
    - !pXXXX!eXX = character portrait/emotion
    - !cXX = color code
    - / = line break
    - @ = end of dialog block
    - !0 = player name placeholder
    
    Returns list of dicts with japanese, context info
    """
    with open(file_path, 'rb') as f:
        data = f.read()
    
    text = data.decode('shift_jis', errors='replace')
    
    strings = []
    
    # Pattern to find dialog blocks: !pXXXX!eXX followed by text until @
    # Also captures standalone color-coded text
    pattern = r'(!p[0-9a-fA-F]{4}!e[0-9]{2})([^@]+)@'
    
    matches = re.finditer(pattern, text)
    
    for match in matches:
        portrait_code = match.group(1)
        dialog_text = match.group(2).strip()
        
        # Skip empty or very short strings
        if len(dialog_text) < 2:
            continue
        
        # Skip if it's mostly control codes
        clean_text = re.sub(r'!c[0-9]{2}', '', dialog_text)
        clean_text = re.sub(r'!p[0-9a-fA-F]{4}', '', clean_text)
        clean_text = re.sub(r'!e[0-9]{2}', '', clean_text)
        clean_text = re.sub(r'!0', '', clean_text)
        clean_text = clean_text.replace('/', '').replace('　', '').strip()
        
        if len(clean_text) < 2:
            continue
        
        # Check if it contains Japanese characters
        has_japanese = any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in clean_text)
        
        if has_japanese:
            strings.append({
                'japanese': dialog_text,
                'portrait': portrait_code,
                'context': f'Portrait: {portrait_code}'
            })
    
    return strings


def extract_colored_strings(file_path: Path) -> list:
    """
    Extract color-coded strings (like player selection menu).
    These start with !cXX and may not have portrait codes.
    """
    with open(file_path, 'rb') as f:
        data = f.read()
    
    text = data.decode('shift_jis', errors='replace')
    
    strings = []
    
    # Find color-coded strings that end with @ but don't start with !p
    # These are typically menu items
    pattern = r'(?<![!p0-9a-fA-F])(!c[0-9]{2}[^@]{5,})@'
    
    matches = re.finditer(pattern, text)
    seen = set()
    
    for match in matches:
        colored_text = match.group(1).strip()
        
        if colored_text in seen:
            continue
        seen.add(colored_text)
        
        # Check if contains Japanese
        has_japanese = any('\u3040' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in colored_text)
        
        if has_japanese:
            strings.append({
                'japanese': colored_text,
                'context': 'Color-coded menu/UI text'
            })
    
    return strings


def write_csv(strings: list, output_path: Path, include_english=True):
    """Write extracted strings to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        if include_english:
            fieldnames = ['japanese', 'english', 'context', 'notes']
        else:
            fieldnames = ['japanese', 'context', 'notes']
        
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        
        for s in strings:
            row = {
                'japanese': s['japanese'],
                'context': s.get('context', ''),
                'notes': s.get('notes', '')
            }
            if include_english:
                row['english'] = ''
            writer.writerow(row)
    
    print(f"Wrote {len(strings)} strings to {output_path}")


def deduplicate_strings(strings: list) -> list:
    """Remove duplicate Japanese strings, keeping first occurrence."""
    seen = set()
    unique = []
    for s in strings:
        jp = s['japanese']
        if jp not in seen:
            seen.add(jp)
            unique.append(s)
    return unique


def main():
    print("Nekketsu Nikki Text Extractor")
    print("=" * 60)
    
    TRANSLATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Extract from MGDATA/00000062 (female protagonist)
    file_62 = EXTRACTED_DIR / "MGDATA" / "00000062"
    if file_62.exists():
        print(f"\nProcessing {file_62}...")
        
        # Extract dialog strings
        dialogs = extract_dialog_strings(file_62)
        print(f"  Found {len(dialogs)} dialog strings")
        
        # Extract color-coded strings
        colored = extract_colored_strings(file_62)
        print(f"  Found {len(colored)} color-coded strings")
        
        # Combine and deduplicate
        all_strings = dialogs + colored
        all_strings = deduplicate_strings(all_strings)
        print(f"  Total unique strings: {len(all_strings)}")
        
        # Write to CSV
        output_path = TRANSLATIONS_DIR / "mgdata_62_extracted.csv"
        write_csv(all_strings, output_path)
    
    # Extract from MGDATA/00000063 (male protagonist)
    file_63 = EXTRACTED_DIR / "MGDATA" / "00000063"
    if file_63.exists():
        print(f"\nProcessing {file_63}...")
        
        dialogs = extract_dialog_strings(file_63)
        print(f"  Found {len(dialogs)} dialog strings")
        
        colored = extract_colored_strings(file_63)
        print(f"  Found {len(colored)} color-coded strings")
        
        all_strings = dialogs + colored
        all_strings = deduplicate_strings(all_strings)
        print(f"  Total unique strings: {len(all_strings)}")
        
        output_path = TRANSLATIONS_DIR / "mgdata_63_extracted.csv"
        write_csv(all_strings, output_path)
    
    print("\n" + "=" * 60)
    print("Extraction complete!")
    print(f"CSV files saved to: {TRANSLATIONS_DIR}")
    print("\nNext steps:")
    print("1. Open the CSV files in Excel/Google Sheets")
    print("2. Fill in the 'english' column with translations")
    print("3. Rename files (e.g., mgdata_62_extracted.csv -> mgdata_62_dialog.csv)")
    print("4. Run: python scripts/replace_text.py")


if __name__ == '__main__':
    main()
