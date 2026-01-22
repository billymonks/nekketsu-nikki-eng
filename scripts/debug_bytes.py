#!/usr/bin/env python3
"""Debug byte positions for specific strings."""

def trace_string(label, text):
    print(f"\n{'='*70}")
    print(f"{label}")
    print(f"Text: {text}")
    print(f"{'='*70}")
    
    overall_pos = 0
    line_start = 0
    
    for i, char in enumerate(text):
        byte_len = 1 if ord(char) < 128 else 2
        line_pos = overall_pos - line_start
        
        if char in '!/！' or ord(char) > 127:
            overall_even = "EVEN" if overall_pos % 2 == 0 else "ODD"
            line_even = "EVEN" if line_pos % 2 == 0 else "ODD"
            char_type = "2-BYTE" if ord(char) > 127 else "ASCII"
            if char == '!' and i+1 < len(text) and text[i+1].isalnum():
                char_type = "FORMAT"
            # Check if 2-byte char is at odd overall position (BAD)
            bad_2byte = (byte_len == 2 and overall_pos % 2 != 0)
            # Check if format code is at odd per-line position (BAD)
            bad_format = (char_type == "FORMAT" and line_pos % 2 != 0)
            # Check if / is at odd overall position (BAD)
            bad_slash = (char == '/' and overall_pos % 2 != 0)
            status = "BAD!" if (bad_2byte or bad_format or bad_slash) else "OK"
            print(f"  {repr(char):6} at overall={overall_pos:2} ({overall_even}), line={line_pos:2} ({line_even}), {char_type} {status}")
        
        if char == '/':
            line_start = overall_pos + byte_len
            
        overall_pos += byte_len
    
    print(f"Total bytes: {overall_pos}")

# Final fixed versions
trace_string("FINAL: batch_052 line 53",
             "Select roulette /!c03A: Run 5-10 spaces  !c02(HP-!0!c02)  /!c05B: Walk 1-6 spaces!c07")

trace_string("FINAL: batch_005 line 57",
             "!c03ATK !c07 EXP +  !0 points !")
