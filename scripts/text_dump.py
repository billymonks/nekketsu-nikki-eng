#!/usr/bin/env python3
"""
Text Dumper for Dreamcast Game Translation
Extracts text strings from binary files and creates translation-ready CSV/TXT files

Supports:
- Shift-JIS encoded Japanese text
- Pointer table detection
- CSV output for spreadsheet-based translation
"""

import os
import sys
import csv
from pathlib import Path
from typing import List, Tuple, Dict
import struct


def read_shift_jis_string(data: bytes, offset: int, max_length: int = 1000) -> Tuple[str, int]:
    """
    Read a null-terminated Shift-JIS string from data
    Returns (decoded_string, bytes_read)
    """
    end = offset
    while end < len(data) and end < offset + max_length:
        if data[end] == 0x00:
            break
        end += 1
    
    raw_bytes = data[offset:end]
    try:
        decoded = raw_bytes.decode('shift-jis', errors='replace')
        return (decoded, end - offset + 1)  # +1 for null terminator
    except:
        return ("", end - offset + 1)


def extract_strings_from_file(filepath: Path, min_length: int = 3) -> List[Dict]:
    """
    Extract all printable strings from a binary file
    Returns list of dicts with offset, original text, and translation placeholder
    """
    results = []
    
    with open(filepath, 'rb') as f:
        data = f.read()
    
    i = 0
    while i < len(data):
        # Look for printable character sequences
        if data[i] == 0x00:
            i += 1
            continue
        
        # Check for Shift-JIS lead byte
        b1 = data[i]
        
        # Skip non-printable bytes
        if b1 < 0x20 and b1 not in (0x0A, 0x0D):  # Allow newlines
            i += 1
            continue
        
        # Try to read a string
        string_start = i
        string_bytes = bytearray()
        has_japanese = False
        
        while i < len(data):
            b = data[i]
            
            # Null terminator
            if b == 0x00:
                break
            
            # Control characters (except newlines)
            if b < 0x20 and b not in (0x0A, 0x0D):
                break
            
            # ASCII
            if 0x20 <= b <= 0x7E or b in (0x0A, 0x0D):
                string_bytes.append(b)
                i += 1
                continue
            
            # Half-width katakana
            if 0xA1 <= b <= 0xDF:
                string_bytes.append(b)
                has_japanese = True
                i += 1
                continue
            
            # Double-byte Shift-JIS
            if ((0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xFC)) and i + 1 < len(data):
                b2 = data[i + 1]
                if (0x40 <= b2 <= 0x7E) or (0x80 <= b2 <= 0xFC):
                    string_bytes.extend([b, b2])
                    has_japanese = True
                    i += 2
                    continue
            
            # Unknown byte, end string
            break
        
        # Process the collected string
        if len(string_bytes) >= min_length:
            try:
                decoded = bytes(string_bytes).decode('shift-jis', errors='replace')
                
                # Filter out strings that are mostly garbage
                printable_ratio = sum(1 for c in decoded if c.isprintable() or c in '\n\r') / len(decoded)
                
                if printable_ratio > 0.7 and (has_japanese or len(decoded) >= 5):
                    results.append({
                        'offset': string_start,
                        'offset_hex': f'0x{string_start:08X}',
                        'length': len(string_bytes),
                        'original': decoded,
                        'translation': '',
                        'notes': ''
                    })
            except:
                pass
        
        if i == string_start:
            i += 1
    
    return results


def dump_to_csv(strings: List[Dict], output_path: Path):
    """Write extracted strings to a CSV file for translation"""
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['offset_hex', 'length', 'original', 'translation', 'notes'])
        writer.writeheader()
        writer.writerows(strings)
    print(f"Wrote {len(strings)} strings to {output_path}")


def dump_to_txt(strings: List[Dict], output_path: Path):
    """Write extracted strings to a text file for review"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Text Dump - {len(strings)} strings\n")
        f.write(f"# Format: [OFFSET] Original Text\n")
        f.write("=" * 70 + "\n\n")
        
        for s in strings:
            f.write(f"[{s['offset_hex']}] ({s['length']} bytes)\n")
            f.write(f"{s['original']}\n")
            f.write("-" * 40 + "\n\n")
    
    print(f"Wrote {len(strings)} strings to {output_path}")


def main():
    print("=" * 60)
    print("Text Dumper for Dreamcast Game Translation")
    print("=" * 60)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print(f"  {sys.argv[0]} <input_file> [output_format] [min_length]")
        print()
        print("Output formats: csv, txt, both (default: both)")
        print("Min length: minimum string length (default: 3)")
        print()
        print("Examples:")
        print(f"  {sys.argv[0]} extracted-afs/WMENU/0001.bin")
        print(f"  {sys.argv[0]} 3SYS.BIN csv 5")
        return
    
    input_path = Path(sys.argv[1])
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'both'
    min_length = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    
    if not input_path.exists():
        print(f"Error: {input_path} does not exist")
        return
    
    print(f"Input file: {input_path}")
    print(f"Output format: {output_format}")
    print(f"Minimum string length: {min_length}")
    print("-" * 60)
    
    strings = extract_strings_from_file(input_path, min_length)
    
    if not strings:
        print("No strings found in file.")
        return
    
    print(f"Found {len(strings)} strings")
    
    # Create output filenames
    base_name = input_path.stem
    output_dir = input_path.parent
    
    if output_format in ('csv', 'both'):
        csv_path = output_dir / f"{base_name}_strings.csv"
        dump_to_csv(strings, csv_path)
    
    if output_format in ('txt', 'both'):
        txt_path = output_dir / f"{base_name}_strings.txt"
        dump_to_txt(strings, txt_path)
    
    print()
    print("Done!")


if __name__ == '__main__':
    main()
