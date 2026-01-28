#!/usr/bin/env python3
"""
Find short Japanese strings (names, menu items) in binary files
that were missed by the main extraction script.
Prepends missing entries to the CSV file.
"""

import os
import sys
import csv
from pathlib import Path

# Character names to search for (Japanese -> English)
CHARACTER_NAMES = {
    # Main characters - normal
    'バツ': 'Batsu',
    '烈': 'Batsu',
    'ひなた': 'Hinata',
    '京介': 'Kyosuke',
    'ロイ': 'Roy',
    'ティファニー': 'Tiffany',
    '将馬': 'Shoma',
    'ザキ': 'Zaki',
    'ロベルト': 'Roberto',
    '委員長': 'Chairperson',
    '巌': 'Gan',
    'いわ': 'Iwa',
    'なつ': 'Natsu',
    '英雄': 'Eiyu',
    '響子': 'Kyoko',
    '栄治': 'Eiji',
    '雷蔵': 'Raizo',
    '蘭': 'Ran',
    '兵': 'Hyo',
    '大悟': 'Daigo',
    'アキラ': 'Akira',
    'エッジ': 'Edge',
    'もも': 'Momo',
    '桃': 'Momo',
    'ユリカ': 'Yurika',
    '隼人': 'Hayato',
    '流': 'Nagare',
    '九郎': 'Kuro',
    'こずえ': 'Kozue',
    '雹': 'Hail',
    # With fullwidth spaces (menu format)
    'も　も': 'Momo',
    'バ　ツ': 'Batsu',
    'ひ　な　た': 'Hinata',
    'ロ　イ': 'Roy',
    'な　つ': 'Natsu',
    'い　わ': 'Iwa',
    'ザ　キ': 'Zaki',
    'しょう　ま': 'Shoma',
    '将　馬': 'Shoma',
    'きょう　すけ': 'Kyosuke',
    '京　介': 'Kyosuke',
    # Common menu items
    'はい': 'Yes',
    'いいえ': 'No',
    'は　い': 'Yes',
    'い　い　え': 'No',
    'もどる': 'Back',
    'やめる': 'Cancel',
    'けってい': 'Confirm',
    'つづける': 'Continue',
    'おわり': 'End',
    'すすむ': 'Next',
    'きめる': 'Decide',
    'たいせん': 'VS',
    'れんしゅう': 'Practice',
    # Schools
    '太陽学園': 'Taiyo Academy',
    '五輪高校': 'Gorin High',
    '外道高校': 'Gedo High',
    'ジャスティス学園': 'Justice Academy',
    '聖純Ｆ学院': 'Seijun Academy',
}


def search_bin_for_strings(bin_path: str, search_terms: dict) -> list:
    """Search binary file for specific strings and return found ones with offsets"""
    
    with open(bin_path, 'rb') as f:
        data = f.read()
    
    found = []
    
    for jp_text, en_text in search_terms.items():
        try:
            # Encode to Shift-JIS
            encoded = jp_text.encode('shift-jis')
            
            # Search for the pattern
            offset = 0
            while True:
                pos = data.find(encoded, offset)
                if pos == -1:
                    break
                
                # Check if it's null-terminated (standalone string)
                # Look for null byte before and after
                is_standalone = False
                
                # Check byte before (if not at start)
                if pos > 0:
                    byte_before = data[pos - 1]
                    # Should be null or another terminator
                    if byte_before == 0x00 or byte_before < 0x20:
                        # Check byte after
                        end_pos = pos + len(encoded)
                        if end_pos < len(data):
                            byte_after = data[end_pos]
                            if byte_after == 0x00 or byte_after < 0x20:
                                is_standalone = True
                
                if is_standalone:
                    found.append({
                        'japanese': jp_text,
                        'english': en_text,
                        'offset': pos,
                        'notes': 'Auto-found name/menu item'
                    })
                    # Only add first occurrence
                    break
                
                offset = pos + 1
                
        except Exception as e:
            print(f"  Could not encode '{jp_text}': {e}")
    
    return found


def load_existing_csv(csv_path: str) -> set:
    """Load existing Japanese strings from CSV"""
    existing = set()
    
    if not os.path.exists(csv_path):
        return existing
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        for row in reader:
            if row:
                existing.add(row[0])
    
    return existing


def prepend_to_csv(csv_path: str, new_entries: list):
    """Prepend new entries to the CSV file"""
    
    # Read existing content
    existing_content = []
    header = ['japanese', 'english', 'offset', 'notes']
    
    if os.path.exists(csv_path):
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, header)
            existing_content = list(reader)
    
    # Write back with new entries prepended
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        # Write new entries first
        for entry in new_entries:
            writer.writerow([
                entry['japanese'],
                entry['english'],
                f"0x{entry['offset']:08X}",
                entry['notes']
            ])
        
        # Write existing entries
        for row in existing_content:
            writer.writerow(row)


def main():
    if len(sys.argv) < 3:
        print("Usage: python find_missing_names.py <bin_file> <csv_file>")
        print()
        print("Example:")
        print("  python find_missing_names.py extracted-disc/1ST_READ.BIN translations/1st_read_strings.csv")
        return
    
    bin_path = sys.argv[1]
    csv_path = sys.argv[2]
    
    if not os.path.exists(bin_path):
        print(f"Error: Binary file not found: {bin_path}")
        return
    
    print(f"Searching for names/menu items in: {bin_path}")
    print(f"CSV file: {csv_path}")
    print()
    
    # Load existing entries
    existing = load_existing_csv(csv_path)
    print(f"Existing entries in CSV: {len(existing)}")
    
    # Search for strings
    print(f"Searching for {len(CHARACTER_NAMES)} known strings...")
    found = search_bin_for_strings(bin_path, CHARACTER_NAMES)
    
    print(f"Found {len(found)} strings in binary")
    
    # Filter out already existing
    new_entries = []
    for entry in found:
        if entry['japanese'] not in existing:
            new_entries.append(entry)
            print(f"  NEW: '{entry['japanese']}' -> '{entry['english']}' at 0x{entry['offset']:08X}")
        else:
            print(f"  EXISTS: '{entry['japanese']}' (skipping)")
    
    print()
    print(f"New entries to add: {len(new_entries)}")
    
    if new_entries:
        prepend_to_csv(csv_path, new_entries)
        print(f"Prepended {len(new_entries)} entries to {csv_path}")
    else:
        print("No new entries to add.")


if __name__ == '__main__':
    main()
