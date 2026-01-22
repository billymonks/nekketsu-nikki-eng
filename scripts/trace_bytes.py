#!/usr/bin/env python3
"""
Trace byte positions in strings to understand game text parsing.
Tests different hypotheses about how / line breaks affect byte counting.
"""

def get_byte_len(char: str) -> int:
    """Get byte length of a character in Shift-JIS."""
    return 1 if ord(char) < 128 else 2

def trace_counting_slash(text: str):
    """Trace assuming / is counted as a byte."""
    print(f"\n=== Counting / as 1 byte ===")
    print(f"Text: {text}")
    pos = 0
    for i, char in enumerate(text):
        byte_len = get_byte_len(char)
        even_odd = "EVEN" if pos % 2 == 0 else "ODD"
        if char in ('/', '!', '！', '？', '…') or (char == '!' and i+1 < len(text) and text[i+1].isalnum()):
            print(f"  {repr(char):6} at byte {pos:3} ({even_odd}) <- IMPORTANT")
        pos += byte_len
    print(f"  Total bytes: {pos}")

def trace_not_counting_slash(text: str):
    """Trace assuming / is NOT counted (control code)."""
    print(f"\n=== NOT counting / (control code) ===")
    print(f"Text: {text}")
    pos = 0
    for i, char in enumerate(text):
        byte_len = get_byte_len(char)
        even_odd = "EVEN" if pos % 2 == 0 else "ODD"
        if char in ('/', '!', '！', '？', '…') or (char == '!' and i+1 < len(text) and text[i+1].isalnum()):
            print(f"  {repr(char):6} at byte {pos:3} ({even_odd}) <- IMPORTANT")
        # Don't count / in byte position
        if char != '/':
            pos += byte_len
    print(f"  Total bytes (excluding /): {pos}")

def trace_per_line(text: str):
    """Trace assuming each line (after /) restarts at byte 0."""
    print(f"\n=== Per-line counting (/ resets to 0) ===")
    print(f"Text: {text}")
    lines = text.split('/')
    for line_num, line in enumerate(lines):
        print(f"  Line {line_num}: {repr(line)}")
        pos = 0
        for i, char in enumerate(line):
            byte_len = get_byte_len(char)
            even_odd = "EVEN" if pos % 2 == 0 else "ODD"
            if char in ('!', '！', '？', '…'):
                print(f"    {repr(char):6} at byte {pos:3} ({even_odd})")
            pos += byte_len

# Test strings from the game
test_strings = [
    "Registration complete!/Now you can join the festival！/Have fun！",
    "I'll decide play order. /Press　!a button!",
    "Register the CPU！/Select !c03'Random'!c07 to /automatically choose a CPU.",
    "Hey, Roy. /You look bored.",
]

for text in test_strings:
    print("\n" + "="*80)
    trace_counting_slash(text)
    trace_not_counting_slash(text)
    trace_per_line(text)
