# Translation Files

This folder contains CSV files with translations for Nekketsu Nikki mode.

## File Format

Each CSV file has the following columns:

| Column | Description |
|--------|-------------|
| `japanese` | Original Japanese text (copy exactly from game) |
| `english` | English translation |
| `context` | Description of where this text appears |
| `notes` | Translation notes, formatting hints |

## File Naming

Files are named: `{archive}_{file}_{category}.csv`

Example: `mgdata_62_player_select.csv` = MGDATA archive, file 00000062, player selection strings

## Formatting Rules

### Line Breaks
Use `/` for line breaks (must be at **even byte position**, like `!` codes):
```
Line 1 /Line 2 /Line 3
```

### Color Codes
| Code | Color |
|------|-------|
| `!c01` | Pink/Magenta |
| `!c02` | Green |
| `!c03` | Blue |
| `!c04` | Orange/Red |
| `!c05` | Pink |
| `!c07` | White (default) |

### ⚠️ IMPORTANT: Byte Alignment

The `!` character in color codes **must be at an EVEN byte position** in the string!

**How to ensure even alignment:**
- Count bytes from the start of the string (after the initial `!c0X`)
- ASCII characters = 1 byte each
- Fullwidth characters (like `　` or `＋`) = 2 bytes each
- Add spaces or use fullwidth space `　` to adjust alignment

**Example:**
```
!c021 Human !c07　＋　!c041 CPU !c07 battle!
```
- `!c02` at position 0 (even ✓)
- `1 Human ` = 8 bytes → `!c07` at position 12 (even ✓)
- `　＋　` = 6 bytes → `!c04` at position 22 (even ✓)
- `1 CPU ` = 6 bytes → `!c07` at position 32 (even ✓)

## Testing Translations

1. Edit CSV files in this folder
2. Run: `python scripts/replace_text.py`
3. Run: `scripts/rebuild.bat`
4. Test: `translated-disc/disc.gdi` in emulator
