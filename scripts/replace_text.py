#!/usr/bin/env python3
"""
Text Replacement Script for Nekketsu Nikki Translation
Reads translations from CSV files and applies them to game script files.

Handles:
- MGDATA files (00000062, 00000063) - main game dialogue
- 1ST_READ.BIN - menu labels and UI text
"""

import csv
import shutil
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).parent.parent
EXTRACTED_AFS_DIR = PROJECT_DIR / "extracted-afs"
EXTRACTED_DISC_DIR = PROJECT_DIR / "extracted-disc"
MODIFIED_AFS_DIR = PROJECT_DIR / "modified-afs-contents"
MODIFIED_DISC_DIR = PROJECT_DIR / "modified-disc-files"
TRANSLATIONS_DIR = PROJECT_DIR / "translations"
REPLACE_REPORTS_DIR = TRANSLATIONS_DIR / "replace_reports"


def load_translations_from_csv(csv_path: Path) -> dict:
    """
    Load translations from a CSV file.
    
    Supports two formats:
    - Source CSVs: japanese,english,context,notes
    - MGDATA CSVs: Japanese,English,offset
    
    Returns dict of {japanese_text: english_text}
    """
    translations = {}

    if not csv_path.exists():
        print(f"WARNING: Translation file not found: {csv_path}")
        return translations

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Support both column name conventions
            jp = row.get('Japanese', row.get('japanese', ''))
            en = row.get('English', row.get('english', ''))
            if jp and en:
                translations[jp] = en

    print(f"Loaded {len(translations)} translations from {csv_path.name}")
    return translations



def replace_text_in_file(input_file: Path, output_file: Path, replacements: dict, pad_to_length=True, pad_char=b' '):
    """
    Replace text in a binary file using Shift-JIS encoding.
    Pads English text to match Japanese byte length.
    
    If there are multiple consecutive null bytes after the string, the English
    text can expand into that space (keeping at least 1 null terminator).
    This gives extra room for longer translations before truncating.
    
    Args:
        pad_char: Byte to use for padding. Default is space (b' ').
                  Use b'\x00' for null padding (good for menu/UI text).
    
    IMPORTANT: Replacements are sorted by length (longest first) to prevent
    shorter substrings from corrupting longer strings during replacement.
    """
    with open(input_file, 'rb') as f:
        data = f.read()
    
    modified = bytearray(data)
    replaced_count = 0
    issues = []
    
    # Sort by Japanese text length (longest first) to prevent substring corruption
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    for jp_text, en_text in sorted_replacements:
        jp_bytes = jp_text.encode('shift_jis')
        en_bytes = en_text.encode('shift_jis')

        fmt_problem = has_malformed_format_code(en_text)
        if fmt_problem:
            issues.append({
                'issue': 'BAD_FORMAT_CODE',
                'offset': '',
                'detail': fmt_problem,
                'japanese': jp_text,
                'english': en_text,
            })
        
        found = False
        occurrences = 0
        truncated = False
        pos = 0
        
        while True:
            idx = bytes(modified).find(jp_bytes, pos)
            if idx == -1:
                break
            
            # Count trailing null bytes after the Japanese text
            text_end = idx + len(jp_bytes)
            null_count = 0
            while text_end + null_count < len(modified) and modified[text_end + null_count] == 0x00:
                null_count += 1
            
            # Available space: JP bytes + trailing nulls minus 1 (keep at least 1 null)
            if null_count > 0:
                available = len(jp_bytes) + null_count - 1
            else:
                available = len(jp_bytes)
            
            if pad_to_length:
                if len(en_bytes) <= len(jp_bytes):
                    # English fits within original JP space - pad normally
                    padded = en_bytes + pad_char * (len(jp_bytes) - len(en_bytes))
                    modified[idx:idx + len(jp_bytes)] = padded
                elif len(en_bytes) <= available:
                    # English is longer than JP but fits using trailing nulls
                    total_span = len(jp_bytes) + null_count
                    remaining = total_span - len(en_bytes)
                    padded = en_bytes + b'\x00' * remaining
                    modified[idx:idx + total_span] = padded
                else:
                    # Doesn't fit even with trailing nulls - truncate
                    over = len(en_bytes) - available
                    print(f"WARNING: English is {over} bytes LONGER than available space - truncating!")
                    truncated = True
                    issues.append({
                        'issue': 'TRUNCATED',
                        'offset': f"0x{idx:X}",
                        'detail': f"English {len(en_bytes)}B > available {available}B (over by {over}B)",
                        'japanese': jp_text,
                        'english': en_text,
                    })
                    modified[idx:idx + len(jp_bytes)] = en_bytes[:len(jp_bytes)]
            else:
                modified[idx:idx + len(jp_bytes)] = en_bytes[:len(jp_bytes)]
            
            pos = idx + max(len(jp_bytes), len(en_bytes))
            occurrences += 1
            found = True
        
        if found:
            replaced_count += 1
            print(f"  [{replaced_count}] {jp_text[:25]}... -> {en_text[:25]}... ({occurrences} occurrences)")
        else:
            print(f"  NOT FOUND: {jp_text[:40]}...")
            issues.append({
                'issue': 'NOT_FOUND',
                'offset': '',
                'detail': 'Japanese text not found in binary',
                'japanese': jp_text,
                'english': en_text,
            })
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'wb') as f:
        f.write(modified)
    
    return replaced_count, issues


def replace_null_terminated_strings(input_file: Path, output_file: Path, replacements: dict, pad_to_length=True, pad_char=b' '):
    """
    Replace text in a binary file, but ONLY when it appears as a null-terminated string.
    
    This is safer for short strings (like single kanji) that might accidentally
    match binary data like pointers or code. By requiring null terminators,
    we ensure we're only replacing actual string data.
    
    If there are multiple consecutive null bytes after the string, the English
    text can expand into that space (keeping at least 1 null terminator).
    This gives extra room for longer translations before truncating.
    
    Args:
        pad_char: Byte to use for padding. Default is space (b' ').
    
    Matches patterns like:
    - \x00<text>\x00  (null on both sides - middle/end of string array)
    - <text>\x00 where preceded by non-string data (first item in array)
    """
    with open(input_file, 'rb') as f:
        data = f.read()
    
    modified = bytearray(data)
    replaced_count = 0
    issues = []
    
    # Sort by Japanese text length (longest first) to prevent substring corruption
    sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
    
    for jp_text, en_text in sorted_replacements:
        jp_bytes = jp_text.encode('shift_jis')
        en_bytes = en_text.encode('shift_jis')
        
        found = False
        occurrences = 0
        
        # Search for <text>\x00 pattern
        search_pattern = jp_bytes + b'\x00'
        
        pos = 0
        while True:
            idx = bytes(modified).find(search_pattern, pos)
            if idx == -1:
                break
            
            # Determine if this is a valid string location
            prev_byte = modified[idx - 1] if idx > 0 else 0
            is_null_preceded = (prev_byte == 0x00)
            is_valid_start = (prev_byte < 0x80)  # ASCII or control char before
            
            if not is_valid_start:
                pos = idx + 1
                continue
            
            # Count trailing null bytes after the string (including the terminator)
            text_end = idx + len(jp_bytes)
            null_count = 0
            while text_end + null_count < len(modified) and modified[text_end + null_count] == 0x00:
                null_count += 1
            
            # Available space: the Japanese text bytes + trailing nulls minus 1 (keep at least 1 null)
            available = len(jp_bytes) + max(0, null_count - 1)
            
            if pad_to_length:
                if len(en_bytes) <= available:
                    # Fits: pad with pad_char to fill original jp_bytes, rest stays null
                    if len(en_bytes) < len(jp_bytes):
                        padded = en_bytes + pad_char * (len(jp_bytes) - len(en_bytes))
                    else:
                        # English is longer than jp but fits in available space
                        # Write en_bytes, then null-fill the rest up to original total span
                        total_span = len(jp_bytes) + null_count
                        remaining = total_span - len(en_bytes)
                        padded = en_bytes + b'\x00' * remaining
                        # Replace the full span (text + all nulls)
                        modified[idx:idx + total_span] = padded
                        pos = idx + total_span
                        occurrences += 1
                        found = True
                        continue
                    # Standard case: replace just the text portion
                    modified[idx:idx + len(jp_bytes)] = padded
                else:
                    over = len(en_bytes) - available
                    print(f"WARNING: English is {over} bytes LONGER than available space - truncating!")
                    issues.append({
                        'issue': 'TRUNCATED',
                        'offset': f"0x{idx:X}",
                        'detail': f"English {len(en_bytes)}B > available {available}B (over by {over}B)",
                        'japanese': jp_text,
                        'english': en_text,
                    })
                    # Rebuild the full [text][nulls] span at exactly total_span
                    # bytes. Writing a slice whose RHS length differs would
                    # resize the bytearray and shift every following string.
                    total_span = len(jp_bytes) + null_count
                    truncated_bytes = en_bytes[:available]
                    new_region = truncated_bytes + b'\x00' * (total_span - len(truncated_bytes))
                    if len(new_region) != total_span:
                        raise RuntimeError(
                            f"Internal packing error at 0x{idx:X}: region "
                            f"{len(new_region)}B != span {total_span}B"
                        )
                    modified[idx:idx + total_span] = new_region
            else:
                modified[idx:idx + len(jp_bytes)] = en_bytes[:len(jp_bytes)]
            
            pos = idx + len(jp_bytes) + null_count
            occurrences += 1
            found = True
        
        if found:
            replaced_count += 1
            print(f"  [{replaced_count}] {jp_text[:25]}... -> {en_text[:25]}... ({occurrences} occurrences)")
        else:
            print(f"  NOT FOUND (null-terminated): {jp_text[:40]}...")
            issues.append({
                'issue': 'NOT_FOUND',
                'offset': '',
                'detail': 'Japanese text not found as null-terminated string',
                'japanese': jp_text,
                'english': en_text,
            })
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'wb') as f:
        f.write(modified)
    
    return replaced_count, issues


def load_translations_with_offsets(csv_path: Path) -> list:
    """
    Load translations from an MGDATA CSV file, including offsets.
    
    Returns list of dicts: [{'japanese': str, 'english': str, 'offset': int}, ...]
    Only includes rows that have both Japanese and English text.
    """
    entries = []

    if not csv_path.exists():
        print(f"WARNING: Translation file not found: {csv_path}")
        return entries

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jp = row.get('Japanese', '')
            en = row.get('English', '')
            offset_str = row.get('offset', '')
            if jp and en and offset_str:
                offset = int(offset_str, 16)
                entries.append({
                    'japanese': jp,
                    'english': en,
                    'offset': offset,
                })

    print(f"Loaded {len(entries)} translations (with offsets) from {csv_path.name}")
    return entries


def has_malformed_format_code(en_text: str) -> str | None:
    """
    Heuristic check for broken control codes in an English line.

    Returns a short description of the problem, or None if the line looks OK.
    Catches the kinds of corruption that crash the in-game script renderer:
      - a format-code introducer '!' followed by a known type letter but with
        too few following characters (e.g. a truncated '!c0' or '!p010')
      - a line that contains a format-code letter pattern but is missing its
        leading '!' (e.g. starts with 'p0100!e00' instead of '!p0100!e00')
    """
    # Number of DIGITS that must follow the type letter:
    #   !c## (color) -> 2,  !p#### (portrait) -> 4,  !e## (expression) -> 2
    # Button/name codes (!0-!9, !a, !b, !x, !y, !h) take no trailing digits.
    digit_codes = {'c': 2, 'p': 4, 'e': 2}

    # Missing leading '!': a line whose first chars look like a bare format code
    # (e.g. 'p0100!e00...' instead of '!p0100!e00...'). Real lines start with '!'.
    if en_text[:1] in 'pce' and len(en_text) > 1 and en_text[1].isdigit():
        return f"missing leading '!' (starts with '{en_text[:6]}')"

    hexdigits = set('0123456789abcdefABCDEF')

    i = 0
    n = len(en_text)
    while i < n:
        if en_text[i] == '!' and i + 1 < n:
            t = en_text[i + 1]
            if t in digit_codes:
                need = digit_codes[t]
                tail = en_text[i + 2:i + 2 + need]
                # Code values are hex (e.g. !pffff, !c07, !e00).
                if len(tail) < need or any(ch not in hexdigits for ch in tail):
                    return f"truncated !{t} code near '{en_text[i:i+2+need]}'"
                i += 2 + need
                continue
        i += 1
    return None


def write_issue_report(report_path: Path, issues: list) -> None:
    """Write a CSV report of replacement issues. Removes a stale report when clean."""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    if not issues:
        if report_path.exists():
            report_path.unlink()
        return
    with open(report_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL, doublequote=True)
        writer.writerow(['issue', 'offset', 'detail', 'Japanese', 'English'])
        for it in issues:
            writer.writerow([
                it.get('issue', ''),
                it.get('offset', ''),
                it.get('detail', ''),
                it.get('japanese', ''),
                it.get('english', ''),
            ])


def replace_at_offsets(input_file: Path, output_file: Path, entries: list, pad_char=b' '):
    """
    Replace text in a binary file at specific offsets.
    
    Each entry has 'japanese', 'english', and 'offset'. Uses Shift-JIS aware
    parsing from the offset to find the '@' terminator, determining the actual
    byte span of the string in the binary.
    
    Binary layout: [text bytes] [@] [NUL padding...]
    
    The total span from offset through the NUL padding is preserved. If English
    is shorter than Japanese, it's padded with pad_char before the '@'. If English
    is longer, it can expand into trailing NUL bytes (keeping at least 1 NUL).

    Returns (replaced_count, issues) where issues is a list of dicts describing
    any line that could not be replaced cleanly (mismatch, no terminator,
    truncated, or a malformed control code).
    """
    with open(input_file, 'rb') as f:
        data = f.read()

    modified = bytearray(data)
    replaced_count = 0
    skipped_count = 0
    issues = []

    for entry in entries:
        jp_text = entry['japanese']
        en_text = entry['english']
        offset = entry['offset']

        en_bytes = en_text.encode('shift_jis')

        # Proactively flag broken control codes (these crash the renderer even
        # though the bytes "fit").
        fmt_problem = has_malformed_format_code(en_text)
        if fmt_problem:
            issues.append({
                'issue': 'BAD_FORMAT_CODE',
                'offset': f"0x{offset:X}",
                'detail': fmt_problem,
                'japanese': jp_text,
                'english': en_text,
            })

        # Find the '@' terminator from the offset using Shift-JIS aware parsing
        at_pos = find_string_end_sjis(modified, offset)
        if at_pos is None:
            print(f"  NO TERMINATOR at 0x{offset:X}: skipping '{jp_text[:40]}...'")
            skipped_count += 1
            issues.append({
                'issue': 'NO_TERMINATOR',
                'offset': f"0x{offset:X}",
                'detail': 'no @ terminator found within scan range',
                'japanese': jp_text,
                'english': en_text,
            })
            continue

        # Verify the text at this offset matches (ignoring embedded NUL bytes)
        actual_bytes = bytes(modified[offset:at_pos])
        try:
            decoded = actual_bytes.decode('shift_jis', errors='replace').replace('\x00', '')
        except Exception:
            decoded = ''

        if decoded != jp_text:
            print(f"  MISMATCH at 0x{offset:X}: expected '{jp_text[:40]}...', got '{decoded[:40]}...'")
            skipped_count += 1
            issues.append({
                'issue': 'MISMATCH',
                'offset': f"0x{offset:X}",
                'detail': f"binary has: {decoded[:60]}",
                'japanese': jp_text,
                'english': en_text,
            })
            continue

        jp_span = at_pos - offset  # bytes of text before '@'

        # Count trailing NUL bytes after the '@'
        null_start = at_pos + 1  # byte after '@'
        null_count = 0
        while null_start + null_count < len(modified) and modified[null_start + null_count] == 0x00:
            null_count += 1

        # Available space for English text (before '@'):
        #   jp_span + null bytes we can consume (keep at least 1 NUL after '@')
        extra_from_nulls = max(0, null_count - 1)
        available = jp_span + extra_from_nulls

        # Total span we're working with: [text] [@] [nulls]
        total_span = jp_span + 1 + null_count  # text + '@' + nulls

        if len(en_bytes) <= jp_span:
            # English fits within original text space - pad with pad_char.
            # The '@' terminator and original NULs are left untouched.
            new_text = en_bytes + pad_char * (jp_span - len(en_bytes))
            new_region = new_text
            span = jp_span
        elif len(en_bytes) <= available:
            # English is longer but fits by consuming some trailing NULs.
            # New layout: [en_bytes] [@] [fewer NULs] - always exactly total_span.
            consumed = len(en_bytes) - jp_span  # extra bytes needed from NULs
            remaining_nulls = null_count - consumed
            new_region = en_bytes + b'\x40' + b'\x00' * remaining_nulls
            span = total_span
        else:
            # Doesn't fit even with trailing NULs - truncate to fit.
            over = len(en_bytes) - available
            print(f"  WARNING at 0x{offset:X}: English is {over}B over available space - truncating!")
            print(f"    JP: {jp_text[:60]}")
            print(f"    EN: {en_text[:60]}")
            issues.append({
                'issue': 'TRUNCATED',
                'offset': f"0x{offset:X}",
                'detail': f"English {len(en_bytes)}B > available {available}B (over by {over}B)",
                'japanese': jp_text,
                'english': en_text,
            })
            # Rebuild the full span as [truncated text][@][NULs] so the region is
            # ALWAYS exactly total_span bytes. (When null_count == 0 this keeps
            # the layout [text][@] with no trailing NUL, never growing the file.)
            new_text = en_bytes[:available]
            nulls_needed = total_span - len(new_text) - 1  # -1 reserves the '@'
            new_region = new_text + b'\x40' + b'\x00' * nulls_needed
            span = total_span

        # Hard guard: a slice assignment whose RHS length differs from the slice
        # length resizes the bytearray and shifts every following string, which
        # silently corrupts the rest of the file. Never allow it.
        if len(new_region) != span:
            raise RuntimeError(
                f"Internal packing error at 0x{offset:X}: region {len(new_region)}B "
                f"!= span {span}B (jp_span={jp_span}, null_count={null_count})"
            )
        modified[offset:offset + span] = new_region

        replaced_count += 1

    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'wb') as f:
        f.write(modified)

    if skipped_count:
        print(f"  Skipped {skipped_count} entries due to offset mismatch")
    return replaced_count, issues


def find_string_end_sjis(data: bytearray, start: int) -> int | None:
    """
    From 'start', parse forward using Shift-JIS aware logic until we hit
    a standalone 0x40 ('@' terminator). Returns the position of the byte
    just before the '@', i.e. the end of the string content.
    Returns None if no terminator found within a reasonable range.
    """
    pos = start
    limit = min(start + 4096, len(data))  # don't scan too far

    def is_sjis_lead(b):
        return (0x81 <= b <= 0x9F) or (0xE0 <= b <= 0xEF)

    while pos < limit:
        b = data[pos]
        if is_sjis_lead(b) and pos + 1 < len(data):
            pos += 2  # skip 2-byte Shift-JIS character
            continue
        if b == 0x40:  # standalone '@' terminator
            return pos
        pos += 1

    return None


def copy_original_files():
    """Copy original files from extracted-afs to modified-afs-contents for modification."""
    files_to_copy = [
        ("MGDATA", "00000062"),
        ("MGDATA", "00000063"),
    ]
    
    for archive, file_num in files_to_copy:
        src = EXTRACTED_AFS_DIR / archive / file_num
        dst = MODIFIED_AFS_DIR / archive / file_num
        
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"Copied {archive}/{file_num} to modified-afs-contents/")
        else:
            print(f"WARNING: Source file not found: {src}")
    
    # Also copy the metadata JSON
    json_src = EXTRACTED_AFS_DIR / "MGDATA.json"
    json_dst = MODIFIED_AFS_DIR / "MGDATA.json"
    if json_src.exists():
        shutil.copy2(json_src, json_dst)
        print("Copied MGDATA.json")


def process_mgdata():
    """Process MGDATA files 00000062 and 00000063 (female & male protagonist scripts)"""
    
    # First, copy fresh originals
    print("\n" + "=" * 60)
    print("Copying original files from extracted-afs/")
    print("=" * 60)
    copy_original_files()
    
    mgdata_files = [
        ("00000062", "MGDATA_00000062.csv", "female protagonist"),
        ("00000063", "MGDATA_00000063.csv", "male protagonist"),
    ]
    
    total = 0
    grand_issues = 0
    
    for file_num, csv_name, label in mgdata_files:
        csv_path = TRANSLATIONS_DIR / csv_name
        entries = load_translations_with_offsets(csv_path)
        
        if not entries:
            print(f"No translations found for {file_num}!")
            continue
        
        print("\n" + "=" * 60)
        print(f"Processing MGDATA/{file_num} ({label}) - offset-based replacement")
        print("=" * 60)
        target = MODIFIED_AFS_DIR / "MGDATA" / file_num
        if target.exists():
            count, issues = replace_at_offsets(target, target, entries)
            print(f"\nReplaced {count} strings in {target.name}")
            total += count

            report_path = REPLACE_REPORTS_DIR / f"MGDATA_{file_num}_issues.csv"
            write_issue_report(report_path, issues)
            if issues:
                grand_issues += len(issues)
                by_type = {}
                for it in issues:
                    by_type[it['issue']] = by_type.get(it['issue'], 0) + 1
                summary = ", ".join(f"{k}:{v}" for k, v in sorted(by_type.items()))
                print(f"  !! {len(issues)} problem line(s) [{summary}] -> {report_path.name}")
            else:
                print(f"  All lines replaced cleanly (no issues).")
    
    if grand_issues:
        print(f"\n*** {grand_issues} MGDATA line(s) could not be replaced cleanly.")
        print(f"    See reports in: {REPLACE_REPORTS_DIR}")
    return total


def process_1st_read():
    """Process 1ST_READ.BIN (main executable with menu/UI text and move names)"""
    
    input_file = EXTRACTED_DISC_DIR / "1ST_READ.BIN"
    output_file = MODIFIED_DISC_DIR / "1ST_READ.BIN"
    
    # CSV files for 1ST_READ.BIN translations (normal global replacement)
    csv_files = [
        TRANSLATIONS_DIR / "1st_read_strings.csv",   # All text (merged from menu/moves)
    ]
    
    # CSV file for dangerous short strings (null-terminated replacement only)
    dangerous_csv = TRANSLATIONS_DIR / "1st_read_dangerous.csv"
    
    print("\n" + "=" * 60)
    print("Processing 1ST_READ.BIN (menu/UI text + move names)")
    print("=" * 60)
    
    if not input_file.exists():
        print(f"WARNING: Input file not found: {input_file}")
        print("Skipping 1ST_READ.BIN processing.")
        return 0
    
    # Copy original file first
    output_file.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_file, output_file)
    print(f"Copied 1ST_READ.BIN to modified-disc-files/")
    
    # Load translations from all CSV files
    translations = {}
    for csv_file in csv_files:
        if csv_file.exists():
            file_translations = load_translations_from_csv(csv_file)
            translations.update(file_translations)
        else:
            print(f"WARNING: Translation file not found: {csv_file}")
    
    total_count = 0
    all_issues = []
    
    if translations:
        # Apply normal translations (global replacement) - use space padding (null breaks color codes)
        count, issues = replace_text_in_file(output_file, output_file, translations, pad_char=b' ')
        print(f"\nReplaced {count} strings in 1ST_READ.BIN (global)")
        total_count += count
        all_issues.extend(issues)
    else:
        print("No translations loaded for 1ST_READ.BIN")
    
    # Process dangerous short strings with null-terminated replacement
    if dangerous_csv.exists():
        print("\n" + "-" * 40)
        print("Processing dangerous short strings (null-terminated only)")
        print("-" * 40)
        dangerous_translations = load_translations_from_csv(dangerous_csv)
        if dangerous_translations:
            count, issues = replace_null_terminated_strings(output_file, output_file, dangerous_translations)
            print(f"\nReplaced {count} dangerous strings in 1ST_READ.BIN (null-terminated)")
            total_count += count
            all_issues.extend(issues)

    report_path = REPLACE_REPORTS_DIR / "1ST_READ_issues.csv"
    write_issue_report(report_path, all_issues)
    if all_issues:
        by_type = {}
        for it in all_issues:
            by_type[it['issue']] = by_type.get(it['issue'], 0) + 1
        summary = ", ".join(f"{k}:{v}" for k, v in sorted(by_type.items()))
        print(f"\n  !! {len(all_issues)} problem line(s) in 1ST_READ.BIN [{summary}] -> {report_path.name}")
        print(f"     See: {REPLACE_REPORTS_DIR}")
    
    return total_count


def main():
    print("Nekketsu Nikki Translation Tool")
    print("=" * 60)
    print(f"Translations folder: {TRANSLATIONS_DIR}")
    print(f"Modified AFS folder: {MODIFIED_AFS_DIR}")
    print(f"Modified disc folder: {MODIFIED_DISC_DIR}")
    
    # List available translation files
    csv_files = list(TRANSLATIONS_DIR.glob("*.csv"))
    print(f"\nFound {len(csv_files)} translation file(s):")
    for f in csv_files:
        print(f"  - {f.name}")
    
    # Process files
    total = 0
    total += process_mgdata()
    total += process_1st_read()
    
    print("\n" + "=" * 60)
    print(f"Total replacements: {total}")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Run scripts\\rebuild.bat to rebuild the disc")
    print("2. Test translated-disc\\disc.gdi in emulator")


if __name__ == '__main__':
    main()
