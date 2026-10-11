"""Build TBoI_Flash_Mods.exe (single file, windowed) with PyInstaller.

The launcher ("TBoI Flash Mods.exe") is compiled here and bundled, so players' PCs don't need to compile it.
Usage: python tools/build_exe.py [--out DIR]      (needs: pip install pyinstaller)
Output: build/dist/TBoI_Flash_Mods.exe
"""
import argparse
import os
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, ROOT)
sys.dont_write_bytecode = True
from flashmods import install  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "build"))
    a = ap.parse_args()
    work = os.path.join(a.out, "pyinstaller")
    os.makedirs(work, exist_ok=True)
    launcher = os.path.join(work, install.LAUNCHER)
    install.compile_launcher(launcher)
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onefile", "--windowed",
           "--name", "TBoI_Flash_Mods",
           "--add-data", launcher + os.pathsep + "launcher",
           "--distpath", os.path.join(a.out, "dist"), "--workpath", work, "--specpath", work,
           os.path.join(ROOT, "tboi_flash_mods.py")]
    if subprocess.run(cmd, cwd=ROOT).returncode != 0:
        sys.exit("PyInstaller failed")
    exe = os.path.join(a.out, "dist", "TBoI_Flash_Mods.exe")
    print("built", exe, os.path.getsize(exe), "bytes")


if __name__ == "__main__":
    main()
