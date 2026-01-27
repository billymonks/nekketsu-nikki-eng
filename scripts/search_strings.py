#!/usr/bin/env python3
"""Search for specific Japanese strings in binary files"""

import os
import sys

search_patterns = {
    'の目的': bytes.fromhex('82cc96da9349'),
    'EDITキャラを作るには': bytes.fromhex('45444954834c8383838982f08dec82e982c982cd'),
    'MAPの説明': bytes.fromhex('4d415082cc90e096be'),
    '戦闘について': bytes.fromhex('90ed93ac82c982c282a282c4'),
    'ジャスキャラについて': bytes.fromhex('835783838358834c8383838982c982c282a282c4'),
}

dirs_to_search = ['extracted-afs', 'extracted-disc']

print("Searching for menu strings...")
print("=" * 60)

found_any = False

for dir_path in dirs_to_search:
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        continue
    
    print(f"\nSearching in: {dir_path}")
    
    for root, dirs, files in os.walk(dir_path):
        for filename in files:
            filepath = os.path.join(root, filename)
            try:
                with open(filepath, 'rb') as f:
                    data = f.read()
                
                for name, pattern in search_patterns.items():
                    if pattern in data:
                        offset = data.find(pattern)
                        print(f'  Found "{name}" in {filepath} at offset 0x{offset:08X}')
                        found_any = True
            except Exception as e:
                pass

if not found_any:
    print("\nNo matches found for the specific menu strings.")
    print("The text may be stored differently (e.g., with control characters between bytes)")
