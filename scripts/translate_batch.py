#!/usr/bin/env python3
"""
Batch translation helper for Nekketsu Nikki.
Reads untranslated strings and outputs translations.
"""

import csv
import io
from pathlib import Path

# Common translation patterns
TRANSLATIONS = {
    # Player stats
    "!c03体力!c07": "!c03HP!c07",
    "!c03攻撃力!c07": "!c03ATK!c07",
    "!c03根性!c07": "!c03GUTS!c07",
    "!c03潜在能力!c07": "!c03Potential!c07",
    "!c03パラメータ!c07": "!c03Parameters!c07",
    
    # Common phrases
    "学園祭": "school festival",
    "キャンプファイアー": "campfire",
    "パートナー": "Partner",
    "ジャスティス学園": "Justice Academy",
    
    # UI messages
    "の対戦よ！": " battle!",
    "と話します": "Talk to ",
    "に勝った！": " wins!",
    "になった！": " joined!",
    
    # Numbers
    "１": "1", "２": "2", "３": "3", "４": "4", "５": "5",
    "６": "6", "７": "7", "８": "8", "９": "9", "０": "0",
}

def translate_string(jp_text):
    """Apply common translations and return translated text."""
    result = jp_text
    
    # Apply pattern replacements
    for jp, en in TRANSLATIONS.items():
        result = result.replace(jp, en)
    
    return result if result != jp_text else ""


def main():
    PROJECT_DIR = Path(__file__).parent.parent
    csv_path = PROJECT_DIR / "translations" / "mgdata_62_63.csv"
    
    # Load CSV
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    
    # Count untranslated
    untranslated = [r for r in rows if not r.get('english')]
    print(f"Total strings: {len(rows)}")
    print(f"Untranslated: {len(untranslated)}")
    print(f"Translated: {len(rows) - len(untranslated)}")
    
    # Show sample untranslated
    print("\nFirst 20 untranslated strings:")
    for i, row in enumerate(untranslated[:20]):
        jp = row['japanese'][:50]
        print(f"  {i+1}. {jp}...")


if __name__ == '__main__':
    main()
