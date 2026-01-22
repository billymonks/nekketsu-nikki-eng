text = "To join the festival, /there's stuff to register. /Now, select player count！"
pos = 0
for i, c in enumerate(text):
    if ord(c) < 128:
        byte_len = 1
    else:
        byte_len = 2
    if c in '/！':
        even_odd = "EVEN" if pos % 2 == 0 else "ODD"
        print(f"{repr(c)} at overall byte {pos} ({even_odd})")
    pos += byte_len
print(f"Total bytes: {pos}")
