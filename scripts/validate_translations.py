"""
Validate translations for byte alignment issues.
The ! character in formatting codes (!cXX, !pXXXX, !eXX, !0, !1, etc.)
must land on an EVEN byte position for the game's parser to work.
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
    """Check if all ! codes are on even byte positions."""
    issues = []
    codes = find_format_codes(text)
    
    for code_info in codes:
        text_before = code_info['text_before']
        byte_pos = get_byte_length(text_before)
        
        if byte_pos % 2 != 0:
            issues.append({
                'code': code_info['code'],
                'byte_pos': byte_pos,
                'text_before': text_before[-20:] if len(text_before) > 20 else text_before
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
                    print(f"  ❌ '{prob['code']}' at byte {prob['byte_pos']} (ODD)")
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
    print("(! codes must be at EVEN byte positions)\n")
    
    validate_batch_dir(batch_dir)
