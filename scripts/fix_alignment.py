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
    
    Rules:
    - / line breaks: must be at even OVERALL position
    - ! format codes: must be at even PER-LINE position  
    - Literal ! (at end of line/string): must be at even PER-LINE position
    """
    for i, char in enumerate(text):
        # Check / line breaks - must be at even OVERALL position
        if char == '/':
            byte_pos = get_byte_position(text, i)
            if byte_pos % 2 != 0:
                return (i, 'slash')
        # Check all ! - must be at even PER-LINE position
        elif char == '!':
            byte_pos = get_byte_position_in_line(text, i)
            if byte_pos % 2 != 0:
                is_format_code = (i + 1 < len(text) and text[i + 1].isalnum())
                return (i, 'format_code' if is_format_code else 'literal_excl')
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


def fix_spaces_around_slash(text: str) -> str:
    """
    Ensure proper spacing before / for reliable line break rendering.
    
    Testing shows that / works more reliably when preceded by a space.
    This adds spaces before / to ensure / lands on an even overall position.
    Uses only halfwidth spaces to avoid 2-byte chars at odd positions.
    """
    if '/' not in text:
        return text
    
    result = list(text)
    i = 0
    while i < len(result):
        if result[i] == '/':
            current_byte_pos = get_byte_position(''.join(result), i)
            if current_byte_pos % 2 != 0:
                # Currently at odd position - add one space to make it even
                result.insert(i, ' ')
                i += 1  # Skip the space we just inserted
        i += 1
    
    return ''.join(result)


def fix_fullwidth_punctuation(text: str) -> str:
    """
    Replace fullwidth punctuation with ASCII equivalents to avoid byte alignment issues.
    
    SIMPLIFIED RULE: Always use ASCII punctuation.
    - Fullwidth chars at wrong positions cause corruption (或 etc)
    - ASCII ! is only a problem when followed by alphanumeric (format code)
    - At end of string/line or before non-alphanumeric, ASCII ! is safe
    """
    # Convert ALL fullwidth punctuation to ASCII
    replacements = {
        '！': '!',   # fullwidth exclamation
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
    
    return text

def fix_fullwidth_spaces(text: str) -> str:
    """
    Replace fullwidth spaces with double halfwidth spaces.
    Fullwidth spaces (2 bytes) at odd positions cause corruption.
    Double halfwidth spaces (2 bytes) work at any position.
    """
    return text.replace('　', '  ')

def fix_alignment(text: str, max_iterations: int = 500) -> str:
    """
    Fix all byte alignment issues for ! codes and / line breaks.
    
    - / line breaks: adjusted based on overall byte position
    - ! format codes: adjusted based on per-line byte position
    
    Uses only halfwidth spaces to avoid 2-byte chars at odd positions.
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
                # Add another halfwidth space (2 spaces = 2 bytes, keeps alignment)
                text = text[:problem_index] + ' ' + text[problem_index:]
                continue
            elif prev_char == '　':
                # Replace fullwidth with halfwidth (removes 1 byte)
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
        
        # 3b. Fix fullwidth spaces (convert to double halfwidth)
        fixed = fix_fullwidth_spaces(english)
        if fixed != english:
            fixes['spacing'] += 1
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
        
        # 7. Ensure proper spacing before / for reliable line breaks
        fixed = fix_spaces_around_slash(english)
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
