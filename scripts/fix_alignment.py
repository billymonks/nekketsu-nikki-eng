"""
Auto-fix byte alignment issues in translations.
The ! character in formatting codes must be at even byte positions.
"""
import csv
import io
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

def fix_csv(csv_path: Path) -> int:
    """Fix alignment in a CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    fixes = 0
    
    for row in rows:
        english = row.get('english', '')
        if not english:
            continue
        
        fixed = fix_alignment(english)
        if fixed != english:
            row['english'] = fixed
            fixes += 1
    
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=['japanese', 'english', 'context', 'notes'],
            quoting=csv.QUOTE_ALL,
            extrasaction='ignore'
        )
        writer.writeheader()
        writer.writerows(rows)
    
    return fixes

def fix_batch_dir(batch_dir: Path):
    """Fix all batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    total_fixes = 0
    
    for batch_file in batch_files:
        fixes = fix_csv(batch_file)
        if fixes > 0:
            print(f"  Fixed {fixes} lines in {batch_file.name}")
            total_fixes += fixes
    
    print(f"\nTotal fixes: {total_fixes}")

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
