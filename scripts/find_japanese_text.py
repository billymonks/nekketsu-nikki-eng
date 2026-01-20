#!/usr/bin/env python3
"""
Japanese Text Finder for Dreamcast Game Files
Scans binary files for Shift-JIS encoded Japanese text

This script helps identify files containing translatable text by searching
for Japanese character sequences in binary files.
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Tuple


def is_shift_jis_char(b1: int, b2: int = None) -> bool:
    """Check if byte(s) represent a valid Shift-JIS character"""
    # Single-byte ASCII/half-width katakana
    if b2 is None:
        return (0x20 <= b1 <= 0x7E) or (0xA1 <= b1 <= 0xDF)
    
    # Double-byte Shift-JIS ranges
    # First byte: 0x81-0x9F or 0xE0-0xEF (extended: 0xF0-0xFC)
    # Second byte: 0x40-0x7E or 0x80-0xFC
    if (0x81 <= b1 <= 0x9F) or (0xE0 <= b1 <= 0xFC):
        if (0x40 <= b2 <= 0x7E) or (0x80 <= b2 <= 0xFC):
            return True
    return False


def is_hiragana_sjis(b1: int, b2: int) -> bool:
    """Check if double-byte is Hiragana (0x829F-0x82F1 in Shift-JIS)"""
    if b1 == 0x82:
        return 0x9F <= b2 <= 0xF1
    return False


def is_katakana_sjis(b1: int, b2: int) -> bool:
    """Check if double-byte is Katakana (0x8340-0x8396 in Shift-JIS)"""
    if b1 == 0x83:
        return 0x40 <= b2 <= 0x96
    return False


def find_japanese_strings(data: bytes, min_length: int = 4) -> List[Tuple[int, str]]:
    """
    Find Japanese text strings in binary data
    
    Returns list of (offset, decoded_string) tuples
    """
    results = []
    i = 0
    
    while i < len(data) - 1:
        # Look for start of Japanese text (double-byte character)
        b1 = data[i]
        
        # Skip if not a potential Shift-JIS lead byte
        if not ((0x81 <= b1 <= 0x9F) or (0xE0 <= b1 <= 0xFC)):
            i += 1
            continue
        
        # Try to extract a string starting here
        start = i
        string_bytes = bytearray()
        japanese_chars = 0
        
        while i < len(data) - 1:
            b1 = data[i]
            
            # Check for null terminator or control character
            if b1 == 0x00 or b1 < 0x20:
                break
            
            # Single-byte ASCII
            if 0x20 <= b1 <= 0x7E:
                string_bytes.append(b1)
                i += 1
                continue
            
            # Half-width katakana
            if 0xA1 <= b1 <= 0xDF:
                string_bytes.append(b1)
                japanese_chars += 1
                i += 1
                continue
            
            # Double-byte character
            if i + 1 < len(data):
                b2 = data[i + 1]
                if is_shift_jis_char(b1, b2):
                    string_bytes.extend([b1, b2])
                    if is_hiragana_sjis(b1, b2) or is_katakana_sjis(b1, b2):
                        japanese_chars += 1
                    elif (0x81 <= b1 <= 0x9F) or (0xE0 <= b1 <= 0xEF):
                        # Likely kanji or other Japanese character
                        japanese_chars += 1
                    i += 2
                    continue
            
            break
        
        # Check if we found a valid Japanese string
        if len(string_bytes) >= min_length and japanese_chars >= 2:
            try:
                decoded = bytes(string_bytes).decode('shift-jis', errors='replace')
                if len(decoded) >= min_length:
                    results.append((start, decoded))
            except:
                pass
        
        if i == start:
            i += 1
    
    return results


def scan_file(filepath: Path, min_length: int = 4, max_results: int = 100) -> List[Tuple[int, str]]:
    """Scan a file for Japanese text strings"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        
        results = find_japanese_strings(data, min_length)
        return results[:max_results]
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return []


def scan_directory(dirpath: Path, extensions: List[str] = None, min_length: int = 4):
    """Scan all files in directory for Japanese text"""
    if extensions is None:
        extensions = ['.bin', '.dat', '.afs', '']  # Include files without extension
    
    results = {}
    
    for root, dirs, files in os.walk(dirpath):
        for filename in files:
            filepath = Path(root) / filename
            ext = filepath.suffix.lower()
            
            if extensions and ext not in extensions and '' not in extensions:
                continue
            
            strings = scan_file(filepath, min_length, max_results=50)
            if strings:
                results[filepath] = strings
    
    return results


def main():
    print("=" * 60)
    print("Japanese Text Finder for Dreamcast Games")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <file_or_directory> [min_string_length]")
        print()
        print("Examples:")
        print(f"  {sys.argv[0]} extracted-disc/3SYS.BIN")
        print(f"  {sys.argv[0]} extracted-afs/WMENU/ 6")
        return
    
    target = Path(sys.argv[1])
    min_length = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    
    if not target.exists():
        print(f"Error: {target} does not exist")
        return
    
    if target.is_file():
        print(f"Scanning file: {target}")
        print(f"Minimum string length: {min_length}")
        print("-" * 60)
        
        strings = scan_file(target, min_length, max_results=200)
        
        if strings:
            print(f"Found {len(strings)} Japanese strings:")
            print()
            for offset, text in strings:
                # Clean up for display
                display_text = text[:80] + "..." if len(text) > 80 else text
                display_text = display_text.replace('\n', '\\n').replace('\r', '\\r')
                print(f"  0x{offset:08X}: {display_text}")
        else:
            print("No Japanese text found.")
    
    elif target.is_dir():
        print(f"Scanning directory: {target}")
        print(f"Minimum string length: {min_length}")
        print("-" * 60)
        
        results = scan_directory(target, min_length=min_length)
        
        if results:
            print(f"Found Japanese text in {len(results)} files:")
            print()
            for filepath, strings in sorted(results.items()):
                rel_path = filepath.relative_to(target) if filepath.is_relative_to(target) else filepath
                print(f"\n{rel_path} ({len(strings)} strings)")
                for offset, text in strings[:5]:  # Show first 5 strings per file
                    display_text = text[:60] + "..." if len(text) > 60 else text
                    display_text = display_text.replace('\n', '\\n').replace('\r', '\\r')
                    print(f"    0x{offset:08X}: {display_text}")
                if len(strings) > 5:
                    print(f"    ... and {len(strings) - 5} more")
        else:
            print("No Japanese text found.")


if __name__ == '__main__':
    main()
