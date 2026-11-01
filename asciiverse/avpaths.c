/* NetHack may be freely redistributed.  See license for details. */

/*
 * Asciiverse: where NetHack finds its files without an install by root.
 *
 * The read-only data (nhdat, sysconf, license, symbols) is the folder the
 * xnethack binary sits in when nhdat is there, which is how av installs
 * it, else the compiled-in HACKDIR (/usr/share/xnethack for the system
 * packages).  The game changes to that folder, as NetHack always does.
 *
 * Everything NetHack writes (record, logfile, xlogfile, livelog, perm,
 * the lock and level files of a game in progress, bones, save/, the
 * paniclog, dumplog/ and the player's own xnethackrc) goes to the player's
 * folder, xnethack under $XDG_DATA_HOME (else ~/.local/share), made on the
 * first run.  unixconf.h makes this folder NetHack's VAR_PLAYGROUND.
 *
 * NETHACKDIR, HACKDIR and -d still choose another playground, which then
 * holds everything, as upstream.
 */

#include "hack.h"

#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <limits.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifdef __APPLE__
#include <mach-o/dyld.h>
#endif

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

/* the folder of the running binary, or "" when it cannot be found */
static void
exe_dir(char *out, size_t outsz)
{
    char path[PATH_MAX];
    char *slash;

    out[0] = '\0';
#if defined(__linux__)
    {
        ssize_t n = readlink("/proc/self/exe", path, sizeof path - 1);

        if (n <= 0)
            return;
        path[n] = '\0';
    }
#elif defined(__APPLE__)
    {
        char raw[PATH_MAX];
        uint32_t size = sizeof raw;

        if (_NSGetExecutablePath(raw, &size) != 0 || !realpath(raw, path))
            return;
    }
#else
    return;
#endif
    if ((slash = strrchr(path, '/')) == NULL)
        return;
    *slash = '\0';
    if (strlen(path) + 1 > outsz)
        return;
    strcpy(out, path);
}

/* the folder of the game's read-only data */
const char *
av_hackdir(void)
{
    static char dir[PATH_MAX];
    char probe[PATH_MAX + 8];

    if (!dir[0]) {
        exe_dir(dir, sizeof dir - 8);
        if (dir[0]) {
            snprintf(probe, sizeof probe, "%s/nhdat", dir);
            if (access(probe, R_OK) != 0)
                dir[0] = '\0';
        }
        if (!dir[0])
            snprintf(dir, sizeof dir, "%s", HACKDIR);
    }
    return dir;
}

/* mkdir -p, owner-only searchable whatever NetHack's umask */
static void
mkpath(char *path)
{
    char *p;

    for (p = path + 1; *p; p++)
        if (*p == '/') {
            *p = '\0';
            if (mkdir(path, 0755) == 0)
                (void) chmod(path, 0755);
            *p = '/';
        }
    if (mkdir(path, 0755) == 0)
        (void) chmod(path, 0755);
}

static void
touch(const char *dir, const char *name)
{
    char path[PATH_MAX + 32];
    int fd;

    snprintf(path, sizeof path, "%s%s", dir, name);
    if ((fd = open(path, O_WRONLY | O_CREAT, 0644)) >= 0)
        (void) close(fd);
}

/* the player's own folder, ending in '/', made when it is not there yet */
const char *
av_playground(void)
{
    static char dir[PATH_MAX];
    char sub[PATH_MAX + 16];
    const char *base;

    if (dir[0])
        return dir;
    if ((base = getenv("XDG_DATA_HOME")) != NULL && *base == '/')
        snprintf(dir, sizeof dir - 16, "%s/xnethack/", base);
    else if ((base = getenv("HOME")) != NULL && *base)
        snprintf(dir, sizeof dir - 16, "%s/.local/share/xnethack/", base);
    else
        snprintf(dir, sizeof dir - 16, "./"); /* no home: the start folder */
    snprintf(sub, sizeof sub, "%ssave", dir);
    mkpath(sub);
    snprintf(sub, sizeof sub, "%sdumplog", dir);
    mkpath(sub);
    touch(dir, "record");
    touch(dir, "logfile");
    touch(dir, "xlogfile");
    touch(dir, "livelog");
    touch(dir, "perm");
    return dir;
}
