#!/usr/bin/env python3
"""Records asciiverse/xnethack.cast, xNetHack's catalog preview, at 100x30
(hub/RECORDING.md): Ada the Valkyrie explores the first levels, fights what
she meets and takes the stairs down, then saves. The driver reads the screen
through pyte and walks by breadth-first search (after the hack driver in
theasciiverse/netbsd-games). Several takes are played and the liveliest is
kept. Usage, from the repo root after asciiverse/build.sh, with pyte
installed:
    python3 asciiverse/record-preview.py"""
import fcntl, json, os, pty, random, select, shutil, struct, sys, tempfile, termios, time
from collections import deque

import pyte

# ncurses-style REP (CSI n b) repeats the last character; pyte lacks it
_draw = pyte.Screen.draw


def _draw_remembering(self, data):
    if data:
        self.last_char = data[-1]
    _draw(self, data)


def _repeat_last(self, n=1, *rest, **kw):
    if getattr(self, "last_char", None):
        _draw(self, self.last_char * max(1, n))


pyte.Screen.draw = _draw_remembering
pyte.Screen.repeat_last = _repeat_last
pyte.Stream.csi = dict(pyte.Stream.csi, b="repeat_last")

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAST = f"{root}/asciiverse/xnethack.cast"
COLS, ROWS = 100, 30
RC = """OPTIONS=name:Ada,role:Valkyrie,race:human,gender:female,align:neutral
OPTIONS=!tutorial,!legacy,!news,color,time,showexp
OPTIONS=autopickup,pickup_types:$?!/="+
OPTIONS=!autoquiver,pettype:cat
"""

DIRS = {(-1, 0): "h", (1, 0): "l", (0, -1): "k", (0, 1): "j",
        (-1, -1): "y", (1, -1): "u", (-1, 1): "b", (1, 1): "n"}
FLOOR = set(".#<>%)[!?/=*\"$`^{_")
ITEMS = set("%)[!?/=*\"$")


class Take:
    def __init__(self):
        self.install = tempfile.mkdtemp(prefix="xnethack-install-")
        for f in ("xnethack", "nhdat", "sysconf", "license", "symbols"):
            shutil.copy2(f"{root}/out/{f}", self.install)
        self.home = tempfile.mkdtemp(prefix="xnethack-home-")
        with open(f"{self.home}/.xnethackrc", "w") as f:
            f.write(RC)
        env = {"PATH": f"{self.install}:{os.environ['PATH']}", "HOME": self.home,
               "USER": "player", "LOGNAME": "player", "TERM": "xterm-256color",
               "COLORTERM": "truecolor", "LANG": "C.UTF-8"}
        self.screen = pyte.Screen(COLS, ROWS)
        self.stream = pyte.ByteStream(self.screen)
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.chdir(self.install)
            os.execvpe("asciinema", ["asciinema", "rec", "--overwrite", "-q", "--idle-time-limit", "2",
                "--window-size", f"{COLS}x{ROWS}", "--capture-env", "TERM,COLORTERM,LANG",
                "--title", "xNetHack", "--command", "xnethack", CAST], env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, COLS, 0, 0))
        self.start = time.time()

    def pump(self, t):
        end = time.time() + t
        while True:
            left = end - time.time()
            r, _, _ = select.select([self.fd], [], [], max(0.0, min(0.02, left)))
            if r:
                try:
                    data = os.read(self.fd, 65536)
                except OSError:
                    return False
                if not data:
                    return False
                self.stream.feed(data)
            if left <= 0:
                return True

    def key(self, k, wait=0.25):
        os.write(self.fd, k.encode() if isinstance(k, str) else k)
        self.pump(wait)

    def text(self):
        return "\n".join(self.screen.display)

    def elapsed(self):
        return time.time() - self.start

    def cell(self, x, y):
        return self.screen.buffer[y][x]

    def grid(self):
        """the map, screen rows 1 to 21; an open door (brown | or -) reads
        as '+', a closed one too: both are doorways"""
        g = []
        for y in range(1, 22):
            row = []
            for x in range(80):
                c = self.cell(x, y)
                ch = c.data or " "
                if ch in "|-" and c.fg == "brown":
                    ch = "D"
                elif ch == "+" and c.fg == "brown":
                    ch = "D"
                row.append(ch)
            g.append("".join(row))
        return g

    def finish(self):
        end = time.time() + 5
        while time.time() < end:
            if not self.pump(0.1):
                break
            if os.waitpid(self.pid, os.WNOHANG)[0]:
                break
        else:
            os.kill(self.pid, 15)
        try:
            os.waitpid(self.pid, 0)
        except ChildProcessError:
            pass
        shutil.rmtree(self.install, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)


def doorway(g, c):
    x, y = c
    if g[y][x] == "D":
        return True
    vert = 0 < y < 20 and g[y - 1][x] in "|-" and g[y + 1][x] in "|-"
    horiz = 0 < x < 79 and g[y][x - 1] in "|-" and g[y][x + 1] in "|-"
    return vert or horiz


def step(g, me, want, monster, avoid):
    for (dx, dy), k in DIRS.items():
        x, y = me[0] + dx, me[1] + dy
        if 0 <= y < 21 and 0 <= x < 80 and monster(g[y][x]) and (x, y) not in avoid:
            if dx and dy and (doorway(g, me) or doorway(g, (x, y))):
                continue
            return k
    seen = {me: None}
    q = deque([me])
    goal = None
    while q:
        cur = q.popleft()
        if cur != me and want(g, cur):
            goal = cur
            break
        for (dx, dy) in DIRS:
            x, y = cur[0] + dx, cur[1] + dy
            if not (0 <= y < 21 and 0 <= x < 80) or (x, y) in seen or (x, y) in avoid:
                continue
            ch = g[y][x]
            if not (ch in FLOOR or ch == "D" or ch.isalpha()):
                continue
            if dx and dy and (doorway(g, cur) or doorway(g, (x, y))):
                continue
            seen[(x, y)] = cur
            q.append((x, y))
    if goal is None:
        return None
    while seen[goal] != me:
        goal = seen[goal]
    return DIRS[(goal[0] - me[0], goal[1] - me[1])]


def take():
    t = Take()
    t.pump(2.0)
    visited = set()
    level, stuck, last = 1, 0, None
    pet = None
    while t.elapsed() < 50:
        s = t.text()
        top = t.screen.display[0]
        if "--More--" in s:
            t.key("\r", 0.3)
            continue
        if "Really attack" in top:
            t.key("n", 0.3)
            continue
        if "[yn" in top or "[ynq" in top or "What do you" in top or "(end)" in s:
            t.key("\x1b", 0.3)
            continue
        g = t.grid()
        me = (t.screen.cursor.x, t.screen.cursor.y - 1)
        if not (0 <= me[1] < 21 and 0 <= me[0] < 80) or g[me[1]][me[0]] != "@":
            t.key("\x1b", 0.3)
            continue
        if pet is None:
            for (dx, dy) in DIRS:
                x, y = me[0] + dx, me[1] + dy
                if 0 <= y < 21 and g[y][x] == "f":
                    pet = "f"
        visited.add(me)
        hurry = t.elapsed() > 16 * level
        stairs = [(x, y) for y in range(21) for x in range(80) if g[y][x] == ">"]

        def want(gr, c):
            ch = gr[c[1]][c[0]]
            if hurry and ch == ">":
                return True
            if ch in ITEMS and c not in visited:
                return True
            if c in visited:
                return False
            if ch in ".#D":
                for (dx, dy) in DIRS:
                    x, y = c[0] + dx, c[1] + dy
                    if 0 <= y < 21 and 0 <= x < 80 and gr[y][x] == " ":
                        return True
            return False

        def monster(ch):
            return ch.isalpha() and ch != pet

        petpos = {(x, y) for y in range(21) for x in range(80) if pet and g[y][x] == pet}
        k = None if stuck >= 3 else step(g, me, want, monster, petpos)
        if k is None:
            k = random.choice(list(DIRS.values()))
            stuck = 0
        t.key(k, 0.22)
        after = (t.screen.cursor.x, t.screen.cursor.y - 1)
        stuck = stuck + 1 if after == me and "You" not in t.screen.display[0] else 0
        # standing on the stairs down late enough: take them
        if hurry and stairs and after == stairs[0]:
            t.key(">", 0.8)
            level += 1
            visited.clear()
    while "--More--" in t.text():
        t.key("\r", 0.3)
    t.key("\x1b", 0.3)
    t.key("S", 0.6)
    t.key("y", 1.0)
    t.finish()


def score():
    lines = open(CAST).read().splitlines()
    idle = json.loads(lines[0]).get("idle_time_limit") or 2
    length = sum(min(json.loads(l)[0], idle) for l in lines[1:])
    if length < 30 or length > 60:
        return -1, length
    text = "".join(json.loads(l)[2] for l in lines[1:] if json.loads(l)[1] == "o")
    hits = text.count("You hit") + 3 * (text.count("You kill") + text.count("You destroy"))
    deeper = 6 * ("Dlvl:2" in text) + 6 * ("Dlvl:3" in text)
    return 2 * hits + deeper - 20 * ("You die" in text), length


def main():
    best = None
    for n in range(6):
        take()
        sc, length = score()
        print(f"take {n + 1}: score {sc}, {length:.0f} s", file=sys.stderr)
        if best is None or sc > best[0]:
            best = (sc, open(CAST).read())
        if sc >= 24:
            break
    with open(CAST, "w") as f:
        f.write(best[1])
    print(f"{CAST}: score {best[0]}", file=sys.stderr)


if __name__ == "__main__":
    main()
