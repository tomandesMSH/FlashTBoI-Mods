"""SWF helpers: insert a mod payload into frame 1 of the game SWF.

Same method as the EID Flash and Stats HUD patchers: each payload is a complete DoAction tag (the mod's compiled
ActionScript 2) plus bitmaps (DefineBitsLossless2 bodies without their character id). They are inserted right
before the first ShowFrame of the root timeline, after the game's own frame 1 script.
"""
import base64
import struct
import zlib

# tags whose body starts with a u16 character id
DEFINE_TAGS = {2, 6, 7, 10, 11, 13, 14, 20, 21, 22, 32, 33, 34, 35, 36, 37, 39, 46, 48, 60, 62, 75, 83, 84, 87, 90, 91}
TAG_SHOWFRAME, TAG_END, TAG_LOSSLESS2, TAG_EXPORT = 1, 0, 36, 56


def tag_header(code, length):
    if length < 0x3F:
        return struct.pack("<H", (code << 6) | length)
    return struct.pack("<HI", (code << 6) | 0x3F, length)


def first_tag_offset(d):
    nb = d[8] >> 3
    return 8 + (5 + 4 * nb + 7) // 8 + 4


def walk_tags(d, p, end):
    """Yields (code, tag_start, body_start, body_length) up to and including the End tag."""
    while p + 2 <= end:
        h = struct.unpack("<H", d[p:p + 2])[0]
        code, length, start = h >> 6, h & 0x3F, p
        p += 2
        if length == 0x3F:
            length = struct.unpack("<I", d[p:p + 4])[0]
            p += 4
        yield code, start, p, length
        p += length
        if code == TAG_END:
            return


def decompress(d):
    if d[:3] == b"CWS":
        return b"FWS" + d[3:8] + zlib.decompress(d[8:])
    if d[:3] != b"FWS":
        raise ValueError("not an SWF file")
    return d


def tags_ok(d):
    """True if d is an uncompressed SWF whose tag list walks exactly to its End tag."""
    if len(d) < 30 or d[:3] != b"FWS":
        return False
    end = None
    for code, start, body, length in walk_tags(d, first_tag_offset(d), len(d)):
        if code == TAG_END:
            end = body + length
    return end == len(d)


def exported_names(d):
    """Names of the ExportAssets entries (each mod exports its atlas, e.g. "eid_atlas", "shud_atlas")."""
    names = set()
    for code, start, body, length in walk_tags(d, first_tag_offset(d), len(d)):
        if code == TAG_EXPORT:
            count, p = struct.unpack("<H", d[body:body + 2])[0], body + 2
            for _ in range(count):
                end = d.index(b"\0", p + 2)
                names.add(d[p + 2:end].decode("utf-8", "replace"))
                p = end + 1
    return names


def apply_payload(swf, payload):
    """Insert the payload tags into frame 1 of the root timeline, right before its ShowFrame."""
    d = decompress(swf)
    max_id, show_frame = 0, None
    for code, start, body, length in walk_tags(d, first_tag_offset(d), len(d)):
        if code in DEFINE_TAGS:
            max_id = max(max_id, struct.unpack("<H", d[body:body + 2])[0])
        if show_frame is None and code == TAG_SHOWFRAME:
            show_frame = start
    if show_frame is None:
        raise ValueError("SWF has no frames")
    new = b""
    for i, bitmap in enumerate(payload["bitmaps"]):
        cid = max_id + 1 + i
        body = struct.pack("<H", cid) + base64.b64decode(bitmap["lossless2"])
        new += tag_header(TAG_LOSSLESS2, len(body)) + body
        export = struct.pack("<HH", 1, cid) + bitmap["name"].encode("utf-8") + b"\0"
        new += tag_header(TAG_EXPORT, len(export)) + export
    new += base64.b64decode(payload["doaction"])  # complete DoAction tag (header + actions) with the mod's code
    out = d[:show_frame] + new + d[show_frame:]
    return out[:4] + struct.pack("<I", len(out)) + out[8:]
