# Text Formatting Guide

Technical reference for in-game text formatting codes.

## Line Breaks

Use `/` (forward slash) to create line breaks.

```
Japanese: 君を待っていたのです。
English:  I've been waiting /for you.
```

**Important**: Like the `!` format codes, the `/` must be at an **even byte position** for the game to recognize it as a line break. Use spaces or fullwidth characters to adjust alignment if needed.

## Player Name Placeholder

Use `!0` to insert the player's character name.

```
!0 became your Partner!
```

Use `!1` for the second character reference (opponent, etc.)

```
!0 challenged !1 to battle!
```

## Color Codes

Format: `!cXX` where XX is the color code.

| Code | Color | Usage |
|------|-------|-------|
| `!c02` | Blue | Player/protagonist |
| `!c03` | Yellow | Stats, highlights |
| `!c04` | Green | Positive, allies |
| `!c05` | Pink/Red | Special, partner |
| `!c07` | White | Default text |

**CRITICAL**: The `!` character must land on an **even byte position** for color codes to work.

### Byte Alignment

- ASCII characters = 1 byte
- Fullwidth characters (Japanese, ！＋　) = 2 bytes

Use fullwidth spaces `　` (2 bytes) to pad text and ensure `!` lands on even positions.

### Example

```
!c02 1 Human !c07 ＋ !c04 1 CPU !c07 battle!
```

Count bytes from start to each `!`:
- Position 0: `!c02` ✓ (even)
- After " 1 Human " → use fullwidth space to align
- etc.

## Portrait Codes

Format: `!pXXXX!eYY`
- `!pXXXX` = Portrait ID (character)
- `!eYY` = Expression/emotion

```
!p0100!e00  → Batsu, neutral expression
!p0200!e01  → Hinata, expression 01
```

## Tips

1. Keep translations roughly the same byte length as originals
2. Test color codes in-game - alignment issues cause garbled text
3. Line breaks help fit text in dialog boxes
4. When in doubt, use fullwidth characters for padding
