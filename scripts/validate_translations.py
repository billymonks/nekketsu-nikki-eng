"""
Validate translations for byte alignment issues.

KEY INSIGHT: The game treats each line (split by /) independently for byte counting.
After a / line break, byte counting restarts at 0 for that line segment.

Rules:
- / line breaks must be at even byte positions in the OVERALL string
- ! format codes must be at even byte positions WITHIN THEIR LINE SEGMENT
"""
import csv
import io
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
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    
    for i, row in enumerate(rows, start=2):  # Start at 2 (header is line 1)
        english = row.get('english', '')
        if not english:
            continue
        
        issues = check_byte_alignment(english)
        if issues:
            all_issues.append({
                'line': i,
                'japanese': row.get('japanese', '')[:40],
                'english': english[:60],
                'issues': issues
            })
    
    return all_issues

def validate_batch_dir(batch_dir: Path):
    """Validate all batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    
    total_issues = 0
    
    for batch_file in batch_files:
        issues = validate_csv(batch_file)
        if issues:
            print(f"\n{'='*60}")
            print(f"Issues in {batch_file.name}:")
            print('='*60)
            for issue in issues:
                print(f"\nLine {issue['line']}:")
                print(f"  JP: {issue['japanese']}...")
                print(f"  EN: {issue['english']}...")
                for prob in issue['issues']:
                    pos_type = prob.get('position_type', 'overall')
                    print(f"  ❌ '{prob['code']}' at byte {prob['byte_pos']} ({pos_type}) - ODD")
                    print(f"     ...after: '{prob['text_before']}'")
            total_issues += len(issues)
    
    if total_issues == 0:
        print("✅ All translations pass byte alignment check!")
    else:
        print(f"\n⚠️  Found {total_issues} translations with alignment issues")
    
    return total_issues

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        exit(1)
    
    print("Validating byte alignment in translations...")
    print("(/ must be at EVEN overall position)")
    print("(! codes must be at EVEN position within their line)\n")
    
    validate_batch_dir(batch_dir)
