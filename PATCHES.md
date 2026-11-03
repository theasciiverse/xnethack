# Changes from upstream

This is the Asciiverse packaging of xNetHack 10.0 by copperwater and
contributors, a variant of NetHack 5.0.0, under the NetHack General
Public License (`dat/license`, SPDX `NGPL`). The `asciiverse` branch
starts at upstream's tag `xnh10.0` (commit `6eef394`, 2026-05-26) from
[copperwater/xNetHack](https://github.com/copperwater/xNetHack), the
`upstream` remote. Everything after it is ours.

xNetHack and NetHack 5.0.0 share their build and file handling, so these
are the changes of our NetHack 5.0.0 packaging (theasciiverse/nethack,
its PATCHES.md has the full reasoning), carried over with xNetHack's
names. Changed files say so beside each change, as the licence asks.

## Where the files go

- Read-only data (`nhdat`, `sysconf`, `license`, `symbols`): the folder
  the binary sits in when `nhdat` is there, which is how av installs it,
  else `/usr/share/xnethack`, the `HACKDIR` compiled in for the system
  packages (`asciiverse/avpaths.c`, `av_hackdir()`; Linux reads
  `/proc/self/exe`, macOS `_NSGetExecutablePath`).
- Everything written (record, logfile, xlogfile, livelog, perm, lock and
  level files, bones, `save/`, paniclog, `dumplog/`): `xnethack` under
  `$XDG_DATA_HOME`, else `~/.local/share/xnethack`, made with its empty
  files on the first run (`av_playground()`, `include/unixconf.h` makes
  it the `VAR_PLAYGROUND`).
- `sys/unix/unixmain.c`: `chdirx()` uses `av_hackdir()` where it used
  `HACKDIR`. `NETHACKDIR`, `HACKDIR` and `-d` still pick another
  playground, as upstream.
- `src/cfgfiles.c`: without `~/.xnethackrc` (still read first), the
  options file is `xnethackrc` in the player's folder, which is also
  where `#saveoptions` writes.
- `src/windows.c`: relative `DUMPLOGFILE` and `DUMPHTMLFILE` names are in
  the player's folder (xNetHack adds the HTML dump to NetHack's text
  one; it is not compiled in here, as upstream's own hints leave it out),
  and `sys/unix/sysconf` turns the end-of-game dump on as
  `dumplog/<name>.<date>.txt`.

All of these are guarded by `#ifdef AV_PATHS`, defined only by
`asciiverse/hints`.

## Build

- `asciiverse/hints`: one binary with the tty and curses interfaces, tty
  the default (`OPTIONS=windowtype:curses` picks curses); `DLB`,
  `SELF_RECOVER`, `DUMPLOG`, zlib-compressed saves linked in
  (`ZLIB_COMP`), no crash reports through a browser or gdb
  (`NOCRASHREPORT`, `NOPANICTRACE`). `NOTPARMDECL`, as upstream's own
  hints have it: otherwise `win/tty/termcap.c` declares `tparm()` again
  old-style over the prototype in macOS's `curses.h`, which Apple clang
  rejects as conflicting types.
- `asciiverse/build.sh`: fully static Linux in Alpine (musl, ncursesw and
  zlib linked in), macOS per architecture (`CC_ARCH`), and a plain glibc
  build on other Linux to try things locally (`-lncursesw`). Lua 5.4.8 is
  fetched from lua.org (with retries, lua.org sometimes drops the
  connection), checked against `submodules/CHKSUMS`, and linked
  in statically. Builds xNetHack's extra `shirts` data file with the rest.
  Leaves the install in `out/`.
- `asciiverse/nfpm.yaml`: .deb, .rpm, .apk and Arch packages:
  `/usr/bin/xnethack`, data in `/usr/share/xnethack`, Guidebook and
  licence in `/usr/share/doc/xnethack`, the man page. Nothing setgid, no
  menu entry.
- `.github/workflows/release.yml`: builds all of it on a tag
  `v10.0-av.<n>`; the av archive also carries the Guidebook, the man page
  and `xnh-changelog-10.0.md`.
- `asciiverse/record-preview.py`: records `asciiverse/xnethack.cast`, a
  Valkyrie exploring by breadth-first search over the screen (pyte), best
  of six takes.
- `.gitignore`: `out/` and `dist/`.

## Not built

- `recover` (`SELF_RECOVER` does its work), the X11, Qt and Windows GUI
  interfaces, sound libraries, and Windows (as for NetHack).

## Not changed

- Succubi and incubi keep upstream's seduction behaviour (`SEDUCE` is on
  in `sysconf`), as in our NetHack package.
