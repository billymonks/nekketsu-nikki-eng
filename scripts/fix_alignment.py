"""
Auto-fix byte alignment issues in translations.
- Format codes (! followed by alphanumeric) and line breaks (/) must be at even byte positions.
- Literal ! at even byte positions will be misread as codes, so replace with fullwidth ！
- Fullwidth characters (！ … ？ etc) are 2 bytes and must start on even byte positions.
- Also fixes backslash issues (displays as ¥ in Shift-JIS).
- Replaces ... with … only when it saves bytes (at even position).
- Removes double spaces and other byte-wasting patterns.
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
    """Find the character index of the first misaligned ! code or / line break."""
    for i, char in enumerate(text):
        # Check ! format codes (must be followed by alphanumeric)
        if char == '!' and i + 1 < len(text) and text[i + 1].isalnum():
            byte_pos = get_byte_position(text, i)
            if byte_pos % 2 != 0:
                return i
        # Check / line breaks
        elif char == '/':
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


def fix_ellipsis(text: str) -> str:
    """
    Replace ... (3 bytes) with … (2 bytes) only when it saves bytes.
    If … would end up at an odd byte position (needing a space = 3 bytes total),
    keep ... instead since it's the same length but cleaner.
    """
    if '...' not in text and '…' not in text:
        return text
    
    # First, normalize all ellipses to ... so we can re-evaluate
    text = text.replace('…', '...')
    
    # Now find each ... and decide whether to use … or keep ...
    result = []
    i = 0
    while i < len(text):
        if text[i:i+3] == '...':
            # Check byte position at this point
            byte_pos = get_byte_position(''.join(result), len(result))
            if byte_pos % 2 == 0:
                # Even position - use … (saves 1 byte)
                result.append('…')
            else:
                # Odd position - keep ... (same as " …" but cleaner)
                result.append('...')
            i += 3
        else:
            result.append(text[i])
            i += 1
    
    return ''.join(result)


def fix_double_spaces(text: str) -> str:
    """Remove true double spaces (not alignment spaces)."""
    # Multiple halfwidth spaces -> single
    while '  ' in text:
        text = text.replace('  ', ' ')
    # Multiple fullwidth spaces -> single halfwidth  
    while '　　' in text:
        text = text.replace('　　', ' ')
    # Mixed double spaces
    text = text.replace('　 ', ' ')
    text = text.replace(' 　', ' ')
    return text


def fix_unnecessary_spaces_before_slash(text: str) -> str:
    """
    Remove unnecessary spaces before / line breaks.
    If / is at an even position, and there's a space before it,
    removing the space keeps / at an even position (shifted by 1 or 2 bytes).
    """
    if '/' not in text:
        return text
    
    result = list(text)
    i = 0
    while i < len(result):
        if result[i] == '/':
            # Check if there's a space immediately before
            if i > 0 and result[i-1] in (' ', '　'):
                # Calculate current byte position of /
                current_byte_pos = get_byte_position(''.join(result), i)
                # Calculate byte position if we remove the space
                space_bytes = 1 if result[i-1] == ' ' else 2
                new_byte_pos = current_byte_pos - space_bytes
                
                # Only remove if / stays at even position
                if new_byte_pos % 2 == 0:
                    result.pop(i-1)
                    i -= 1  # Adjust index after removal
        i += 1
    
    return ''.join(result)


def fix_literal_exclamations(text: str) -> str:
    """
    Replace literal ! at even byte positions with fullwidth ！.
    Literal ! at even positions gets interpreted as format codes by the game.
    Only affects ! NOT followed by alphanumeric (those are real format codes).
    """
    if '!' not in text:
        return text
    
    result = list(text)
    i = 0
    while i < len(result):
        char = result[i]
        if char == '!':
            # Check if this is a format code (followed by alphanumeric)
            is_format_code = (i + 1 < len(result) and result[i + 1].isalnum())
            if not is_format_code:
                # This is a literal ! - check byte position
                byte_pos = get_byte_position(''.join(result), i)
                if byte_pos % 2 == 0:
                    # Even position - game will misread as code, use fullwidth
                    result[i] = '！'
        i += 1
    
    return ''.join(result)

def fix_alignment(text: str, max_iterations: int = 500) -> str:
    """Fix all byte alignment issues for ! codes and / line breaks."""
    if '!' not in text and '/' not in text:
        return text
    
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

def fix_csv(csv_path: Path) -> dict:
    """Fix alignment, backslash, ellipsis, and spacing issues in a CSV file. Returns dict of fix counts."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    fixes = {'alignment': 0, 'backslash': 0, 'ellipsis': 0, 'spacing': 0}
    
    for row in rows:
        english = row.get('english', '')
        if not english:
            continue
        
        # 1. Fix backslashes first (remove artifacts)
        fixed = fix_backslashes(english)
        if fixed != english:
            fixes['backslash'] += 1
            english = fixed
        
        # 2. Fix double spaces and space waste
        fixed = fix_double_spaces(english)
        if fixed != english:
            fixes['spacing'] += 1
            english = fixed
        
        # 3. Fix ellipsis - use … only when at even position
        fixed = fix_ellipsis(english)
        if fixed != english:
            fixes['ellipsis'] += 1
            english = fixed
        
        # 4. Fix alignment for format codes and line breaks
        fixed = fix_alignment(english)
        if fixed != english:
            fixes['alignment'] += 1
            english = fixed
        
        # 5. Fix literal ! at even positions (would be misread as codes)
        fixed = fix_literal_exclamations(english)
        if fixed != english:
            fixes['alignment'] += 1
            english = fixed
        
        # 6. Remove unnecessary spaces before / (saves bytes while keeping alignment)
        fixed = fix_unnecessary_spaces_before_slash(english)
        if fixed != english:
            fixes['spacing'] += 1
        
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
    
    return fixes

def fix_batch_dir(batch_dir: Path):
    """Fix all batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    totals = {'alignment': 0, 'backslash': 0, 'ellipsis': 0, 'spacing': 0}
    
    for batch_file in batch_files:
        fixes = fix_csv(batch_file)
        if any(fixes.values()):
            parts = [f"{v} {k}" for k, v in fixes.items() if v > 0]
            print(f"  {batch_file.name}: {', '.join(parts)}")
            for k, v in fixes.items():
                totals[k] += v
    
    parts = [f"{v} {k}" for k, v in totals.items() if v > 0]
    print(f"\nTotal: {', '.join(parts) if parts else 'no fixes needed'}")

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
