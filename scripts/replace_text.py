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


def replace_text_in_file(input_file: Path, output_file: Path, replacements: dict, pad_to_length=True):
    """
    Replace text in a binary file using Shift-JIS encoding
    
    Args:
        input_file: Source file path
        output_file: Destination file path
        replacements: Dict of {japanese_text: english_text}
        pad_to_length: If True, pad English text with spaces to match Japanese length
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
            # Pad or truncate to match original length
            if pad_to_length:
                if len(en_bytes) < len(jp_bytes):
                    # Pad with spaces to match length
                    padding = len(jp_bytes) - len(en_bytes)
                    en_bytes = en_bytes + b' ' * padding
                    print(f"Padded with {padding} spaces")
                elif len(en_bytes) > len(jp_bytes):
                    print(f"WARNING: English is {len(en_bytes) - len(jp_bytes)} bytes LONGER - truncating!")
                    en_bytes = en_bytes[:len(jp_bytes)]
            
            # Replace
            modified = modified.replace(jp_bytes, en_bytes)
            print(f"Replaced ({len(jp_bytes)}→{len(en_bytes)} bytes): {jp_text[:30]}...")
        else:
            print(f"NOT FOUND: {jp_text[:50]}...")
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write modified file
    with open(output_file, 'wb') as f:
        f.write(modified)
    
    print(f"\nSaved to: {output_file}")


def main():
    # IMPORTANT DISCOVERIES:
    # 1. Line breaks: Use Japanese comma before / → 、/ (0x81-41-2F)
    # 2. Color codes: !c02=green, !c04=orange, !c07=white, etc.
    # 3. File format: MUST maintain exact byte length or file corrupts!
    #    - Pad shorter English with spaces
    #    - Keep color codes if possible
    
    replacements = {
        # Intro dialog (this one has same-ish length so it works)
        "学園祭に参加するには、/いろいろ登録することがあるの。/まずは、プレイ人数を選択してね！":
        "To join the festival、/there's stuff to register、/Now, select player count!",
        
        # Player selection - ! must be at EVEN byte position!
        # Use fullwidth space (2 bytes) to maintain even alignment with nice spacing
        "!c02人間１人!c07　＋　!c04ＣＰＵ１体!c07の対戦よ！":
        "!c021 Human !c07　＋　!c041 CPU !c07 battle!",
        
        "!c02人間１人!c07　＋　!c04ＣＰＵ２体!c07の対戦よ！":
        "!c021 Human !c07　＋　!c042 CPUs!c07 battle!",
        
        "!c02人間１人!c07　＋　!c04ＣＰＵ３体!c07の対戦よ！":
        "!c021 Human !c07　＋　!c043 CPUs!c07 battle!",
        
        "!c03人間２人!c07の対戦よ！":
        "!c032 Humans!c07 battle!",
        
        "!c03人間２人!c07　＋　!c04ＣＰＵ１体!c07の対戦よ！":
        "!c032 Humans!c07　＋　!c041 CPU !c07 battle!",
        
        "!c03人間２人!c07　＋　!c04ＣＰＵ２体!c07の対戦よ！":
        "!c032 Humans!c07　＋　!c042 CPUs!c07 battle!",
        
        "!c01人間３人!c07の対戦よ！":
        "!c013 Humans!c07 battle!",
        
        "!c01人間３人!c07　＋　!c04ＣＰＵ１体!c07の対戦よ！":
        "!c013 Humans!c07　＋　!c041 CPU !c07 battle!",
        
        "!c05人間４人!c07の対戦よ！":
        "!c054 Humans!c07 battle!",
    }
    
    # Source and destination files
    MODIFIED_AFS_DIR = PROJECT_DIR / "modified-afs-contents"
    target_file = MODIFIED_AFS_DIR / "MGDATA" / "00000062"
    
    print("Nekketsu Nikki Text Replacement")
    print("=" * 50)
    print(f"Target: {target_file}")
    print("=" * 50)
    
    replace_text_in_file(target_file, target_file, replacements)
    
    print("\nDone! To test:")
    print("1. Run scripts\\rebuild.bat")
    print("2. Test translated-disc\\disc.gdi in emulator")


if __name__ == '__main__':
    main()
