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
    'a': 2, 'b': 2, 'x': 2, 'y': 2, 'h': 2,  # buttons
    'c': 4, 'p': 6, 'e': 4,
}


def get_format_code_length(text: str, pos: int) -> int:
    """Return character length of format code at pos, or 0 if not a format code."""
    if pos >= len(text) or text[pos] != '!' or pos + 1 >= len(text):
        return 0
    return FORMAT_CODE_PATTERNS.get(text[pos + 1], 0)


def is_invisible_format_code(text: str, pos: int) -> bool:
    """
    Check if format code at pos is invisible (just changes state, no display).
    Invisible: !c## (color), !p#### (portrait), !e## (expression)
    Visible: !a, !b, !x, !y (buttons), !0-!9 (player names)
    """
    if pos + 1 >= len(text) or text[pos] != '!':
        return False
    next_char = text[pos + 1]
    # Invisible codes: c (color), p (portrait), e (expression)
    return next_char in 'cpe'


def get_position_for_format_code(text: str, char_index: int) -> int:
    """
    Get byte position for format code alignment.
    Format codes count as 0 bytes (they're invisible).
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
            # Format codes = 0 bytes (invisible, don't affect alignment)
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
                # ODD position - need to add space
                # If preceded by fullwidth chars, insert space BEFORE them
                # (so fullwidth chars stay at even position)
                insert_pos = len(result)
                while insert_pos > 0 and ord(result[insert_pos - 1]) >= 128:
                    insert_pos -= 1
                result.insert(insert_pos, ' ')
            result.append('/')
            i += 1
            
        elif char == '!':
            fc_len = get_format_code_length(text, i)
            if fc_len > 0:
                # Format code - check alignment (format codes count as 0 bytes)
                pos = get_position_for_format_code(current, len(current))
                has_space_before = result and result[-1] == ' '
                after_pos = i + fc_len
                has_space_after = after_pos < len(text) and text[after_pos] == ' '
                invisible = is_invisible_format_code(text, i)
                
                # For visible codes, ensure space BEFORE if preceded by letter
                if not invisible and not has_space_before and result and result[-1].isalpha():
                    result.append(' ')
                    has_space_before = True  # Update for subsequent logic
                
                if pos % 2 != 0:
                    # ODD position - need to shift by 1
                    if has_space_after and not has_space_before and invisible:
                        # Move space from after to before (only for invisible codes)
                        result.append(' ')
                        result.append(text[i:i + fc_len])
                        i = after_pos + 1  # Skip the space after
                    else:
                        # Add space before (for alignment)
                        if not has_space_before:
                            result.append(' ')
                        result.append(text[i:i + fc_len])
                        i += fc_len
                        # If invisible and had space both before and after, skip after
                        if invisible and has_space_before and has_space_after:
                            i += 1
                        # For visible codes, ADD space after if next char is a letter
                        elif not invisible and i < len(text) and text[i].isalpha():
                            result.append(' ')
                else:
                    # EVEN position - OK
                    result.append(text[i:i + fc_len])
                    i += fc_len
                    # Only skip trailing space for invisible codes to avoid visual double
                    if invisible and has_space_before and has_space_after:
                        i += 1
                    # For visible codes, ADD space after if next char is a letter
                    elif not invisible and i < len(text) and text[i].isalpha():
                        result.append(' ')
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
        elif char == '！':
            # Fullwidth ！ - check position
            pos = get_position_for_slash(current, len(current))
            if pos % 2 != 0:
                # ODD position - fullwidth would break, use halfwidth
                result.append('!')
            else:
                # EVEN position - fullwidth OK
                result.append('！')
            i += 1
        elif ord(char) >= 128:
            # Other fullwidth/2-byte characters - need EVEN position
            pos = get_position_for_slash(current, len(current))
            if pos % 2 != 0:
                # ODD position - add space before to shift to EVEN
                result.append(' ')
            result.append(char)
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


def fix_format_code_spaces(text: str) -> str:
    """
    Remove space AFTER format code if there's also space BEFORE.
    "word !c07 word" renders as "word  word" (bad)
    "word !c07word" renders as "word word" (good)
    """
    result = []
    i = 0
    while i < len(text):
        fc_len = get_format_code_length(text, i)
        if fc_len > 0:
            # Check if space before AND space after
            has_space_before = result and result[-1] == ' '
            after_pos = i + fc_len
            has_space_after = after_pos < len(text) and text[after_pos] == ' '
            
            result.append(text[i:i + fc_len])
            i += fc_len
            
            if has_space_before and has_space_after:
                # Skip the space after (remove it)
                i += 1
        else:
            result.append(text[i])
            i += 1
    return ''.join(result)


def process_text(text: str) -> str:
    """Apply all fixes in order."""
    text = cleanup(text)
    text = fix_ellipsis(text)
    text = fix_long_lines(text)          # Move words to next line if too long
    text = fix_all_left_to_right(text)   # Fix alignment (/, format codes, !)
    # Final cleanup to remove any double spaces introduced
    while '  ' in text:
        text = text.replace('  ', ' ')
    return text


def get_display_length(text: str) -> int:
    """
    Calculate display length of a line segment.
    - !c## (colors) = 0 bytes (don't display)
    - !p#### (portraits) = 0 bytes
    - !e## (expressions) = 0 bytes
    - !a, !b, !x, !y (buttons) = 0 bytes? or some length - assuming 0 for now
    - !0-!9 (player names) = 10 bytes (max name length)
    - Other chars = 1 byte (ASCII) or 2 bytes (fullwidth)
    """
    length = 0
    i = 0
    while i < len(text):
        fc_len = get_format_code_length(text, i)
        if fc_len > 0:
            # Check which type of format code
            next_char = text[i + 1] if i + 1 < len(text) else ''
            if next_char.isdigit():
                # !0-!9 player names = 10 bytes max
                length += 10
            # !c, !p, !e, !a, !b, !x, !y = 0 display bytes
            i += fc_len
        else:
            length += 1 if ord(text[i]) < 128 else 2
            i += 1
    return length


def fix_long_lines(text: str, max_bytes: int = 39) -> str:
    """
    Fix overly long lines by adjusting / positions or inserting new /.
    
    - Non-last line too long: Move / left to shorten
    - Last line too long: Try moving / right, else insert new /
    - No / available: Insert new /
    """
    max_iterations = 50
    
    for _ in range(max_iterations):
        segments = text.split('/')
        
        # Find first problem
        problem_idx = None
        for idx, segment in enumerate(segments):
            if get_display_length(segment.rstrip(' ')) > max_bytes:
                problem_idx = idx
                break
        
        if problem_idx is None:
            break  # No problems
        
        fixed = False
        problem_segment = segments[problem_idx]
        
        # Case: Last line too long
        if problem_idx == len(segments) - 1 and len(segments) > 1:
            first_space = problem_segment.find(' ')
            if first_space > 0:
                # Check if moving / right would make previous line too long
                prev_segment = segments[-2]
                word_to_move = problem_segment[:first_space]
                new_prev_len = get_display_length((prev_segment + ' ' + word_to_move).rstrip(' '))
                
                if new_prev_len <= max_bytes:
                    # Safe to move / right
                    new_prev = prev_segment + ' ' + word_to_move
                    new_last = problem_segment[first_space + 1:]
                    segments[-2] = new_prev
                    segments[-1] = new_last
                    text = '/'.join(segments)
                    fixed = True
                else:
                    # Can't move / right, insert new / in last line instead
                    last_space = problem_segment.rfind(' ')
                    if last_space > 0:
                        new_current = problem_segment[:last_space]
                        new_next = problem_segment[last_space + 1:]
                        segments = segments[:-1] + [new_current, new_next]
                        text = '/'.join(segments)
                        fixed = True
        
        # Case: Non-last line too long - move / LEFT
        elif problem_idx < len(segments) - 1:
            last_space = problem_segment.rfind(' ')
            if last_space > 0:
                new_current = problem_segment[:last_space]
                new_next = problem_segment[last_space + 1:] + ' ' + segments[problem_idx + 1]
                
                parts = segments[:problem_idx] + [new_current, new_next] + segments[problem_idx + 2:]
                text = '/'.join(parts)
                fixed = True
        
        # Case: Still not fixed - insert new /
        if not fixed:
            last_space = problem_segment.rfind(' ')
            if last_space > 0:
                new_current = problem_segment[:last_space]
                new_next = problem_segment[last_space + 1:]
                
                parts = segments[:problem_idx] + [new_current, new_next] + segments[problem_idx + 1:]
                text = '/'.join(parts)
                fixed = True
        
        if not fixed:
            break  # Can't fix
    
    return text


def find_long_lines(text: str, max_bytes: int = 39) -> list[tuple[int, str, int]]:
    """
    Find line segments that exceed max_bytes.
    Returns list of (line_number, segment_text, byte_count).
    Trailing spaces are ignored (whitespace extending out of window is fine).
    """
    problems = []
    segments = text.split('/')
    for idx, segment in enumerate(segments):
        # Strip trailing spaces - they don't matter if they extend past window
        display_len = get_display_length(segment.rstrip(' '))
        if display_len > max_bytes:
            problems.append((idx + 1, segment, display_len))
    return problems


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
            # print(f"  {batch_file.name}: {result['changes']} changes")
            total += result['changes']
    
    print(f"\nTotal: {total} changes" if total else "\nNo changes needed")


def report_long_lines(csv_path: Path) -> list[dict]:
    """Find all lines that are too long in a CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        content = f.read().replace('\x00', '')
    
    rows = list(csv.DictReader(io.StringIO(content)))
    issues = []
    
    for row_idx, row in enumerate(rows, start=2):  # +2 for header and 1-based
        english = row.get('english', '')
        if not english:
            continue
        
        problems = find_long_lines(english)
        for line_num, segment, byte_count in problems:
            issues.append({
                'row': row_idx,
                'line': line_num,
                'bytes': byte_count,
                'text': segment[:50] + ('...' if len(segment) > 50 else ''),
                'full_text': english
            })
    
    return issues


def report_long_lines_batch(batch_dir: Path):
    """Report all too-long lines in batch CSV files."""
    batch_files = sorted(batch_dir.glob("*_batch_*.csv"))
    total_issues = 0
    
    for batch_file in batch_files:
        issues = report_long_lines(batch_file)
        if issues:
            # print(f"\n{batch_file.name}:")
            # for issue in issues:
                # print(f"  Row {issue['row']}, Line {issue['line']}: {issue['bytes']} bytes")
                # print(f"    {issue['text']}")
            total_issues += len(issues)
    
    print(f"\nTotal: {total_issues} lines over 39 bytes")


if __name__ == "__main__":
    import sys
    
    project_dir = Path(__file__).parent.parent
    batch_dir = project_dir / "translations" / "mgdata_62_63_batches"
    
    if not batch_dir.exists():
        print(f"ERROR: Batch directory not found: {batch_dir}")
        exit(1)
    
    # Check for --check-length flag
    if len(sys.argv) > 1 and sys.argv[1] == '--check-length':
        print("Checking for lines over 39 bytes...")
        report_long_lines_batch(batch_dir)
    else:
        print("Fixing alignment...")
        fix_batch_dir(batch_dir)
        
        print("\nValidating...")
        from validate_translations import validate_batch_dir
        validate_batch_dir(batch_dir)
