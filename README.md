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

## Key Files Analysis

### AFS Archives (Primary Game Content)

| File | Size | Likely Contents |
|------|------|-----------------|
| `UDCSDM.AFS` | 450 MB | **Largest file** - Likely contains story data, cutscenes, Nikki mode content |
| `ZADX0.AFS` | 106 MB | Audio/ADX files (music, voice) |
| `XPLTEX.AFS` | 26 MB | Player textures |
| `YPLPACK.AFS` | 21 MB | Player data packages |
| `MGDATA.AFS` | 11.6 MB | Mini-game data (possibly Nikki mode) |
| `WGAME.AFS` | 11.5 MB | Game data |
| `WISOUND.AFS` | 11.6 MB | Sound effects |
| `WPLMOT.AFS` | 11.8 MB | Player motion data |
| `WMENU.AFS` | 6 MB | **Menu data** - May contain Nikki menu text |
| `SDEMO.AFS` | 9.5 MB | Story demo data |
| `ODEMO.AFS` | 6.3 MB | Opening demo |
| `ZADX1.AFS`, `ZADX2.AFS` | 7-8 MB | Additional audio |

### Binary Files

| File | Size | Description |
|------|------|-------------|
| `3SYS.BIN` | 225 MB | System data - likely contains embedded text |
| `1ST_READ.BIN` | 3.8 MB | Main executable |
| `2_DP.BIN` | 3.3 MB | DreamPassport executable |

### Other Directories

- `DPETC/` - DreamPassport configuration (MESSAGE.INI contains UI text in Shift-JIS)
- `DPFONT/` - Font files (S18RM04P.DAT, S20RM04P.DAT, etc.)
- `DPTEX/` - UI textures

## Translation Workflow

### Phase 1: Asset Extraction
1. Extract AFS archives using AFSPacker (`tools/afsexplorer.exe`)
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
# Extract an AFS archive
afsexplorer.exe -e <input.afs> <output_dir>

# Create an AFS archive from folder
afsexplorer.exe -c <input_dir> <output.afs>

# Show AFS archive info
afsexplorer.exe -i <input.afs>
```

**Requires:** [.NET Runtime 6](https://dotnet.microsoft.com/download/dotnet/6.0)

### Helper Scripts (`scripts/`)

| Script | Description |
|--------|-------------|
| `extract_all_afs.bat` | Batch extract all AFS archives to `extracted-afs/` |
| `find_japanese_text.py` | Scan files for Shift-JIS Japanese text |
| `text_dump.py` | Extract strings to CSV/TXT for translation |

### External Tools Needed

- **Hex Editor** - For binary analysis (HxD, 010 Editor, etc.)
- **Dreamcast Emulator** - For testing (Flycast recommended)

### Image/Texture Editing Tools

The game uses **PVR (PowerVR)** textures with GBIX headers. These require special tools:

| Tool | Description | Link |
|------|-------------|------|
| **PVRTexTool** | Official PowerVR texture tool (convert PVR ↔ PNG) | [Imagination Technologies](https://developer.imaginationtech.com/pvrtextool/) |
| **TextureConverter** | Dreamcast-specific PVR converter | Search romhacking communities |
| **pvr2png** | Simple command-line converter | GitHub |
| **Noesis** | Multi-format 3D/texture viewer/converter | richwhitehouse.com |

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