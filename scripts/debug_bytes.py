#!/usr/bin/env python3
"""Debug byte positions for specific strings."""

def trace_format_codes(label, text):
    overall_pos = 0
    positions = []
    
    for i, char in enumerate(text):
        byte_len = 1 if ord(char) < 128 else 2
        
        if char == '!' and i+1 < len(text) and text[i+1].isalnum():
            positions.append((overall_pos, text[i:i+4] if i+4 <= len(text) else text[i:]))
            
        overall_pos += byte_len
    
    print(f"{label}: {positions}, total={overall_pos}")

# Check all stat EXP lines after fix
print("After fixes - all should have !0 at position 20+:")
trace_format_codes("HP +", "!c03HP  !c07 EXP +  !0 points !")
trace_format_codes("HP -", "!c03HP  !c07 EXP -  !0 points !")
trace_format_codes("GUTS +", "!c03GUTS!c07 EXP +  !0 points !")
trace_format_codes("GUTS -", "!c03GUTS!c07 EXP -  !0 points !")
trace_format_codes("ATK +", "!c03ATK !c07 EXP +  !0 points !")
trace_format_codes("INT +", "!c03INT !c07 EXP +  !0 points !")
trace_format_codes("DEF +", "!c03DEF !c07 EXP +  !0 points !")
trace_format_codes("Potential +", "!c03Potential !c07 EXP +  !0 points !")
