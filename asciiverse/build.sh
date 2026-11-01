#!/bin/sh
# Builds xNetHack, tty and curses in one binary, tty the default. Linux: run
# inside alpine:3.22 for a fully static binary; macOS: run on the runner,
# with CC_ARCH set to x86_64 or arm64.
#   docker run --rm -v "$PWD":/src -w /src alpine:3.22 sh asciiverse/build.sh
# Lua, which xNetHack runs its levels and dungeon in, is linked in
# statically: lib/lua-<version> is fetched from lua.org and checked against
# submodules/CHKSUMS first (what upstream's `make fetch-lua` does).
# Leaves the game in out/: xnethack, nhdat, sysconf, license and symbols,
# which is what an install holds (asciiverse/hints, asciiverse/avpaths.c).
set -eu
cd "$(dirname "$0")/.."
if [ -f /etc/alpine-release ]; then
  apk add --no-cache build-base linux-headers ncurses-dev ncurses-static zlib-dev zlib-static curl >/dev/null
  lflags="-static"
  curseslib="-lncursesw"
  sha="sha256sum"
elif [ "$(uname -s)" = Linux ]; then
  # a local glibc build to try things (needs libncurses-dev zlib1g-dev)
  lflags=""
  curseslib="-lncursesw"
  sha="sha256sum"
else
  lflags=""
  curseslib="-lncurses"
  sha="shasum -a 256"
fi
cc="cc${CC_ARCH:+ -arch $CC_ARCH}"

lua=lua-$(sed -n 's/^LUA_VERSION *= *//p' sys/unix/Makefile.top)
if [ ! -f "lib/$lua/src/lua.h" ]; then
  mkdir -p lib
  curl -fsSL -o "lib/$lua.tar.gz" "https://www.lua.org/ftp/$lua.tar.gz"
  want=$(awk -v f="$lua.tar.gz" '$2 == f { print $1 }' submodules/CHKSUMS)
  got=$($sha "lib/$lua.tar.gz" | cut -d' ' -f1)
  if [ -z "$want" ] || [ "$want" != "$got" ]; then
    echo "$lua.tar.gz: checksum $got, expected ${want:-none}" >&2
    exit 1
  fi
  tar -xzf "lib/$lua.tar.gz" -C lib
  rm -f "lib/$lua.tar.gz"
fi

sh sys/unix/setup.sh asciiverse/hints >/dev/null
# objects carry the compiler and its target, so start clean every time
make clean >/dev/null 2>&1 || true
rm -f include/nhlua.h lib/lua/*.a
mk="make CC=\"$cc\" LFLAGS=\"$lflags\" CURSESLIB=\"$curseslib\" GITINFO=0"
eval "$mk xnethack" >/dev/null
eval "$mk bogusmon data engrave epitaph oracles options quest.lua rumors shirts spec_levs check-dlb" >/dev/null
strip src/xnethack

rm -rf out && mkdir out
cp src/xnethack dat/nhdat dat/license dat/symbols sys/unix/sysconf out/
chmod 0755 out/xnethack && chmod 0644 out/nhdat out/license out/symbols out/sysconf
