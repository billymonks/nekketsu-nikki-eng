# Nekketsu Nikki English Translation Project

A fan translation project to bring the **Nekketsu Seishun Nikki** (熱血青春日記 / "Diary of Zealous Youth") mode from the Japanese version of Project Justice (Moero! Justice Gakuen) to English.

## What is Nekketsu Nikki?

Nekketsu Nikki is a unique game mode exclusive to the Japanese release of Project Justice (called *Moero! Justice Gakuen* in Japan). It's a hybrid of:
- **Board game** - Move around a game board collecting events
- **Visual novel** - Character interactions with dialogue choices
- **Character creation** - Create your own student fighter

This mode was completely removed from the Western release of Project Justice due to the extensive localization work required.

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

Download these .exe files from their releases and place them in the /tools folder

| Tool | Description |
|------|-------------|
| `AFSPacker.exe` | [AFSPacker](https://github.com/MaikelChan/AFSPacker) - Extract and create AFS archives |
| `buildgdi.exe` | [GDIBuilder](https://github.com/Sappharad/GDIbuilder) - Build GDI disc images from modified files |

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

**Workflow for texture editing:**
1. Convert PVR → PNG using PVRTexTool or similar
2. Edit in image editor (Photoshop, GIMP, etc.)
3. Convert PNG → PVR maintaining same format/compression
4. Replace original file in `modified-disc-files/`

## Text Encoding

The game uses **Shift-JIS** encoding for Japanese text. When translating:
- Ensure output files use correct encoding
- Some text may be in custom formats within binary files

## Resources

- [GameFAQs Nekketsu Nikki Guide](https://gamefaqs.gamespot.com/dreamcast/377885-project-justice/faqs/10107) - Detailed mode mechanics
- [Capcom Fighting Collection 2](https://www.capcom-games.com/cfc2/en-us/) - Support Capcom's commendable efforts in bringing their classic library to modern platforms

## Contributing

This is a work in progress. Contributions welcome for:
- Text/image extraction scripts
- Translation work/localization
- Technical documentation
- Testing

## Legal Notice

This project is for educational and preservation purposes. You must own a legitimate copy of Moero! Justice Gakuen to use this translation patch.