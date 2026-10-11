# TBoI Flash Mods

A mod installer for the original Flash game
([The Binding of Isaac](https://store.steampowered.com/app/113200/The_Binding_of_Isaac/), including Wrath of the
Lamb/Eternal DLC). Tick the mods you want, click **Install**, and play.

| Mod | What it does | Repository |
|---|---|---|
| External Item Descriptions | Descriptions for items, trinkets, cards and pills (F2) | [Flash-EID](https://github.com/tomandesMSH/Flash-EID) |
| Stats HUD | Your current stats on the left side of the screen (F3) | [FlashTBoI-StatsHUD](https://github.com/tomandesMSH/FlashTBoI-StatsHUD) |
| Debug Console | Repentance's debug console: `;` opens it (giveitem, spawn, goto, stage, debug, ...) | [FlashTBoI-DebugConsole](https://github.com/tomandesMSH/FlashTBoI-DebugConsole) |

## Usage

1. Download `TBoI_Flash_Mods.exe` from the [latest release](https://github.com/tomandesMSH/TBoI-FlashMods/releases/latest), put it where you want to keep the modded game, and start it.
   (Or with Python 3.8+: `python tboi_flash_mods.py`, no extra packages.)
2. Check the game folder (found automatically for Steam), tick the mods, click **Install / update selected mods**.
   The first time, a game window appears for a few seconds while the game is read.
3. Paste the launch option into Steam (it is copied to your clipboard): right-click The Binding of Isaac >
   Properties > General > **Launch Options**. Steam's Play button then starts the modded game. Or click **Play**.

To change the mods or update them, open the installer again, change the ticks and click Install again.
To play the normal game, clear the Steam launch option.

No game files are distributed. Everything is built from your own copy of the game, and the installation in Steam's
folder is never changed. The modded game uses the same save as the Steam version: don't run both at the same time.
Steam achievements are granted the next time you start the normal version.

## How it works

For each selected mod, the installer asks GitHub for the mod's latest release, downloads its release zip
(`EID_Flash_<version>.zip`, `Stats_HUD_<version>.zip`, `Debug_Console_<version>.zip`) and reads only the payload in it (`*_payload.json`: the mod's
compiled ActionScript, its graphics and the game versions it was tested with). The mod's own patcher script in the
zip is never run.

The game SWF is read from a temporary copy of the game (the same method as the mods' own patchers) and kept in
`cache/`, so changing the selection later doesn't start the game again. The payloads are inserted into frame 1 of
the SWF, in a fixed order (EID, Stats HUD, Debug Console), and the result is written as:

| File | |
|---|---|
| `TBoI Flash Mods/isaac_mods.swf` | The game with the selected mods |
| `TBoI Flash Mods/flashplayer_32_sa.exe` | Adobe's Flash Player 32 projector (downloaded from Adobe, checksum checked) |
| `TBoI Flash Mods/TBoI Flash Mods.exe` | Launcher, also the Steam launch option (`launcher/FlashModsLauncher.cs`) |
| `TBoI Flash Mods/mods.json` | Installed mods and versions, and the game folder |

### Adding a mod

Add it to `flashmods/mods.py` (GitHub repository, release zip prefix, the name of the atlas it exports). Its release
zip must contain a payload in the same format as EID Flash and Stats HUD (`doaction`, `bitmaps`, `game_sha256`).

## Development

```sh
python tboi_flash_mods.py --source <folder with release zips>   # use local release zips instead of GitHub
python tboi_flash_mods.py --install stats --no-projector        # install without the window
python tools/build_exe.py                                       # -> build/dist/TBoI_Flash_Mods.exe (pip install pyinstaller)
```

| Path | Purpose |
|---|---|
| `tboi_flash_mods.py` | Entry point (window, or `--install` without it). |
| `flashmods/gui.py` | Tkinter window. |
| `flashmods/mods.py` | The mods and their order. |
| `flashmods/releases.py` | Latest release lookup and download (GitHub API, or `--source`). |
| `flashmods/game.py` | Finds the game and reads its SWF from a temporary copy; caches it. |
| `flashmods/swf.py` | Inserts payloads into the SWF. |
| `flashmods/install.py` | The install steps: payloads, game SWF, projector, launcher, `mods.json`. |
| `launcher/FlashModsLauncher.cs` | `TBoI Flash Mods.exe`; compiled with Windows' .NET Framework `csc` (bundled in the exe build, compiled on the player's PC otherwise). |

## Credits

- External Item Descriptions by Wofsauge and contributors; Flash port and Stats HUD use EID's font and icons.
- The Binding of Isaac © Edmund McMillen & Florian Himsl. No game code or assets are included here.
