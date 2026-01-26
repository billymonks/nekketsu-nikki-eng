"""
Fix byte alignment in translations for Shift-JIS game text.

KEY DISCOVERY: Spaces reset the byte count for alignment purposes!

Rules (from testing):
- Byte position resets after each SPACE (not just /)
- / line breaks: must be at EVEN position from last space/start
- ! format codes: must be at EVEN position from last space/start  
- Literal !: must be at ODD position to display (can't fix with spaces)
- Fullwidth chars: must start at EVEN position from last space/start
- ... → … saves 1 byte when at even position
"""
import csv
import io
from pathlib import Path


FORMAT_CODE_PATTERNS = {
    '0': 2, '1': 2, '2': 2, '3': 2, '4': 2,
    '5': 2, '6': 2, '7': 2, '8': 2, '9': 2,
    'a': 2, 'b': 2,
    'c': 4, 'p': 6, 'e': 4,
}


def get_format_code_length(text: str, pos: int) -> int:
    """Return character length of format code at pos, or 0 if not a format code."""
    if pos >= len(text) or text[pos] != '!' or pos + 1 >= len(text):
        return 0
    return FORMAT_CODE_PATTERNS.get(text[pos + 1], 0)


def get_position_for_format_code(text: str, char_index: int) -> int:
    """
    Get byte position for format code alignment.
    Format codes count as 1 byte.
    Resets on space or /.
    """
    segment_start = 0
    for i in range(char_index):
        if text[i] in ' /':
            segment_start = i + 1
    
    pos, i = 0, segment_start
    while i < char_index and i < len(text):
        fc_len = get_format_code_length(text, i)
        if fc_len > 0:
            pos += 1  # Format codes = 1 byte for format code alignment
            i += fc_len
        else:
            pos += 1 if ord(text[i]) < 128 else 2
            i += 1
    return pos


def get_position_for_slash(text: str, char_index: int) -> int:
    """
    Get byte position for / alignment.
    Format codes count as their FULL character length (not 1 byte).
    Resets on space or /.
    """
    segment_start = 0
    for i in range(char_index):
        if text[i] in ' /':
            segment_start = i + 1
    
    pos, i = 0, segment_start
    while i < char_index and i < len(text):
        # For / alignment, count all characters by their actual byte size
        pos += 1 if ord(text[i]) < 128 else 2
        i += 1
    return pos


def fix_all_left_to_right(text: str) -> str:
    """
    Process text left to right, fixing issues as we encounter them.
    Each fix is applied immediately, affecting all subsequent positions.
    """
    result = []
    i = 0
    
    while i < len(text):
        char = text[i]
        current = ''.join(result)
        
        if char == '/':
            # Check / alignment (format codes count as full length)
            pos = get_position_for_slash(current, len(current))
            if pos % 2 != 0:
                # ODD position - add space before /
                result.append(' ')
            result.append('/')
            i += 1
            
        elif char == '!':
            fc_len = get_format_code_length(text, i)
            if fc_len > 0:
                # Format code - check alignment (format codes count as 1 byte)
                pos = get_position_for_format_code(current, len(current))
                if pos % 2 != 0:
                    # ODD position - add space before format code
                    result.append(' ')
                result.append(text[i:i + fc_len])
                i += fc_len
            else:
                # Literal ! - check if it will render
                pos = get_position_for_slash(current, len(current))
                if pos % 2 == 0:
                    # EVEN position - won't render, use fullwidth
                    result.append('！')
                else:
                    # ODD position - will render
                    result.append('!')
                i += 1
        else:
            result.append(char)
            i += 1
    
    return ''.join(result)


def cleanup(text: str) -> str:
    """Remove unnecessary characters."""
    text = text.replace('\\', '')
    while '  ' in text:
        text = text.replace('  ', ' ')
    # Remove spaces around / - fix_alignment will add back if needed
    text = text.replace(' /', '/')
    text = text.replace('/ ', '/')
    text = text.rstrip(' ')
    return text


def fix_ellipsis(text: str) -> str:
    """Replace ... with … when it saves bytes (at even position)."""
    if '...' not in text and '…' not in text:
        return text
    
    text = text.replace('…', '...')
    
    result = []
    i = 0
    while i < len(text):
        if text[i:i+3] == '...':
            current = ''.join(result)
            byte_pos = get_position_for_slash(current, len(current))
            result.append('…' if byte_pos % 2 == 0 else '...')
            i += 3
        else:
            result.append(text[i])
            i += 1
    
    return ''.join(result)


def fix_alignment(text: str, max_iter: int = 100) -> str:
    """Add spaces to fix / and format code alignment."""
    for _ in range(max_iter):
        problem = find_alignment_problem(text)
        if problem is None:
            break
        # Adding a space resets the count, so this shifts the problem char
        text = text[:problem] + ' ' + text[problem:]
    return text


def fix_literal_exclamations(text: str) -> str:
    """
    Convert literal ! at EVEN position to fullwidth ！.
    - Literal ! at EVEN position = dropped (bad)
    - Fullwidth ！ at EVEN position = renders (good)
    """
    result = []
    i = 0
    while i < len(text):
        fc_len = get_format_code_length(text, i)
        if fc_len > 0:
            # Format code - keep as-is
            result.append(text[i:i + fc_len])
            i += fc_len
        elif text[i] == '!':
            # Literal ! - check position (use full char counting)
            current = ''.join(result)
            pos = get_position_for_slash(current, len(current))
            if pos % 2 == 0:
                # EVEN position - won't render, use fullwidth
                result.append('！')
            else:
                # ODD position - will render, keep as-is
                result.append('!')
            i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def process_text(text: str) -> str:
    """Apply all fixes in order."""
    text = cleanup(text)
    text = fix_ellipsis(text)
    text = fix_all_left_to_right(text)  # Single pass: /, format codes, and ! 
    return text


def fix_csv(csv_path: Path) -> dict:
    """Fix a CSV file. Returns counts of changes."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    changes = 0
    
    for row in rows:
        original = row.get('english', '')
        if not original:
            continue
        fixed = process_text(original)
        if fixed != original:
            changes += 1
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
    
    return {'changes': changes}


def fix_batch_dir(batch_dir: Path):
    """Fix all batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    total = 0
    
    for batch_file in batch_files:
        result = fix_csv(batch_file)
        if result['changes']:
            print(f"  {batch_file.name}: {result['changes']} changes")
            total += result['changes']
    
    print(f"\nTotal: {total} changes" if total else "\nNo changes needed")


if __name__ == "__main__":
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        exit(1)
    
    print("Fixing alignment...")
    fix_batch_dir(batch_dir)
    
    print("\nValidating...")
    from validate_translations import validate_batch_dir
    validate_batch_dir(batch_dir)
