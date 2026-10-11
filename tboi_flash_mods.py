"""TBoI Flash Mods: choose mods for The Binding of Isaac (Flash) and add them to your own copy of the game.

Usage: double-click TBoI_Flash_Mods.exe, or with Python 3.8+ (no extra packages):
    python tboi_flash_mods.py                         # window
    python tboi_flash_mods.py --install stats         # no window: install Stats HUD only
    python tboi_flash_mods.py --install eid,stats --game "D:/Games/The Binding Of Isaac"

Options:
    --out DIR       where the modded game goes (default: "TBoI Flash Mods" next to this program)
    --source DIR    take the mods' release zips from DIR instead of GitHub (development)
"""
import argparse
import os
import sys

from flashmods import game, install
from flashmods.mods import MODS

FROZEN = getattr(sys, "frozen", False)


def main():
    base = os.path.dirname(sys.executable if FROZEN else os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description="Add mods to The Binding of Isaac (Flash).")
    ap.add_argument("--out", default=os.path.join(base, "TBoI Flash Mods"))
    ap.add_argument("--source", help=argparse.SUPPRESS)
    ap.add_argument("--install", metavar="IDS", help="comma-separated mods to install without the window: "
                    + ", ".join(m["id"] for m in MODS))
    ap.add_argument("--game", help="game folder containing Isaac.exe (default: Steam install)")
    ap.add_argument("--no-projector", action="store_true", help="don't download the Flash Player projector")
    a = ap.parse_args()

    if a.install:
        if sys.stdout is None:  # the windowed exe has no console: write the output to <out>/install.log
            os.makedirs(a.out, exist_ok=True)
            sys.stdout = sys.stderr = open(os.path.join(a.out, "install.log"), "w", encoding="utf-8", buffering=1)
        game_dir = a.game or install.installed(a.out).get("game") or game.find_game()
        if not game_dir:
            sys.exit('Could not find The Binding of Isaac (Flash); use --game "<folder with Isaac.exe>".')
        option = install.install(a.install.split(","), game_dir, a.out, source=a.source, get_proj=not a.no_projector)
        print("\nSteam launch option:\n  " + option)
        return
    from flashmods import gui
    gui.main(a.out, a.source)


if __name__ == "__main__":
    main()
