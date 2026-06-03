# mgrepack v0.9.1 @pomegd

A tool to extract and rebuild textures and other assets from `MGDATA.AFS` of
Project Justice (Dreamcast).

## Usage

### Extract

```sh
mgrepack.exe extract -in MGDATA.AFS
```

Contents are unpacked into the `extract/` folder next to the executable.
`*.bin` files are model data or other non-image data and are preserved as-is.

### Replacement

Copy any image you want to replace into the `replacement/` folder, keeping
the same filename as the one in `extract/`. Edit it with your image tool.

### Repack

```sh
mgrepack.exe repack
```

`MGDATA.AFS` is rebuilt. Any file present in `replacement/` takes precedence
over the matching file in `extract/`; everything else is pulled from
`extract/` as-is.

---

## Disclaimer

This is an unofficial, fan-made tool and is not affiliated with, endorsed by,
or authorized by CAPCOM Co., Ltd. or any of its affiliates. The names and
trademarks of "Moero! Justice Gakuen / Project Justice", as well as all
copyrights in the in-game data, belong solely to CAPCOM Co., Ltd.

The author assumes no liability for any damages or losses arising from the
use of this tool. Use at your own risk.

For the license terms of this tool itself, see `LICENSE` and
`THIRD_PARTY_NOTICES.md`.
