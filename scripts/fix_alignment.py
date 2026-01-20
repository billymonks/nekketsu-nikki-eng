"""
Auto-fix byte alignment issues in translations.
The ! character in formatting codes must be at even byte positions.
Also fixes backslash issues (displays as ¥ in Shift-JIS).
"""
import csv
import io
import re
from pathlib import Path

def get_byte_position(text: str, char_index: int) -> int:
    """Get the byte position of a character index in Shift-JIS."""
    pos = 0
    for i, char in enumerate(text):
        if i == char_index:
            return pos
        if ord(char) < 128:
            pos += 1
        else:
            pos += 2
    return pos

def find_first_problem(text: str) -> int | None:
    """Find the character index of the first misaligned ! code."""
    for i, char in enumerate(text):
        if char == '!' and i + 1 < len(text) and text[i + 1].isalnum():
            byte_pos = get_byte_position(text, i)
            if byte_pos % 2 != 0:
                return i
    return None

def fix_backslashes(text: str) -> str:
    """
    Fix backslash characters that display as ¥ in Shift-JIS.
    Simply remove all backslashes - they're artifacts from escaping.
    """
    return text.replace('\\', '')

def fix_alignment(text: str, max_iterations: int = 500) -> str:
    """Fix all byte alignment issues."""
    if '!' not in text:
        return text
    
    # Clean up double spaces from previous bad fixes
    text = text.replace('　　', ' ')
    text = text.replace('　 ', ' ')
    text = text.replace(' 　', ' ')
    
    for _ in range(max_iterations):
        problem_index = find_first_problem(text)
        if problem_index is None:
            break  # All fixed!
        
        # Check if character IMMEDIATELY before the problem is a space
        if problem_index > 0:
            prev_char = text[problem_index - 1]
            if prev_char == ' ':
                # Swap halfwidth to fullwidth (adds 1 byte)
                text = text[:problem_index-1] + '　' + text[problem_index:]
                continue
            elif prev_char == '　':
                # Swap fullwidth to halfwidth (removes 1 byte)
                text = text[:problem_index-1] + ' ' + text[problem_index:]
                continue
        
        # No space immediately before - insert one
        text = text[:problem_index] + ' ' + text[problem_index:]
    
    return text

def fix_csv(csv_path: Path) -> tuple[int, int]:
    """Fix alignment and backslash issues in a CSV file. Returns (alignment_fixes, backslash_fixes)."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    alignment_fixes = 0
    backslash_fixes = 0
    
    for row in rows:
        english = row.get('english', '')
        if not english:
            continue
        
        # Fix backslashes first (affects byte count)
        fixed = fix_backslashes(english)
        if fixed != english:
            backslash_fixes += 1
            english = fixed
        
        # Then fix alignment
        fixed = fix_alignment(english)
        if fixed != english:
            alignment_fixes += 1
        
        row['english'] = fixed
    
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['japanese', 'english', 'context', 'notes'],
            quoting=csv.QUOTE_ALL,
            extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(rows)
    
    return alignment_fixes, backslash_fixes

def fix_batch_dir(batch_dir: Path):
    """Fix all batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    total_alignment = 0
    total_backslash = 0
    
    for batch_file in batch_files:
        alignment_fixes, backslash_fixes = fix_csv(batch_file)
        if alignment_fixes > 0 or backslash_fixes > 0:
            print(f"  {batch_file.name}: {alignment_fixes} alignment, {backslash_fixes} backslash fixes")
            total_alignment += alignment_fixes
            total_backslash += backslash_fixes
    
    print(f"\nTotal: {total_alignment} alignment fixes, {total_backslash} backslash fixes")

if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        exit(1)
    
    print("Fixing byte alignment...")
    fix_batch_dir(batch_dir)
    
    print("\nValidating...")
    from validate_translations import validate_batch_dir
    validate_batch_dir(batch_dir)
