# Nekketsu Nikki English Translation Project

A fan translation project to bring the **Nekketsu Seishun Nikki** (熱血青春日記 / "Diary of Zealous Youth") mode from the Japanese version of Project Justice (Moero! Justice Gakuen) to English.

## What is Nekketsu Nikki?

Nekketsu Nikki is a unique game mode exclusive to the Japanese release of Project Justice (called *Moero! Justice Gakuen* in Japan). It's a hybrid of:
- **Board game** - Move around a game board collecting events
- **Visual novel** - Character interactions with dialogue choices
- **Character creation** - Create your own student fighter

This mode was completely removed from the Western release of Project Justice due to the extensive localization work required.

## Project Structure

```
nekketsu-nikki-eng/
├── original-disc/          # Original Japanese GDI disc image
│   ├── disc.gdi
│   ├── track01.bin
│   ├── track02.raw
│   └── track03.bin
├── extracted-disc/         # Extracted files from Japanese disc
│   ├── *.AFS               # Sega AFS archives (contain game assets)
│   ├── *.BIN               # Binary/executable files
│   ├── *.PVR               # PowerVR textures
│   ├── DPETC/              # DreamPassport config/messages
│   ├── DPFONT/             # Font files
│   ├── DPSS/               # Screenshots/images (GIF)
│   ├── DPTEX/              # Textures
│   └── DPWWW/              # HTML content for browser
├── extracted-afs/          # Extracted AFS archive contents (created by scripts)
├── modified-disc-files/    # Modified files (same structure as extracted-disc)
├── translated-disc/        # Output folder for rebuilt disc image
├── scripts/                # Helper scripts for translation
│   ├── extract_all_afs.bat   # Batch extract all AFS files
│   ├── find_japanese_text.py # Find Japanese text in binaries
│   └── text_dump.py          # Dump text to CSV for translation
└── tools/
    ├── afsexplorer.exe     # AFSPacker - AFS archive tool
    └── buildgdi.exe        # GDI disc image builder
```

## Translation Workflow

### Phase 1: Asset Extraction
1. Extract AFS archives using AFSPacker (`tools/AFSPacker.exe`)
2. Identify text files and their encoding (Shift-JIS)
3. Document text locations and formats

### Phase 2: Text Translation
1. Extract all Japanese text strings (use `scripts/text_dump.py`)
2. Translate to English
3. Handle text length constraints (may need abbreviation)

### Phase 3: Asset Modification
1. Edit text files with translated content
2. Modify texture files containing Japanese text
3. Place modified files in `modified-disc-files/` maintaining directory structure

### Phase 4: Disc Rebuilding
1. Run `tools/buildgdi.exe` to create new disc image
2. Test in Dreamcast emulator (Flycast, Redream, etc.)
3. Verify text displays correctly

## Tools

### Included Tools (`tools/`)

| Tool | Description |
|------|-------------|
| `AFSPacker.exe` | [AFSPacker](https://github.com/MaikelChan/AFSPacker) - Extract and create AFS archives |
| `buildgdi.exe` | Build GDI disc images from modified files |

### AFSPacker Usage

```bash
AFSPacker -e <input_afs_file> <output_dir>  :  Extract AFS archive
AFSPacker -c <input_dir> <output_afs_file>  :  Create AFS archive
AFSPacker -i <input_afs_file>               :  Show AFS information
```

**Requires:** [.NET Runtime 6](https://dotnet.microsoft.com/download/dotnet/6.0)

### Helper Scripts (`scripts/`)

| Script | Description |
|--------|-------------|
| `extract_all_afs.bat` | Batch extract all AFS archives to `extracted-afs/` |
| `find_japanese_text.py` | Scan files for Shift-JIS Japanese text |
| `text_dump.py` | Extract strings to CSV/TXT for translation |

**Texture files that likely need translation:**

| File | Location | Description |
|------|----------|-------------|
| `OPTION01-03.PVR` | `DPTEX/` | Options menu graphics |
| `SKB_KANA.PVR` | `DPTEX/` | Soft keyboard (Japanese kana) |
| `SKB_EISU.PVR` | `DPTEX/` | Soft keyboard (alphanumeric) |
| `JYOUCYU0-2.PVR` | `DPTEX/` | Various UI text |
| `TAG_SU.PVR` | `DPTEX/` | UI tags/labels |
| Files in `XPLTEX/` | `extracted-afs/` | Player/character textures |

**Workflow for texture editing:**
1. Convert PVR → PNG using PVRTexTool or similar
2. Edit in image editor (Photoshop, GIMP, etc.)
3. Convert PNG → PVR maintaining same format/compression
4. Replace original file in `modified-disc-files/`

## Text Encoding

The game uses **Shift-JIS** encoding for Japanese text. When translating:
- Ensure output files use correct encoding
- Some text may be in custom formats within binary files
- Font glyphs may need expansion for English characters

## Font Files

Located in `DPFONT/`:

| File | Size | Description |
|------|------|-------------|
| `S18RM04P.DAT` | 18px | Small font |
| `S20RM04P.DAT` | 20px | Medium font |
| `S24RM04P.DAT` | 24px | Large font |
| `S26RM04P.DAT` | 26px | Extra large font |

These are likely bitmap fonts containing Japanese characters. For full English support, fonts may need to be:
- Analyzed to understand the format
- Modified to ensure ASCII/Latin characters display correctly
- Potentially replaced with custom fonts if format allows

## Resources

- [GameFAQs Nekketsu Nikki Guide](https://gamefaqs.gamespot.com/dreamcast/377885-project-justice/faqs/10107) - Detailed mode mechanics
- [Nekketsu Nikki Blog](https://nekketsunikki.wordpress.com/) - Fan documentation

## Contributing

This is a work in progress. Contributions welcome for:
- Text extraction scripts
- Translation work
- Technical documentation
- Testing

## Legal Notice

This project is for educational and preservation purposes. You must own a legitimate copy of Moero! Justice Gakuen to use this translation patch.