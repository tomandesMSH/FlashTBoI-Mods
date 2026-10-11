"""Find the installed game and read its SWF.

The Steam game (Isaac.exe) is an MDM Zinc projector that keeps the game SWF encrypted. A copy of the game folder is
started from a temporary folder for a few seconds and the decrypted SWF is read from its memory. The installation
itself is never modified. The SWF is cached (keyed by Isaac.exe's size and date), so changing the mod selection later
doesn't need the game to be started again.
"""
import ctypes
import os
import shutil
import struct
import subprocess
import tempfile
import time

from . import swf as swflib

STEAM_DIRS = [r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"]
GAME_SUBDIR = os.path.join("steamapps", "common", "The Binding Of Isaac")


def find_game():
    for steam in STEAM_DIRS:
        lib_file = os.path.join(steam, "steamapps", "libraryfolders.vdf")
        libs = [steam]
        if os.path.exists(lib_file):
            for line in open(lib_file, encoding="utf-8", errors="ignore"):
                if '"path"' in line:
                    libs.append(line.split('"')[3].replace("\\\\", "\\"))
        for lib in libs:
            if os.path.exists(os.path.join(lib, GAME_SUBDIR, "Isaac.exe")):
                return os.path.join(lib, GAME_SUBDIR)
    return None


class MBI(ctypes.Structure):
    _fields_ = [("BaseAddress", ctypes.c_void_p), ("AllocationBase", ctypes.c_void_p), ("AllocationProtect", ctypes.c_uint32),
                ("PartitionId", ctypes.c_uint16), ("RegionSize", ctypes.c_size_t), ("State", ctypes.c_uint32),
                ("Protect", ctypes.c_uint32), ("Type", ctypes.c_uint32)]


def scan_process(handle):
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.VirtualQueryEx.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(MBI), ctypes.c_size_t]
    k32.ReadProcessMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t,
                                      ctypes.POINTER(ctypes.c_size_t)]
    best, addr, mbi = None, 0, MBI()
    while addr < 0xFFFF0000 and k32.VirtualQueryEx(handle, addr, ctypes.byref(mbi), ctypes.sizeof(mbi)):
        base, size = mbi.BaseAddress or 0, mbi.RegionSize
        if mbi.State == 0x1000 and not (mbi.Protect & 0x101):  # committed, not guard/no-access
            buf, n = ctypes.create_string_buffer(size), ctypes.c_size_t()
            if k32.ReadProcessMemory(handle, base, buf, size, ctypes.byref(n)):
                d = buf.raw[:n.value]
                i = d.find(b"FWS")
                while i != -1:
                    if i + 8 <= len(d):
                        length = struct.unpack("<I", d[i + 4:i + 8])[0]
                        if 1_000_000 < length <= len(d) - i and (best is None or length > len(best)) \
                                and swflib.tags_ok(d[i:i + length]):
                            best = d[i:i + length]
                    i = d.find(b"FWS", i + 1)
        addr = base + size
    return best


def dump_swf(game_dir, wait=30, log=print):
    """Copy the game folder to a temp folder, run the copy, read the decrypted SWF from its memory."""
    if not os.path.exists(os.path.join(game_dir, "Isaac.exe")):
        raise RuntimeError(f"Isaac.exe not found in {game_dir}")
    tmp = tempfile.mkdtemp(prefix="tboi_flash_mods_")
    try:
        for f in os.listdir(game_dir):
            if os.path.isfile(os.path.join(game_dir, f)):
                shutil.copy2(os.path.join(game_dir, f), tmp)
        log("Starting a temporary copy of the game for a few seconds (a game window will appear)...")
        # The copy is not affected by a "Run as administrator" compatibility flag on the original path, and the
        # handle returned to us as the creator keeps full access to read its memory.
        proc = subprocess.Popen([os.path.join(tmp, "Isaac.exe")], cwd=tmp)
        try:
            swf = None
            for _ in range(max(1, wait // 5)):
                time.sleep(5)
                if proc.poll() is not None:
                    raise RuntimeError("The game closed before its SWF could be read.")
                swf = scan_process(int(proc._handle))
                if swf:
                    break
        finally:
            proc.kill()
            proc.wait()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if not swf:
        raise RuntimeError("Could not find the game SWF in memory; try again.")
    return swf


def game_swf(game_dir, cache_dir, log=print, wait=30):
    """The game's SWF, from the cache if Isaac.exe hasn't changed since it was read."""
    st = os.stat(os.path.join(game_dir, "Isaac.exe"))
    key = f"{st.st_size}-{int(st.st_mtime)}"
    path = os.path.join(cache_dir, f"isaac_{key}.swf")
    if os.path.exists(path):
        d = open(path, "rb").read()
        if swflib.tags_ok(d):
            log("Using the game data read earlier.")
            return d
    d = dump_swf(game_dir, wait, log)
    os.makedirs(cache_dir, exist_ok=True)
    for f in os.listdir(cache_dir):
        if f.startswith("isaac_") and f.endswith(".swf"):
            os.remove(os.path.join(cache_dir, f))
    open(path, "wb").write(d)
    return d
