"""
Auto-fix byte alignment issues in translations.

KEY INSIGHT: The game treats each line (split by /) independently for byte counting.
After a / line break, byte counting restarts at 0 for that line segment.

Rules:
- / line breaks must be at even byte positions in the OVERALL string
- ! format codes must be at even byte positions WITHIN THEIR LINE SEGMENT
- Literal ! at even positions (within line) will be misread as codes -> use fullwidth ！
- Fullwidth characters are 2 bytes and should start on even positions within their line
- Backslashes display as ¥ in Shift-JIS -> remove them
- ... can be replaced with … (saves 1 byte) when at even position
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
    pos = 0
    for i in range(line_start, char_index):
        if ord(text[i]) < 128:
            pos += 1
        else:
            pos += 2
    return pos

def find_first_problem(text: str) -> tuple[int, str] | None:
    """
    Find the character index of the first alignment problem.
    Returns (index, problem_type) or None.
    
    - / line breaks: must be at even position in OVERALL string
    - ! format codes: must be at even position WITHIN THEIR LINE
    """
    for i, char in enumerate(text):
        # Check / line breaks - uses overall byte position
        if char == '/':
            byte_pos = get_byte_position(text, i)
            if byte_pos % 2 != 0:
                return (i, 'slash')
        # Check ! format codes - uses per-line byte position
        elif char == '!' and i + 1 < len(text) and text[i + 1].isalnum():
            byte_pos = get_byte_position_in_line(text, i)
            if byte_pos % 2 != 0:
                return (i, 'format_code')
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
    
    Uses per-line byte position since game resets counting after each /.
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
            # Check byte position WITHIN LINE at this point
            current_text = ''.join(result)
            byte_pos = get_byte_position_in_line(current_text + '...', len(current_text))
            if byte_pos % 2 == 0:
                # Even position in line - use … (saves 1 byte)
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
    If / is at an even OVERALL position, and there's a space before it,
    removing the space might keep / at an even position (if shifted by 2 bytes).
    
    Note: / must be at even OVERALL byte position (not per-line).
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


def fix_fullwidth_punctuation(text: str) -> str:
    """
    Replace fullwidth punctuation with ASCII equivalents to avoid byte alignment issues.
    
    Fullwidth chars (2 bytes) at odd OVERALL positions cause corruption.
    ASCII chars (1 byte) work at any position.
    
    Special case for !:
    - Literal ! at EVEN per-line position → misread as format code → keep as ！
    - Literal ! at ODD per-line position → safe to use ASCII !
    - ！ at ODD overall position → corrupted → convert to ! (which is safe)
    - ！ at EVEN overall position → keep as ！ (correct)
    """
    # First pass: convert fullwidth punctuation (except ！) to ASCII
    # These are safe as ASCII at any position
    replacements = {
        '、': ',',   # fullwidth comma
        '。': '.',   # fullwidth period  
        '？': '?',   # fullwidth question mark
        '：': ':',   # fullwidth colon
        '；': ';',   # fullwidth semicolon
        '（': '(',   # fullwidth open paren
        '）': ')',   # fullwidth close paren
        '「': '"',   # Japanese open quote
        '」': '"',   # Japanese close quote
        '『': '"',   # Japanese double open quote
        '』': '"',   # Japanese double close quote
        '～': '~',   # fullwidth tilde
        '・': '-',   # middle dot to hyphen
    }
    
    for fw, ascii_char in replacements.items():
        text = text.replace(fw, ascii_char)
    
    # Second pass: handle ！ specially
    # ！ at odd OVERALL position → convert to ! (safe)
    # ！ at even OVERALL position → keep as ！ (correct)
    # ! at even PER-LINE position (not format code) → misread as format code → use ！
    # ! at odd PER-LINE position (not format code) → safe as ASCII !
    
    if '！' not in text and '!' not in text:
        return text
    
    result = list(text)
    i = 0
    while i < len(result):
        char = result[i]
        
        if char == '！':
            # Fullwidth exclamation - check OVERALL position
            byte_pos = get_byte_position(''.join(result), i)
            if byte_pos % 2 != 0:
                # Odd overall position - fullwidth will corrupt, use ASCII
                result[i] = '!'
            # Even overall position - keep as fullwidth (safe)
        
        elif char == '!':
            # ASCII exclamation - check if it's a format code
            is_format_code = (i + 1 < len(result) and result[i + 1].isalnum())
            if not is_format_code:
                # Literal ! - check PER-LINE position (format code detection is per-line)
                byte_pos = get_byte_position_in_line(''.join(result), i)
                if byte_pos % 2 == 0:
                    # Even per-line position - will be misread as format code
                    # But we can only use ！ if OVERALL position is even
                    overall_pos = get_byte_position(''.join(result), i)
                    if overall_pos % 2 == 0:
                        result[i] = '！'
                    # If overall is odd, we have a conflict - keep as ! and hope for best
                # Odd per-line position - keep as ASCII (safe)
        
        i += 1
    
    return ''.join(result)

def fix_alignment(text: str, max_iterations: int = 500) -> str:
    """
    Fix all byte alignment issues for ! codes and / line breaks.
    
    - / line breaks: adjusted based on overall byte position
    - ! format codes: adjusted based on per-line byte position
    """
    if '!' not in text and '/' not in text:
        return text
    
    for _ in range(max_iterations):
        problem = find_first_problem(text)
        if problem is None:
            break  # All fixed!
        
        problem_index, problem_type = problem
        
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
    """Fix alignment, backslash, ellipsis, punctuation and spacing issues in a CSV file. Returns dict of fix counts."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    fixes = {'alignment': 0, 'backslash': 0, 'ellipsis': 0, 'spacing': 0, 'punctuation': 0}
    
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
        
        # 3. Fix fullwidth punctuation (convert to ASCII where safe)
        fixed = fix_fullwidth_punctuation(english)
        if fixed != english:
            fixes['punctuation'] += 1
            english = fixed
        
        # 4. Fix ellipsis - use … only when at even position
        fixed = fix_ellipsis(english)
        if fixed != english:
            fixes['ellipsis'] += 1
            english = fixed
        
        # 5. Fix alignment for format codes and line breaks
        fixed = fix_alignment(english)
        if fixed != english:
            fixes['alignment'] += 1
            english = fixed
        
        # 6. Re-check fullwidth punctuation after alignment changes
        fixed = fix_fullwidth_punctuation(english)
        if fixed != english:
            fixes['punctuation'] += 1
            english = fixed
        
        # 7. Remove unnecessary spaces before / (saves bytes while keeping alignment)
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
    totals = {'alignment': 0, 'backslash': 0, 'ellipsis': 0, 'spacing': 0, 'punctuation': 0}
    
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
