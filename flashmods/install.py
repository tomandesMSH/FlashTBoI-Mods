"""Build the modded game with the selected mods.

<out>/isaac_mods.swf          the game with the selected mods (built from the user's own game)
<out>/flashplayer_32_sa.exe   Adobe's Flash Player 32 projector (downloaded, checksum verified)
<out>/TBoI Flash Mods.exe     launcher, also usable as a Steam launch option
<out>/mods.json               which mods (and versions) are installed
<out>/game.txt                the game folder (the launcher sends Steam achievements with its FlashAchievements.exe)
<out>/cache/                  game SWF read earlier, downloaded release zips
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request

from . import game, releases, swf as swflib
from .mods import MODS

PROJECTOR_URL = "https://fpdownload.macromedia.com/pub/flashplayer/updaters/32/flashplayer_32_sa.exe"
PROJECTOR_SHA256 = "a4b333ac1da12026989549015303d82231982838bccfb544ba5fd188746066f0"
PROJECTOR = "flashplayer_32_sa.exe"
LAUNCHER = "TBoI Flash Mods.exe"
SWF_NAME = "isaac_mods.swf"
STATE = "mods.json"

HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def installed(out_dir):
    """Contents of mods.json: {"mods": {id: version}, "game": dir}, or {} if nothing is installed."""
    try:
        return json.load(open(os.path.join(out_dir, STATE), encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def launch_option(out_dir):
    return f'"{os.path.join(os.path.abspath(out_dir), LAUNCHER)}" %command%'


def get_projector(out_dir, log):
    path = os.path.join(out_dir, PROJECTOR)
    if os.path.exists(path):
        return path
    log("Downloading Adobe Flash Player 32 projector...")
    data = urllib.request.urlopen(PROJECTOR_URL, timeout=300).read()
    if hashlib.sha256(data).hexdigest() != PROJECTOR_SHA256:
        raise RuntimeError("The downloaded Flash Player projector has an unexpected checksum; not saved.")
    open(path, "wb").write(data)
    return path


def compile_launcher(out_path):
    """Compile launcher/FlashModsLauncher.cs with the .NET Framework compiler that comes with Windows."""
    windir = os.environ.get("WINDIR", r"C:\Windows")
    csc = next((p for p in (os.path.join(windir, "Microsoft.NET", fw, "v4.0.30319", "csc.exe")
                            for fw in ("Framework64", "Framework")) if os.path.exists(p)), None)
    if not csc:
        raise RuntimeError("csc.exe (.NET Framework 4) not found; it is needed to make the launcher")
    src = os.path.join(HERE, "launcher", "FlashModsLauncher.cs")
    r = subprocess.run([csc, "-nologo", "-target:winexe", "-optimize", "-out:" + out_path, src],
                       capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if r.returncode != 0:
        raise RuntimeError("launcher compile failed:\n" + r.stdout + r.stderr)


def write_launcher(out_dir):
    path = os.path.join(out_dir, LAUNCHER)
    bundled = os.path.join(HERE, "launcher", LAUNCHER)  # the exe build ships it precompiled
    if os.path.exists(bundled):
        shutil.copyfile(bundled, path)
    else:
        compile_launcher(path)
    return path


def install(mod_ids, game_dir, out_dir, log=print, source=None, get_proj=True):
    """Apply the selected mods (newest releases) to the game; returns the Steam launch option."""
    selected = [m for m in MODS if m["id"] in mod_ids]
    if not selected:
        raise ValueError("No mods selected.")
    cache = os.path.join(out_dir, "cache")
    os.makedirs(cache, exist_ok=True)

    payloads = []
    for m in selected:
        rel = releases.latest(m, source)
        log(f"{m['name']} {rel['version']}: downloading..." if "url" in rel else f"{m['name']} {rel['version']}: {rel['path']}")
        payloads.append((m, rel, releases.payload(m, rel, cache)))

    d = swflib.decompress(game.game_swf(game_dir, cache, log))
    digest = hashlib.sha256(d).hexdigest()
    if not all(digest in p["game_sha256"] for _, _, p in payloads):
        log("Warning: this game version differs from the one the mods were tested with (" + digest[:12] + ").")
    for m, rel, p in payloads:
        log(f"Adding {m['name']}...")
        d = swflib.apply_payload(d, p)

    os.makedirs(out_dir, exist_ok=True)
    tmp = os.path.join(out_dir, SWF_NAME + ".tmp")
    open(tmp, "wb").write(d)
    os.replace(tmp, os.path.join(out_dir, SWF_NAME))
    log("Wrote " + os.path.join(out_dir, SWF_NAME))
    if get_proj:
        get_projector(out_dir, log)
    write_launcher(out_dir)
    if os.path.exists(os.path.join(game_dir, "FlashAchievements.exe")):
        # the launcher sends Steam achievements with the game's FlashAchievements.exe
        with open(os.path.join(out_dir, "game.txt"), "w", encoding="utf-8") as f:
            f.write(os.path.abspath(game_dir) + "\n")
    state = {"mods": {m["id"]: rel["version"] for m, rel, _ in payloads}, "game": game_dir}
    with open(os.path.join(out_dir, STATE), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)
    log("Done: " + ", ".join(f"{m['name']} {rel['version']}" for m, rel, _ in payloads))
    return launch_option(out_dir)
