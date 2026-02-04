# Nekketsu Nikki English Translation Project

A fan translation project to bring the **Nekketsu Seishun Nikki** (熱血青春日記 / "Diary of Zealous Youth") mode from the Japanese version of Project Justice (Moero! Justice Gakuen) to English.

## What is Nekketsu Nikki?

Nekketsu Nikki is a unique game mode exclusive to the Japanese release of Project Justice (called *Moero! Justice Gakuen* in Japan). It's a hybrid of:
- **Board game** - Move around a game board collecting events
- **Visual novel** - Character interactions with dialogue choices
- **Character creation** - Create your own student fighter

This mode was completely removed from the Western release of Project Justice due to the extensive localization work required.

## Requirements

- [.NET Runtime 6](https://dotnet.microsoft.com/download/dotnet/6.0)
- [Python 3](https://www.python.org/downloads/)

## Tools

Download these .exe files from their releases and place them in the /tools folder

| Tool | Description |
|------|-------------|
| `AFSPacker.exe` | [AFSPacker](https://github.com/MaikelChan/AFSPacker) - Extract and create AFS archives |
| `buildgdi.exe` | [GDIBuilder](https://github.com/Sappharad/GDIbuilder) - Build GDI disc images from modified files |

## How to Update Translation

1. Name original disc "disc.gdi" and place original disc files in folder /original-disc/
2. Use buildgdi to extract disc contents to /extracted-disc/ folder
3. Run extract_all_afs.bat to extract contents of afs files to /extracted-afs/ folder
4. Modify English column of CSV files: 1st_read_strings.csv, 1st_read_dangerous.csv, and files in /translations/mgdata_62_63_batches/ folder.
5. Run fix_alignment.py. This will edit translations to ensure special characters are positioned on valid bytes.
6. Run check_lengths.py. This will ensure translations fit into byte limits defined by original Japanese text.
7. If translations that are too long are found, a folder called "toolong_reports" will be created. Edit the CSV files in here and run apply_toolong_fixes.py. Repeat until no issues found.
8. Run merge_batches.py. This will merge the mgdata_62_63 files into a single csv file. (mgdata/000000062 + mgdata/000000063 had so many strings, it was crashing my computer to have them all in 1 file while editing)
9. Run replace_text.py. This will generate files in /modified-afs-contents/ and /modified-disc-files/.
10. Run rebuild.bat. Updated disc will be placed in /translated-disc/

### Helper Scripts (`scripts/`)

| Script | Description |
|--------|-------------|
| `extract_all_afs.bat` | Batch extract all AFS archives to `extracted-afs/` |

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