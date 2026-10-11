"""Find and download the newest release of a mod from GitHub.

A release's zip is downloaded into the cache and only its `*_payload.json` is read. For development, a local folder
with release zips (e.g. the mods' build folders) can be used instead of GitHub (`--source DIR`).
"""
import glob
import io
import json
import os
import re
import urllib.error
import urllib.request
import zipfile

API = "https://api.github.com/repos/{repo}/releases/latest"
USER_AGENT = "TBoI-FlashMods"


class NoRelease(Exception):
    pass


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.github+json"})
    return urllib.request.urlopen(req, timeout=timeout).read()


def _version_key(name, prefix):
    v = name[len(prefix):-len(".zip")]
    return [int(x) for x in re.findall(r"\d+", v)]


def latest(mod, source=None):
    """{'version', 'zip_name', 'url' or 'path'} of the newest release of a mod."""
    if source:
        zips = [z for z in glob.glob(os.path.join(source, "**", mod["zip_prefix"] + "*.zip"), recursive=True)
                if not z.endswith("-debug.zip")]
        if not zips:
            raise NoRelease(f"no {mod['zip_prefix']}*.zip in {source}")
        path = max(zips, key=lambda z: _version_key(os.path.basename(z), mod["zip_prefix"]))
        name = os.path.basename(path)
        return {"version": name[len(mod["zip_prefix"]):-4], "zip_name": name, "path": path}
    try:
        rel = json.loads(_get(API.format(repo=mod["repo"]), timeout=20))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise NoRelease(f"{mod['repo']} has no release yet")
        raise
    for a in rel.get("assets", []):
        if a["name"].startswith(mod["zip_prefix"]) and a["name"].endswith(".zip"):
            return {"version": rel["tag_name"].lstrip("v"), "zip_name": a["name"], "url": a["browser_download_url"]}
    raise NoRelease(f"the latest release of {mod['repo']} ({rel.get('tag_name')}) has no {mod['zip_prefix']}*.zip")


def payload(mod, release, cache_dir):
    """Download the release zip (once) and return the payload it contains."""
    if "path" in release:
        data = open(release["path"], "rb").read()
    else:
        path = os.path.join(cache_dir, "downloads", release["zip_name"])
        if os.path.exists(path):
            data = open(path, "rb").read()
        else:
            data = _get(release["url"], timeout=300)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "wb").write(data)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.endswith("_payload.json")]
        if len(names) != 1:
            raise ValueError(f"{release['zip_name']} has no payload")
        p = json.loads(z.read(names[0]).decode("utf-8"))
    for key in ("doaction", "bitmaps", "game_sha256"):
        if key not in p:
            raise ValueError(f"{release['zip_name']}: payload has no {key}")
    if not any(b["name"] == mod["export"] for b in p["bitmaps"]):
        raise ValueError(f"{release['zip_name']} is not {mod['name']}")
    return p
