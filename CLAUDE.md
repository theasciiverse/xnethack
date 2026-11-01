# xNetHack (Asciiverse packaging)

xNetHack 10.0 by copperwater and contributors, a NetHack 5.0.0 variant
(NGPL), packaged for the Asciiverse catalog (id `xnethack`, binary
`xnethack`) and as system packages. Not our code: keep changes small, list
every one in PATCHES.md, guard source changes with `#ifdef AV_PATHS`.

- `upstream` is github.com/copperwater/xNetHack; branch `asciiverse` starts
  at tag `xnh10.0`. For a new release, rebase onto its tag.
- The packaging is a port of theasciiverse/nethack's (remote `avnethack`):
  `asciiverse/avpaths.c`, `asciiverse/hints`, `asciiverse/build.sh`, and
  the source patches. Fix things in both when they apply to both.
- Build: `sh asciiverse/build.sh` (Ubuntu: libncurses-dev zlib1g-dev;
  release builds run it in alpine:3.22 for a static binary). Output in
  `out/`: xnethack, nhdat, sysconf, license, symbols. Run `out/xnethack`.
- Player files: `~/.local/share/xnethack` (saves, scores, dumplogs,
  `xnethackrc`).
- Release: tag `v10.0-av.<n>` and push it.
- Preview: `python3 asciiverse/record-preview.py` (pyte, asciinema 3);
  plays six takes and keeps the liveliest.
