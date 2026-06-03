"""
Validate translations for byte alignment issues.

KEY INSIGHT: The game treats each line (split by /) independently for byte counting.
After a / line break, byte counting restarts at 0 for that line segment.

Rules:
- / line breaks must be at even byte positions in the OVERALL string
- ! format codes must be at even byte positions WITHIN THEIR LINE SEGMENT
"""
import csv
import re
from pathlib import Path

def get_byte_length(text: str) -> int:
    """Get the Shift-JIS byte length of a string."""
    try:
        return len(text.encode('shift-jis'))
    except UnicodeEncodeError:
        # Fallback: estimate based on character types
        length = 0
        for char in text:
            if ord(char) < 128:
                length += 1  # ASCII = 1 byte
            else:
                length += 2  # Japanese/fullwidth = 2 bytes
        return length

def get_byte_position_in_line(text: str, char_index: int) -> int:
    """
    Get byte position within the current line segment (after last /).
    The game resets byte counting to 0 after each / line break.
    """
    # Find the start of the current line (after the last /)
    line_start = 0
    for i in range(char_index):
        if text[i] == '/':
            line_start = i + 1
    
    # Calculate byte position from line start to char_index
    return get_byte_length(text[line_start:char_index])

def find_format_codes(text: str) -> list:
    """Find all ! format codes and their positions."""
    # Match !cXX, !pXXXX, !eXX, !0, !1, !a, !h, etc.
    pattern = r'![a-zA-Z0-9]+'
    codes = []
    for match in re.finditer(pattern, text):
        codes.append({
            'code': match.group(),
            'char_pos': match.start(),
            'text_before': text[:match.start()]
        })
    return codes

def check_byte_alignment(text: str) -> list:
    """
    Check byte alignment for:
    - / line breaks: must be at even OVERALL byte position
    - ! format codes: must be at even byte position WITHIN THEIR LINE
    """
    issues = []
    
    # Check / line breaks (overall position)
    for i, char in enumerate(text):
        if char == '/':
            byte_pos = get_byte_length(text[:i])
            if byte_pos % 2 != 0:
                issues.append({
                    'code': '/',
                    'byte_pos': byte_pos,
                    'position_type': 'overall',
                    'text_before': text[max(0,i-20):i]
                })
    
    # Check ! format codes (per-line position)
    codes = find_format_codes(text)
    for code_info in codes:
        char_pos = code_info['char_pos']
        # Use per-line byte position
        byte_pos = get_byte_position_in_line(text, char_pos)
        
        if byte_pos % 2 != 0:
            issues.append({
                'code': code_info['code'],
                'byte_pos': byte_pos,
                'position_type': 'in-line',
                'text_before': code_info['text_before'][-20:] if len(code_info['text_before']) > 20 else code_info['text_before']
            })
    
    return issues

def validate_csv(csv_path: Path) -> list:
    """Validate all translations in a CSV file."""
    all_issues = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for i, row in enumerate(rows, start=2):
        english = row.get('English', '')
        if not english:
            continue

        issues = check_byte_alignment(english)
        if issues:
            all_issues.append({
                'line': i,
                'japanese': row.get('Japanese', '')[:40],
                'english': english[:60],
                'issues': issues
            })

    return all_issues


def validate_at_terminators(translations_dir: Path) -> int:
    """
    Validate the implicit '@' (0x40) message terminator of every MGDATA string.

    The game only treats '@' as a terminator when it lands on an EVEN byte
    position (counting from the last space or '/'). Japanese text is all 2-byte
    glyphs so it is always even, but single-byte English can leave an odd final
    segment. When that happens the '@' is drawn literally and the text bleeds
    into the next string.

    A string is only truly broken when the English exactly fills its slot AND the
    final segment is odd AND there is no trailing NUL for replace_text.py to slip
    a space before the '@'. (Shorter English is padded with a space before '@', so
    it is always safe; a spare NUL lets the patcher rescue an exact fit.)

    Needs the untouched binaries in extracted-afs/. Returns the broken count, or
    -1 if the binaries are unavailable (check skipped).
    """
    from replace_text import find_string_end_sjis, at_render_position

    project_dir = translations_dir.parent
    pairs = [
        ("MGDATA_00000062.csv", project_dir / "extracted-afs" / "MGDATA" / "00000062"),
        ("MGDATA_00000063.csv", project_dir / "extracted-afs" / "MGDATA" / "00000063"),
    ]

    broken = []
    for csv_name, bin_path in pairs:
        csv_path = translations_dir / csv_name
        if not csv_path.exists() or not bin_path.exists():
            print(f"  (skipping '@' check for {csv_name}: missing CSV or extracted binary)")
            return -1
        data = bytearray(bin_path.read_bytes())
        with open(csv_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for line_no, row in enumerate(rows, start=2):
            offset = row.get("offset", "")
            english = row.get("English", "")
            if not offset or not english:
                continue
            o = int(offset, 16)
            at = find_string_end_sjis(data, o)
            if at is None:
                continue
            jp_span = at - o
            nulls = 0
            while at + 1 + nulls < len(data) and data[at + 1 + nulls] == 0x00:
                nulls += 1
            enc = english.encode("shift_jis", errors="replace")
            # Shorter than the slot -> padded with a space before '@' -> safe.
            if len(enc) < jp_span:
                continue
            # Longer is a length/truncation problem, reported elsewhere.
            if len(enc) > jp_span:
                continue
            # Exact fit: '@' abuts the text. Odd final segment + no spare NUL = broken.
            if at_render_position(enc) % 2 == 1 and nulls == 0:
                broken.append((csv_name, line_no, offset, english[:60]))

    if not broken:
        print("All strings pass the '@' terminator check!")
    else:
        print(f"\nFound {len(broken)} strings where '@' would render literally:")
        for csv_name, line_no, offset, text in broken:
            print(f"  {csv_name} line {line_no} ({offset}): {text}")
    return len(broken)


def validate_mgdata_files(translations_dir: Path):
    """Validate MGDATA CSV files."""
    target_files = [
        translations_dir / "MGDATA_00000062.csv",
        translations_dir / "MGDATA_00000063.csv",
    ]

    total_issues = 0

    for target_file in target_files:
        issues = validate_csv(target_file)
        if issues:
            total_issues += len(issues)

    if total_issues == 0:
        print("All translations pass byte alignment check!")
    else:
        print(f"\nFound {total_issues} translations with alignment issues")

    validate_at_terminators(translations_dir)

    return total_issues


if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    translations_dir = project_dir / "translations"

    print("Validating byte alignment in translations...")
    print("(/ must be at EVEN overall position)")
    print("(! codes must be at EVEN position within their line)\n")

    validate_mgdata_files(translations_dir)
