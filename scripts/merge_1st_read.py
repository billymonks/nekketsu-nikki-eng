#!/usr/bin/env python3
"""
Merge 1st_read_menu.csv and 1st_read_moves.csv into 1st_read_strings.csv
Reports any conflicts (same Japanese, different English)
"""

import csv
import io
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TRANSLATIONS_DIR = PROJECT_DIR / "translations"


def load_csv(path: Path) -> dict:
    """Load translations from a CSV file."""
    translations = {}
    if not path.exists():
        return translations
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        jp = row.get('japanese', '')
        en = row.get('english', '')
        if jp:
            translations[jp] = {
                'english': en,
                'context': row.get('context', ''),
                'notes': row.get('notes', '')
            }
    return translations


def main():
    print("Merge Check: 1st_read files")
    print("=" * 60)
    
    # Load all three files
    strings_path = TRANSLATIONS_DIR / "1st_read_strings.csv"
    menu_path = TRANSLATIONS_DIR / "1st_read_menu.csv"
    moves_path = TRANSLATIONS_DIR / "1st_read_moves.csv"
    
    strings = load_csv(strings_path)
    menu = load_csv(menu_path)
    moves = load_csv(moves_path)
    
    print(f"1st_read_strings.csv: {len(strings)} entries")
    print(f"1st_read_menu.csv: {len(menu)} entries")
    print(f"1st_read_moves.csv: {len(moves)} entries")
    print()
    
    # Check for conflicts
    conflicts = []
    
    # Menu vs Strings
    for jp, data in menu.items():
        if jp in strings and strings[jp]['english'] and data['english']:
            if strings[jp]['english'] != data['english']:
                conflicts.append({
                    'japanese': jp,
                    'strings_en': strings[jp]['english'],
                    'other_en': data['english'],
                    'source': 'menu.csv'
                })
    
    # Moves vs Strings
    for jp, data in moves.items():
        if jp in strings and strings[jp]['english'] and data['english']:
            if strings[jp]['english'] != data['english']:
                conflicts.append({
                    'japanese': jp,
                    'strings_en': strings[jp]['english'],
                    'other_en': data['english'],
                    'source': 'moves.csv'
                })
    
    # Menu vs Moves
    for jp, data in menu.items():
        if jp in moves and moves[jp]['english'] and data['english']:
            if moves[jp]['english'] != data['english']:
                conflicts.append({
                    'japanese': jp,
                    'strings_en': data['english'],
                    'other_en': moves[jp]['english'],
                    'source': 'menu vs moves'
                })
    
    if conflicts:
        print(f"CONFLICTS FOUND: {len(conflicts)}")
        print("=" * 60)
        for c in conflicts:
            print(f"Japanese: {c['japanese']}")
            print(f"  strings.csv: {c['strings_en']}")
            print(f"  {c['source']}: {c['other_en']}")
            print()
    else:
        print("No conflicts found!")
    
    # Count what would be merged
    new_from_menu = [jp for jp in menu if jp not in strings]
    new_from_moves = [jp for jp in moves if jp not in strings]
    updates_from_menu = [jp for jp in menu if jp in strings and not strings[jp]['english'] and menu[jp]['english']]
    updates_from_moves = [jp for jp in moves if jp in strings and not strings[jp]['english'] and moves[jp]['english']]
    
    print()
    print("Merge summary:")
    print(f"  New entries from menu.csv: {len(new_from_menu)}")
    print(f"  New entries from moves.csv: {len(new_from_moves)}")
    print(f"  Empty entries in strings.csv that menu.csv can fill: {len(updates_from_menu)}")
    print(f"  Empty entries in strings.csv that moves.csv can fill: {len(updates_from_moves)}")
    
    return conflicts, strings, menu, moves, new_from_menu, new_from_moves, strings_path


def perform_merge(strings_path, strings, menu, moves, new_from_menu, new_from_moves):
    """Actually merge the entries into strings.csv"""
    
    # Read original file to preserve structure
    with open(strings_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    reader = csv.DictReader(io.StringIO(content))
    fieldnames = reader.fieldnames or ['japanese', 'english', 'offset', 'notes']
    rows = list(reader)
    
    added = 0
    
    # Add new entries from menu (strings.csv uses 'offset' not 'context')
    for jp in new_from_menu:
        data = menu[jp]
        rows.append({
            'japanese': jp,
            'english': data['english'],
            'offset': data.get('context', ''),  # menu uses 'context', strings uses 'offset'
            'notes': f"merged from menu.csv - {data['notes']}" if data['notes'] else "merged from menu.csv"
        })
        added += 1
        print(f"  + {jp} -> {data['english']} (from menu)")
    
    # Add new entries from moves
    for jp in new_from_moves:
        data = moves[jp]
        rows.append({
            'japanese': jp,
            'english': data['english'],
            'offset': data.get('context', ''),  # moves uses 'context', strings uses 'offset'
            'notes': f"merged from moves.csv - {data['notes']}" if data['notes'] else "merged from moves.csv"
        })
        added += 1
        print(f"  + {jp} -> {data['english']} (from moves)")
    
    # Write back
    with open(strings_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(rows)
    
    return added


if __name__ == '__main__':
    import sys
    
    result = main()
    conflicts, strings, menu, moves, new_from_menu, new_from_moves, strings_path = result
    
    if conflicts:
        print("\nResolve conflicts before merging!")
        exit(1)
    
    total_new = len(new_from_menu) + len(new_from_moves)
    if total_new == 0:
        print("\nNothing to merge.")
        exit(0)
    
    # Auto-merge if --merge flag or prompt
    if '--merge' in sys.argv:
        do_merge = True
    else:
        print(f"\nReady to merge {total_new} new entries. Proceed? [y/N] ", end='')
        response = input().strip().lower()
        do_merge = response in ('y', 'yes')
    
    if do_merge:
        print("\nMerging...")
        added = perform_merge(strings_path, strings, menu, moves, new_from_menu, new_from_moves)
        print(f"\nDone! Added {added} entries to 1st_read_strings.csv")
    else:
        print("\nMerge cancelled.")
