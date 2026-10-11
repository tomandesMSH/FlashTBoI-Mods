"""The mods this wrapper can install, in the order they are applied to the game.

Each mod publishes GitHub releases with a zip (made by its tools/package.py) that contains its patcher payload
(`*_payload.json`: compiled code, bitmaps, game hashes). Only that JSON is used; the mod's own patcher script in the
zip is never run.

Order matters: EID Flash first, then Stats HUD. Both carry the same projector compatibility code, and Stats HUD's copy
skips itself when EID Flash's is already there.
"""

MODS = [
    {
        "id": "eid",
        "name": "External Item Descriptions",
        "description": "Shows what items, trinkets, cards and pills do when you walk up to them. F2 shows/hides it.",
        "repo": "tomandesMSH/Flash-EID",
        "zip_prefix": "EID_Flash_",
        "export": "eid_atlas",
    },
    {
        "id": "stats",
        "name": "Stats HUD",
        "description": "Shows your current stats on the left side of the screen. F3 shows/hides it.",
        "repo": "tomandesMSH/FlashTBoI-StatsHUD",
        "zip_prefix": "Stats_HUD_",
        "export": "shud_atlas",
    },
]


def by_id(mod_id):
    return next(m for m in MODS if m["id"] == mod_id)
