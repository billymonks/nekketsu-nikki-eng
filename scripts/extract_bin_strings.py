#!/usr/bin/env python3
"""
Extract Japanese strings from binary files to CSV for translation.
Outputs a CSV with "japanese" and blank "english" columns.
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Tuple


def is_shift_jis_char(b1: int, b2: int = None) -> bool:
    """Check if byte(s) represent a valid Shift-JIS character"""
    if b2 is None:
        return (0x20 <= b1 <= 0x7E) or (0xA1 <= b1 <= 0xDF)
    
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


def is_fullwidth_ascii(b1: int, b2: int) -> bool:
    """Check if double-byte is fullwidth ASCII (0x8140-0x8197 range)"""
    if b1 == 0x82:
        return 0x4F <= b2 <= 0x58  # Fullwidth 0-9
    if b1 == 0x82:
        return 0x60 <= b2 <= 0x79  # Fullwidth A-Z
    if b1 == 0x82:
        return 0x81 <= b2 <= 0x9A  # Fullwidth a-z
    return False


def extract_strings(data: bytes, min_length: int = 3, min_japanese: int = 1) -> List[Tuple[int, str]]:
    """
    Extract Japanese text strings from binary data.
    
    Args:
        data: Binary data to scan
        min_length: Minimum string length to include
        min_japanese: Minimum number of Japanese characters required
    
    Returns:
        List of (offset, decoded_string) tuples
    """
    results = []
    i = 0
    
    while i < len(data) - 1:
        b1 = data[i]
        
        # Look for potential start of Japanese text
        # Double-byte Shift-JIS lead byte or printable ASCII
        if not ((0x81 <= b1 <= 0x9F) or (0xE0 <= b1 <= 0xFC) or (0x20 <= b1 <= 0x7E)):
            i += 1
            continue
        
        # Try to extract a string starting here
        start = i
        string_bytes = bytearray()
        japanese_chars = 0
        
        while i < len(data):
            b1 = data[i]
            
            # Check for null terminator or control character
            if b1 == 0x00 or (b1 < 0x20 and b1 not in (0x0A, 0x0D)):  # Allow newlines
                break
            
            # Single-byte ASCII (including space)
            if 0x20 <= b1 <= 0x7E:
                string_bytes.append(b1)
                i += 1
                continue
            
            # Newline characters
            if b1 in (0x0A, 0x0D):
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
                    # Count as Japanese if hiragana, katakana, or kanji
                    if is_hiragana_sjis(b1, b2) or is_katakana_sjis(b1, b2):
                        japanese_chars += 1
                    elif (0x81 <= b1 <= 0x9F) or (0xE0 <= b1 <= 0xEF):
                        # Likely kanji or other Japanese character
                        japanese_chars += 1
                    i += 2
                    continue
            
            break
        
        # Check if we found a valid Japanese string
        if len(string_bytes) >= min_length and japanese_chars >= min_japanese:
            try:
                decoded = bytes(string_bytes).decode('shift-jis', errors='replace')
                # Clean up the string
                decoded = decoded.strip()
                if len(decoded) >= min_length:
                    # Skip strings that are mostly garbage
                    if not is_garbage_string(decoded):
                        results.append((start, decoded))
            except:
                pass
        
        if i == start:
            i += 1
    
    return results


def is_garbage_string(s: str) -> bool:
    """Check if a string is likely garbage/binary data"""
    # Count replacement characters
    if '\ufffd' in s:
        return True
    
    # Reject strings with regular ASCII letters/numbers/punctuation
    # Real Japanese game text uses fullwidth for these
    garbage_ascii = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.,;:!?()[]{}/<>\\|`~@#$%^&*-_=+\'"')
    
    for c in s:
        if c in garbage_ascii:
            return True
    
    # Count different character types
    hiragana = 0
    katakana = 0
    kanji = 0
    fullwidth_ascii = 0
    punctuation = 0
    garbage_chars = 0
    halfwidth_kana = 0
    spaces = 0
    
    for c in s:
        cp = ord(c)
        # Hiragana: U+3040-U+309F
        if 0x3040 <= cp <= 0x309F:
            hiragana += 1
        # Katakana: U+30A0-U+30FF
        elif 0x30A0 <= cp <= 0x30FF:
            katakana += 1
        # CJK Unified Ideographs (Kanji): U+4E00-U+9FFF
        elif 0x4E00 <= cp <= 0x9FFF:
            kanji += 1
        # Fullwidth ASCII: U+FF01-U+FF5E (fullwidth ! to ~)
        elif 0xFF01 <= cp <= 0xFF5E:
            fullwidth_ascii += 1
        # Japanese punctuation
        elif c in '。、！？「」『』（）・ー〜：；…―':
            punctuation += 1
        # Half-width katakana (often garbage in binary misreads)
        elif 0xFF61 <= cp <= 0xFF9F:
            halfwidth_kana += 1
        # Spaces (both regular and fullwidth)
        elif c == ' ' or c == '　':
            spaces += 1
        # Newlines
        elif c in '\r\n':
            pass
        else:
            garbage_chars += 1
    
    japanese_chars = hiragana + katakana + kanji
    
    # Reject if ANY half-width katakana (almost always binary garbage)
    if halfwidth_kana > 0:
        return True
    
    # Must have meaningful Japanese content
    if japanese_chars == 0 and fullwidth_ascii == 0:
        return True
    
    # Too many garbage/unusual characters
    if garbage_chars > 0:
        return True
    
    # Minimum content - at least 2 Japanese chars or fullwidth
    content_chars = japanese_chars + fullwidth_ascii
    if content_chars < 2:
        return True
    
    return False


def extract_to_csv(input_file: str, output_file: str, min_length: int = 3, min_japanese: int = 1):
    """Extract strings from a binary file and save to CSV"""
    
    print(f"Reading: {input_file}")
    with open(input_file, 'rb') as f:
        data = f.read()
    
    print(f"File size: {len(data):,} bytes")
    print(f"Extracting strings (min length: {min_length}, min Japanese chars: {min_japanese})...")
    
    strings = extract_strings(data, min_length, min_japanese)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_strings = []
    for offset, text in strings:
        if text not in seen:
            seen.add(text)
            unique_strings.append((offset, text))
    
    print(f"Found {len(strings)} strings ({len(unique_strings)} unique)")
    
    # Write to CSV
    print(f"Writing to: {output_file}")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['japanese', 'english', 'offset', 'notes'])
        for offset, text in unique_strings:
            writer.writerow([text, '', f'0x{offset:08X}', ''])
    
    print(f"Done! Wrote {len(unique_strings)} entries to CSV")


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_bin_strings.py <input_file> [output_csv] [min_length] [min_japanese]")
        print()
        print("Examples:")
        print("  python extract_bin_strings.py extracted-disc/1ST_READ.BIN")
        print("  python extract_bin_strings.py extracted-disc/1ST_READ.BIN translations/1st_read_strings.csv")
        print("  python extract_bin_strings.py extracted-disc/1ST_READ.BIN output.csv 4 2")
        return
    
    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: File not found: {input_file}")
        return
    
    # Default output filename
    if len(sys.argv) >= 3:
        output_file = sys.argv[2]
    else:
        base_name = Path(input_file).stem
        output_file = f"translations/{base_name}_strings.csv"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    
    min_length = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    min_japanese = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    
    extract_to_csv(input_file, output_file, min_length, min_japanese)


if __name__ == '__main__':
    main()
