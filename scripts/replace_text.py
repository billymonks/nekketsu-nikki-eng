#!/usr/bin/env python3
"""
Text Replacement Script for Nekketsu Nikki Translation
Replaces Japanese text with English in game script files
"""

import os
import shutil
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_DIR = PROJECT_DIR / "extracted-afs"
MODIFIED_DIR = PROJECT_DIR / "modified-disc-files"


def replace_text_in_file(input_file: Path, output_file: Path, replacements: dict):
    """
    Replace text in a binary file using Shift-JIS encoding
    
    Args:
        input_file: Source file path
        output_file: Destination file path
        replacements: Dict of {japanese_text: english_text}
    """
    # Read original file
    with open(input_file, 'rb') as f:
        data = f.read()
    
    modified = data
    
    for jp_text, en_text in replacements.items():
        # Encode both texts as Shift-JIS
        jp_bytes = jp_text.encode('shift_jis')
        en_bytes = en_text.encode('shift_jis')
        
        if jp_bytes in modified:
            # Check length - warn if English is longer
            if len(en_bytes) > len(jp_bytes):
                print(f"WARNING: English text is {len(en_bytes) - len(jp_bytes)} bytes longer!")
                print(f"  JP ({len(jp_bytes)} bytes): {jp_text}")
                print(f"  EN ({len(en_bytes)} bytes): {en_text}")
                print("  This may cause issues if the game has fixed-size text buffers.")
            
            # Replace
            modified = modified.replace(jp_bytes, en_bytes)
            print(f"Replaced: {jp_text[:30]}... -> {en_text[:30]}...")
        else:
            print(f"NOT FOUND: {jp_text[:50]}...")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write modified file
    with open(output_file, 'wb') as f:
        f.write(modified)
    
    print(f"\nSaved to: {output_file}")


def main():
    # IMPORTANT: Line break format discovered!
    # The game requires a 2-byte character before / to trigger line breaks.
    # Use Japanese comma: 、/ (0x81-41-2F in Shift-JIS)
    # 
    # Format: "Line 1 text、/Line 2 text、/Line 3 text!"
    
    replacements = {
        "学園祭に参加するには、/いろいろ登録することがあるの。/まずは、プレイ人数を選択してね！":
        "To join the festival、/there's stuff to register、/Now, select player count!"
    }
    
    # Source and destination files
    # We modify files in-place in the modified-afs-contents folder
    MODIFIED_AFS_DIR = PROJECT_DIR / "modified-afs-contents"
    target_file = MODIFIED_AFS_DIR / "MGDATA" / "00000062"
    
    print("Nekketsu Nikki Text Replacement")
    print("=" * 50)
    print(f"Target: {target_file}")
    print("=" * 50)
    
    replace_text_in_file(target_file, target_file, replacements)
    
    print("\nDone! To test:")
    print("1. Copy the modified file back to the AFS archive")
    print("2. Rebuild the disc with buildgdi.exe")
    print("3. Test in emulator")


if __name__ == '__main__':
    main()
