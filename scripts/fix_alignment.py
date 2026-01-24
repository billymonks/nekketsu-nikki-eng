"""
Validate and minimally fix byte alignment issues in translations.

KEY INSIGHT: The game treats each line (split by /) independently for byte counting.
After a / line break, byte counting restarts at 0 for that line segment.

Rules (based on testing):
- / line breaks must be at EVEN byte positions in the OVERALL string
  BUT also must NOT be at multiples of 20 (positions 20, 40, 60... don't work)
- ! format codes (like !0, !p1800) must be at EVEN byte positions WITHIN THEIR LINE SEGMENT
- Literal ! at EVEN position may be parsed as format code (user must handle manually)
- Fullwidth characters are 2 bytes and should start on even positions within their line
- Backslashes display as ¥ in Shift-JIS -> remove them
- Use … instead of ... to save 1 byte (when at even position)

IMPORTANT: This script tries to MINIMIZE byte usage, not add padding spaces.
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
    Find the character index of the first alignment problem that CAN be auto-fixed.
    Returns (index, problem_type) or None.
    
    Only flags issues we can fix without adding bytes:
    - ! format codes at ODD position: add 1 space (necessary for functionality)
    - / at ODD position: add 1 space (necessary for functionality)
    
    Does NOT flag (user must handle manually):
    - / at multiples of 20 (would require adding 2 spaces)
    - Literal ! issues (would require adding bytes)
    """
    for i, char in enumerate(text):
        # Check / line breaks - must be at even OVERALL position
        # Note: We don't auto-fix multiples of 20 (would waste 2 bytes)
        if char == '/':
            byte_pos = get_byte_position(text, i)
            if byte_pos % 2 != 0:
                return (i, 'slash_odd')
        # Check ! format codes only - must be at EVEN PER-LINE position
        elif char == '!':
            is_format_code = (i + 1 < len(text) and text[i + 1].isalnum())
            if is_format_code:
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


def cleanup_spaces(text: str) -> str:
    """
    Remove unnecessary spaces that waste bytes.
    This cleans up damage from previous script runs.
    
    - Double spaces → single space
    - Space before / → remove (fix_alignment will add back if needed)
    - Space before ! (not format code) → remove
    - Trailing spaces → remove
    """
    # Remove double/triple/etc spaces
    while '  ' in text:
        text = text.replace('  ', ' ')
    
    # Remove space before /
    text = text.replace(' /', '/')
    
    # Remove space before literal ! (not format codes)
    # We need to be careful not to break " !0" type patterns
    result = []
    i = 0
    while i < len(text):
        if text[i] == ' ' and i + 1 < len(text) and text[i + 1] == '!':
            # Check if the ! is a format code (followed by alphanumeric)
            is_format_code = (i + 2 < len(text) and text[i + 2].isalnum())
            if is_format_code:
                # Keep the space - it's before a format code
                result.append(' ')
            # else: skip the space (before literal !)
            i += 1
        else:
            result.append(text[i])
            i += 1
    text = ''.join(result)
    
    # Remove trailing spaces
    text = text.rstrip(' ')
    
    return text




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


def fix_alignment(text: str, max_iterations: int = 500) -> str:
    """
    Fix byte alignment for ! format codes and / line breaks.
    Only adds a single space when necessary to shift from odd to even position.
    
    - / line breaks: must be at EVEN overall byte position
    - ! format codes: must be at EVEN per-line byte position
    """
    if '!' not in text and '/' not in text:
        return text
    
    for _ in range(max_iterations):
        problem = find_first_problem(text)
        if problem is None:
            break
        
        problem_index, problem_type = problem
        
        # Add 1 space to shift from odd to even position
        text = text[:problem_index] + ' ' + text[problem_index:]
    
    return text

def fix_csv(csv_path: Path) -> dict:
    """Fix alignment issues in a CSV file. Prioritizes saving bytes. Returns dict of fix counts."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    fixes = {'cleanup': 0, 'alignment': 0, 'backslash': 0, 'ellipsis': 0}
    
    for row in rows:
        english = row.get('english', '')
        if not english:
            continue
        
        # 1. Remove backslashes (saves bytes, fixes display)
        fixed = fix_backslashes(english)
        if fixed != english:
            fixes['backslash'] += 1
            english = fixed
        
        # 2. Cleanup: remove double spaces, space before /, space before literal !
        fixed = cleanup_spaces(english)
        if fixed != english:
            fixes['cleanup'] += 1
            english = fixed
        
        # 3. Use … instead of ... to save 1 byte (when at even position)
        fixed = fix_ellipsis(english)
        if fixed != english:
            fixes['ellipsis'] += 1
            english = fixed
        
        # 4. Fix alignment for format codes and / (only adds spaces when necessary)
        fixed = fix_alignment(english)
        if fixed != english:
            fixes['alignment'] += 1
        
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
    totals = {'cleanup': 0, 'alignment': 0, 'backslash': 0, 'ellipsis': 0}
    
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
