"""
yt-autopilot — local MCP server that lets Claude upload videos to a YouTube
channel and review their performance, using Google's own APIs (no vidIQ).

Run:   python server.py            (stdio, registered in Claude Desktop)
Auth:  python server.py --auth     (one-time browser sign-in with the channel's Google account)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))

SCOPES = [
    "https://www.googleapis.com/auth/youtube",            # manage videos, playlists, thumbnails
    "https://www.googleapis.com/auth/youtube.upload",     # upload
    "https://www.googleapis.com/auth/youtube.force-ssl",  # comments
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]

CATEGORIES = {
    "1": "Film & Animation", "2": "Autos & Vehicles", "10": "Music", "15": "Pets & Animals",
    "17": "Sports", "19": "Travel & Events", "20": "Gaming", "22": "People & Blogs",
    "23": "Comedy", "24": "Entertainment", "25": "News & Politics", "26": "Howto & Style",
    "27": "Education", "28": "Science & Technology", "29": "Nonprofits & Activism",
}

mcp = FastMCP("yt-autopilot")

# YouTube Data API quota: 10,000 units/day, resets at midnight Pacific time.
QUOTA_DAILY = 10_000
QUOTA_COST = {"upload": 1600, "update": 50, "thumbnail": 50, "playlist_insert": 50, "playlist_create": 50,
              "comment_insert": 50, "list": 1, "channels": 1, "comments_list": 1}


# --------------------------------------------------------------------------- helpers
def _p(rel: str) -> Path:
    p = Path(rel)
    return p if p.is_absolute() else ROOT / p


def _watch(sub: str) -> Path:
    return Path(os.path.expandvars(CONFIG["watch_root"])) / CONFIG[sub]


def _credentials(interactive: bool = False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    token_file = _p(CONFIG["token_file"])
    secret_file = _p(CONFIG["client_secret_file"])
    creds = None
    if token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_file.write_text(creds.to_json(), encoding="utf-8")
        return creds
    if not interactive:
        raise RuntimeError(
            "Not authorized yet. Double-click 'Sign in to YouTube' on the Desktop (or run server.py --auth) "
            "and sign in with the Google account that owns the target channel."
        )
    if not secret_file.exists():
        raise RuntimeError(f"Missing OAuth client file: {secret_file}. Download it from Google Cloud Console.")
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_secrets_file(str(secret_file), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
    token_file.parent.mkdir(parents=True, exist_ok=True)
    token_file.write_text(creds.to_json(), encoding="utf-8")
    return creds


def _yt():
    from googleapiclient.discovery import build
    return build("youtube", "v3", credentials=_credentials(), cache_discovery=False)


def _analytics():
    from googleapiclient.discovery import build
    return build("youtubeAnalytics", "v2", credentials=_credentials(), cache_discovery=False)


def _my_channel() -> dict:
    r = _yt().channels().list(part="snippet,statistics,contentDetails", mine=True).execute()
    items = r.get("items") or []
    if not items:
        raise RuntimeError("The signed-in Google account has no YouTube channel.")
    c = items[0]
    return {
        "channelId": c["id"],
        "title": c["snippet"]["title"],
        "handle": c["snippet"].get("customUrl"),
        "subscribers": c["statistics"].get("subscriberCount"),
        "views": c["statistics"].get("viewCount"),
        "videos": c["statistics"].get("videoCount"),
        "uploadsPlaylist": c["contentDetails"]["relatedPlaylists"]["uploads"],
    }


def _query(metrics: str, start: date, end: date, dimensions: Optional[str] = None,
           filters: Optional[str] = None, sort: Optional[str] = None, max_results: Optional[int] = None) -> dict:
    kwargs: dict[str, Any] = dict(ids="channel==MINE", startDate=start.isoformat(), endDate=end.isoformat(), metrics=metrics)
    if dimensions:
        kwargs["dimensions"] = dimensions
    if filters:
        kwargs["filters"] = filters
    if sort:
        kwargs["sort"] = sort
    if max_results:
        kwargs["maxResults"] = max_results
    r = _analytics().reports().query(**kwargs).execute()
    cols = [c["name"] for c in r.get("columnHeaders", [])]
    return {"columns": cols, "rows": [dict(zip(cols, row)) for row in r.get("rows", [])]}


def _period(days: int) -> tuple[date, date]:
    end = date.today() - timedelta(days=2)  # analytics lag ~2 days
    return end - timedelta(days=days - 1), end


def _log_upload(record: dict) -> None:
    f = _p(CONFIG["upload_log"])
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_uploads() -> list[dict]:
    f = _p(CONFIG["upload_log"])
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _find_duplicate(path: Path) -> Optional[dict]:
    """Return the earlier upload record if this exact file (by SHA-256) was uploaded before."""
    digest = _sha256(path)
    for rec in _read_uploads():
        if rec.get("sha256") == digest:
            return rec
    return None


def _validate_metadata(title: str, description: str, tags: list[str]) -> list[str]:
    """YouTube's hard rules. Returns a list of problems (empty = ok)."""
    problems = []
    if not title or not title.strip():
        problems.append("title is empty")
    if len(title) > 100:
        problems.append(f"title is {len(title)} characters, max 100")
    if "<" in title or ">" in title:
        problems.append("title contains < or >, which YouTube rejects")
    if len(description) > 5000:
        problems.append(f"description is {len(description)} characters, max 5000")
    if "<" in description or ">" in description:
        problems.append("description contains < or >, which YouTube rejects")
    bad = [t for t in tags if len(t) > 100]
    if bad:
        problems.append(f"tags longer than 100 characters: {bad}")
    # YouTube counts tags with spaces as quoted, plus separators
    total = sum(len(t) + (2 if " " in t else 0) for t in tags) + max(0, len(tags) - 1)
    if total > 500:
        problems.append(f"tags total {total} characters, max 500 (drop some tags)")
    problems += _shorts_rules(title, description)
    return problems


HASHTAG_RE = re.compile(r"#([\wऀ-ॿ]+)")
USELESS_TAGS = {"fyp", "foryou", "foryoupage", "tiktok", "reels", "instagram", "viralvideo", "viral", "trending"}
CTA_WORDS = ("subscribe", "follow", "like", "comment", "share", "save", "सब्सक्राइब", "फॉलो", "लाइक", "कमेंट", "शेयर")


def _hashtags(text: str) -> list[str]:
    return [h.lower() for h in HASHTAG_RE.findall(text or "")]


def _shorts_rules(title: str, description: str) -> list[str]:
    """Strict Shorts rules so every upload is discoverable: #shorts present, 3-5 unique hashtags, hashtags in the
    first 3 description lines, no useless cross-platform tags, description >=150 chars with a hook and a CTA."""
    p = []
    t_tags, d_tags = _hashtags(title), _hashtags(description)
    all_tags = t_tags + d_tags
    uniq = list(dict.fromkeys(all_tags))
    if "shorts" not in uniq:
        p.append("missing #shorts (put it in the title or in the first lines of the description)")
    nt, nd = len(set(t_tags)), len(set(d_tags))
    if nt < 3 or nt > 4:
        p.append(f"title has {nt} hashtags; use 3 to 4 (for example #shorts plus 2-3 topic tags)")
    if nd < 5 or nd > 10:
        p.append(f"description has {nd} hashtags; use 5 to 10")
    if len(all_tags) > 15:
        p.append("more than 15 hashtags in total: YouTube ignores all hashtags on the video")
    for field, tags_in in (("title", _hashtags(title)), ("description", _hashtags(description))):
        dupes = sorted({t for t in tags_in if tags_in.count(t) > 1})
        if dupes:
            p.append(f"hashtags repeated inside the {field}: {dupes}")
    bad = sorted(set(uniq) & USELESS_TAGS)
    if bad:
        p.append(f"drop cross-platform/spam hashtags that do nothing on YouTube: {['#' + b for b in bad]}")
    numeric = [t for t in uniq if t.isdigit()]
    if numeric:
        p.append(f"hashtags that are only numbers are ignored: {numeric}")
    desc = (description or "").strip()
    lines = [l.strip() for l in desc.splitlines() if l.strip()]
    if len(desc) < 150:
        p.append(f"description is {len(desc)} characters; write at least 150 (what the video is about, keywords, CTA, hashtags)")
    if not lines or len(lines[0]) < 20 or lines[0].startswith("#"):
        p.append("first description line should be a hook sentence (20+ characters, not a hashtag line)")
    if not any(_hashtags(l) for l in lines[:3]):
        p.append("put a hashtag line within the first 3 lines of the description (shown above the fold)")
    low = desc.lower()
    if not any(w in low for w in CTA_WORDS):
        p.append("no call to action in description (ask to subscribe / like / comment / share)")
    return p


# ---- style profile learned from best videos -----------------------------------
EMOJI_RE = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F900-\U0001F9FF]")
DEVANAGARI_RE = re.compile("[ऀ-ॿ]")


def _profile_file() -> Path:
    return _p("data/style_profile.json")


def _build_style_profile(top_n: int = 5) -> dict:
    yt = _yt()
    ch = _my_channel()
    ids, page = [], None
    while len(ids) < 200:
        r = yt.playlistItems().list(part="contentDetails", playlistId=ch["uploadsPlaylist"], maxResults=50, pageToken=page).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page:
            break
    vids = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,statistics,status", id=",".join(ids[i:i + 50])).execute()
        for v in r.get("items", []):
            if v["status"]["privacyStatus"] != "public":
                continue
            pub = datetime.fromisoformat(v["snippet"]["publishedAt"].replace("Z", "+00:00"))
            age_days = max(1.0, (datetime.now(timezone.utc) - pub).total_seconds() / 86400)
            views = int(v["statistics"].get("viewCount", 0))
            vids.append({"videoId": v["id"], "title": v["snippet"]["title"], "description": v["snippet"].get("description", ""),
                         "tags": v["snippet"].get("tags", []), "views": views, "viewsPerDay": round(views / age_days, 2),
                         "publishedAt": v["snippet"]["publishedAt"]})
    vids.sort(key=lambda x: x["viewsPerDay"], reverse=True)
    best = vids[:top_n]
    if not best:
        raise RuntimeError("No public videos to learn from yet.")

    def stats(group: list[dict]) -> dict:
        tag_counts: dict[str, int] = {}
        for v in group:
            for t in dict.fromkeys(_hashtags(v["title"]) + _hashtags(v["description"])):
                tag_counts[t] = tag_counts.get(t, 0) + 1
        texts = [v["title"] + " " + v["description"] for v in group]
        letters = sum(len(re.findall(r"[A-Za-zऀ-ॿ]", t)) for t in texts) or 1
        dev = sum(len(DEVANAGARI_RE.findall(t)) for t in texts)
        ctas = [l.strip() for v in group for l in v["description"].splitlines() if any(w in l.lower() for w in CTA_WORDS)]
        return {
            "count": len(group),
            "avgTitleLength": round(sum(len(v["title"]) for v in group) / len(group)),
            "avgDescriptionLength": round(sum(len(v["description"]) for v in group) / len(group)),
            "avgHashtagsPerVideo": round(sum(len(set(_hashtags(v["title"]) + _hashtags(v["description"]))) for v in group) / len(group), 1),
            "emojiInTitleRate": round(sum(1 for v in group if EMOJI_RE.search(v["title"])) / len(group), 2),
            "devanagariShare": round(dev / letters, 2),
            "topHashtags": sorted(tag_counts.items(), key=lambda kv: -kv[1])[:12],
            "ctaLinesSeen": list(dict.fromkeys(ctas))[:5],
        }

    profile = {
        "builtAt": datetime.now(timezone.utc).isoformat(), "channel": ch["title"], "handle": ch["handle"],
        "basedOnTopVideos": [{k: v[k] for k in ("videoId", "title", "viewsPerDay", "views")} for v in best],
        "bestVideosStyle": stats(best), "allVideosStyle": stats(vids),
        "exampleTitles": [v["title"] for v in best],
        "exampleDescriptions": [v["description"][:400] for v in best if v["description"]][:3],
        "guidance": [
            "Match the language mix of the best videos (devanagariShare: 0 = Latin/Hinglish, 1 = full Hindi script).",
            "Title: #shorts plus 2-3 topic tags (3-4 total). Description: 5-10 hashtags, reusing topHashtags that fit plus topic-specific ones. Max 15 overall.",
            "Keep the title near avgTitleLength; use an emoji in the title if emojiInTitleRate is high.",
            "First description line = hook sentence; then 2-3 lines about the video with keywords; then CTA; then hashtags.",
        ],
    }
    _profile_file().parent.mkdir(parents=True, exist_ok=True)
    _profile_file().write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")
    return profile


# ---- quota tracking (per Pacific-time day) -----------------------------------
def _quota_day() -> str:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/Los_Angeles")).date().isoformat()
    except Exception:  # noqa: BLE001
        return (datetime.now(timezone.utc) - timedelta(hours=8)).date().isoformat()


def _quota_file() -> Path:
    return _p("data/quota.json")


def _quota_used() -> int:
    f = _quota_file()
    if not f.exists():
        return 0
    try:
        d = json.loads(f.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    return int(d.get("used", 0)) if d.get("day") == _quota_day() else 0


def _quota_add(kind: str, n: int = 1) -> int:
    used = _quota_used() + QUOTA_COST.get(kind, 1) * n
    _quota_file().parent.mkdir(parents=True, exist_ok=True)
    _quota_file().write_text(json.dumps({"day": _quota_day(), "used": used}), encoding="utf-8")
    return used


def _quota_summary() -> dict:
    used = _quota_used()
    left = max(0, QUOTA_DAILY - used)
    return {"day_pacific": _quota_day(), "used": used, "remaining": left, "uploadsLeftToday": left // QUOTA_COST["upload"],
            "warning": "Fewer than 2 uploads left today." if left < 2 * QUOTA_COST["upload"] else None,
            "note": "Estimated from calls made through this connector only; YouTube Studio or other apps are not counted."}


# ---- daily stats snapshots (SQLite) -------------------------------------------
def _db() -> sqlite3.Connection:
    f = _p("data/stats.db")
    f.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(f))
    con.execute("""CREATE TABLE IF NOT EXISTS video_snapshots (
        day TEXT, videoId TEXT, title TEXT, publishedAt TEXT, views INTEGER, likes INTEGER, comments INTEGER,
        PRIMARY KEY (day, videoId))""")
    con.execute("""CREATE TABLE IF NOT EXISTS channel_snapshots (
        day TEXT PRIMARY KEY, subscribers INTEGER, views INTEGER, videos INTEGER)""")
    return con


def _take_snapshot() -> dict:
    today = date.today().isoformat()
    ch = _my_channel()
    vids = list_my_videos(200)["videos"]
    con = _db()
    with con:
        con.execute("INSERT OR REPLACE INTO channel_snapshots VALUES (?,?,?,?)",
                    (today, int(ch["subscribers"] or 0), int(ch["views"] or 0), int(ch["videos"] or 0)))
        for v in vids:
            con.execute("INSERT OR REPLACE INTO video_snapshots VALUES (?,?,?,?,?,?,?)",
                        (today, v["videoId"], v["title"], v["publishedAt"], int(v["views"] or 0),
                         int(v["likes"] or 0), int(v["comments"] or 0)))
    con.close()
    return {"day": today, "channel": ch["title"], "videosRecorded": len(vids)}


# ---- automatic new-video checks -----------------------------------------------
CHECK_DAYS = (1, 3)


def _alerts_file() -> Path:
    return _p("data/alerts.jsonl")


def _run_checks() -> list[dict]:
    """For each upload made through the connector, 1 and 3 days after upload, compare it to the previous
    10 uploads and record a verdict. Each (video, day) check runs once."""
    done = set()
    if _alerts_file().exists():
        for line in _alerts_file().read_text(encoding="utf-8").splitlines():
            try:
                a = json.loads(line)
                done.add((a["videoId"], a["checkDay"]))
            except Exception:  # noqa: BLE001
                pass
    now = datetime.now(timezone.utc)
    new_alerts = []
    for rec in _read_uploads():
        vid = rec.get("videoId")
        if not vid or not rec.get("at"):
            continue
        age_days = (now - datetime.fromisoformat(rec["at"])).total_seconds() / 86400
        for d in CHECK_DAYS:
            if (vid, d) in done or age_days < d + 1.0:  # +1 because analytics lags ~1-2 days
                continue
            try:
                cmp = compare_new_video(vid, window_days=d, baseline_videos=10)
            except Exception as e:  # noqa: BLE001
                cmp = {"error": str(e)}
            r = (cmp.get("ratioVsBaseline") or {}).get("views")
            verdict = ("no baseline yet" if r is None else "better than usual" if r >= 1.3
                       else "worse than usual" if r <= 0.7 else "about average")
            alert = {"at": now.isoformat(), "videoId": vid, "title": rec.get("title"), "checkDay": d,
                     "viewsRatioVsBaseline": r, "verdict": verdict,
                     "target": cmp.get("target"), "baselineAverage": cmp.get("baselineAverage"), "error": cmp.get("error")}
            with _alerts_file().open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(alert, ensure_ascii=False) + "\n")
            new_alerts.append(alert)
            done.add((vid, d))
    return new_alerts


def _sidecar(video: Path) -> tuple[Optional[Path], dict]:
    for cand in (video.with_suffix(".json"), video.with_name(video.name + ".json")):
        if cand.exists():
            try:
                return cand, json.loads(cand.read_text(encoding="utf-8"))
            except Exception as e:  # noqa: BLE001
                return cand, {"_error": f"invalid JSON: {e}"}
    return None, {}


def _move(src: Path, dest_dir: str) -> str:
    dest_dir_p = _watch(dest_dir)
    dest_dir_p.mkdir(parents=True, exist_ok=True)
    target = dest_dir_p / src.name
    if target.exists():
        target = dest_dir_p / f"{src.stem}_{datetime.now():%Y%m%d%H%M%S}{src.suffix}"
    shutil.move(str(src), str(target))
    side, _ = _sidecar(src)
    if side and side.exists():
        shutil.move(str(side), str(dest_dir_p / side.name))
    return str(target)


# --------------------------------------------------------------------------- auth / channel
@mcp.tool()
def youtube_auth_status() -> dict:
    """Check whether the connector is authorized and which channel it will act on."""
    try:
        ch = _my_channel()
        return {"authorized": True, "channel": ch}
    except Exception as e:  # noqa: BLE001
        return {"authorized": False, "error": str(e),
                "fix": f"Double-click 'Sign in to YouTube' on the Desktop, or run: {ROOT}\\.venv\\Scripts\\python.exe {ROOT}\\server.py --auth"}


@mcp.tool()
def youtube_categories() -> dict:
    """List YouTube video category IDs usable in upload_video / update_video."""
    return CATEGORIES


# --------------------------------------------------------------------------- watch folder
@mcp.tool()
def list_incoming_videos() -> dict:
    """List videos waiting in the watch folder (incoming/) with any sidecar metadata (<name>.json).
    Sidecar keys: title, description, tags[], categoryId, privacy, publishAt, madeForKids, language, thumbnail, playlistId."""
    inc = _watch("incoming_dir")
    inc.mkdir(parents=True, exist_ok=True)
    exts = set(CONFIG["video_extensions"])
    out = []
    for f in sorted(inc.iterdir()):
        if f.suffix.lower() not in exts:
            continue
        side, meta = _sidecar(f)
        missing = [k for k in ("title",) if not meta.get(k)]
        out.append({
            "file": str(f), "sizeMB": round(f.stat().st_size / 1e6, 1),
            "metadataFile": str(side) if side else None, "metadata": meta,
            "readyToUpload": not missing and "_error" not in meta, "missing": missing,
        })
    return {"incoming": str(inc), "count": len(out), "videos": out}


@mcp.tool()
def find_video_files(query: str = "", max_results: int = 20, extra_folders: Optional[list[str]] = None) -> dict:
    """Find video files anywhere on this PC's usual folders (Downloads, Desktop, Videos, Documents, OneDrive copies,
    the watch folder) so a file the user attached or downloaded can be uploaded without moving it. `query` matches
    words in the filename (case-insensitive, all words must match); empty query lists the newest videos.
    Use the returned path directly with upload_video."""
    home = Path.home()
    folders = [home / "Downloads", home / "Desktop", home / "Videos", home / "Documents",
               home / "OneDrive" / "Desktop", home / "OneDrive" / "Documents", Path(os.path.expandvars(CONFIG["watch_root"])),
               home / "Claude"]  # Claude Desktop Cowork drops attached files here
    for f in extra_folders or []:
        folders.append(Path(f))
    exts = set(CONFIG["video_extensions"])
    words = [w for w in query.lower().split() if w]
    found: list[tuple[float, Path]] = []
    seen = set()
    for folder in folders:
        if not folder.exists():
            continue
        try:
            for root, dirs, files in os.walk(folder):
                dirs[:] = [d for d in dirs if not d.startswith(".") and d.lower() not in ("node_modules", "$recycle.bin")]
                depth = len(Path(root).relative_to(folder).parts)
                if depth >= 3:
                    dirs[:] = []
                for name in files:
                    p = Path(root) / name
                    if p.suffix.lower() not in exts or p in seen:
                        continue
                    low = name.lower()
                    if words and not all(w in low for w in words):
                        continue
                    seen.add(p)
                    try:
                        found.append((p.stat().st_mtime, p))
                    except OSError:
                        pass
        except PermissionError:
            continue
    found.sort(key=lambda t: t[0], reverse=True)
    return {"query": query, "searched": [str(f) for f in folders if f.exists()],
            "results": [{"file": str(p), "sizeMB": round(p.stat().st_size / 1e6, 1),
                         "modified": datetime.fromtimestamp(m).isoformat(timespec="minutes")} for m, p in found[:max_results]]}


@mcp.tool()
def write_video_metadata(file: str, title: str, description: str = "", tags: Optional[list[str]] = None,
                         categoryId: Optional[str] = None, privacy: Optional[str] = None,
                         publishAt: Optional[str] = None, madeForKids: Optional[bool] = None,
                         language: Optional[str] = None, thumbnail: Optional[str] = None,
                         playlistId: Optional[str] = None) -> dict:
    """Save/overwrite the sidecar metadata JSON next to a video in the watch folder (after the user approved the draft)."""
    v = Path(file)
    if not v.exists():
        raise FileNotFoundError(file)
    meta = {k: val for k, val in dict(title=title, description=description, tags=tags or [], categoryId=categoryId,
                                       privacy=privacy, publishAt=publishAt, madeForKids=madeForKids, language=language,
                                       thumbnail=thumbnail, playlistId=playlistId).items() if val is not None}
    side = v.with_suffix(".json")
    side.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"metadataFile": str(side), "metadata": meta}


# --------------------------------------------------------------------------- upload
@mcp.tool()
def upload_video(file: str, title: Optional[str] = None, description: Optional[str] = None,
                 tags: Optional[list[str]] = None, categoryId: Optional[str] = None,
                 privacy: Optional[str] = None, publishAt: Optional[str] = None,
                 madeForKids: Optional[bool] = None, language: Optional[str] = None,
                 thumbnail: Optional[str] = None, playlistId: Optional[str] = None,
                 move_when_done: bool = True, force: bool = False, dry_run: bool = False) -> dict:
    """Upload a video file to the authorized channel. `file` may be ANY absolute path on this PC (use
    find_video_files to locate a file the user attached or downloaded); files from the watch folder's incoming/
    are moved to uploaded/ afterwards, others stay where they are. Arguments override the sidecar JSON. Privacy
    defaults to PRIVATE: the user reviews it, then says 'publish' and you call publish_video. publishAt (RFC3339
    UTC) schedules it instead. Read get_style_profile before drafting and run validate_metadata on the draft; the
    upload refuses drafts that fail the Shorts rules, duplicates (same file, unless force=True), and runs out of
    quota. dry_run=True validates everything without uploading."""
    from googleapiclient.http import MediaFileUpload

    v = Path(file)
    if not v.exists():
        raise FileNotFoundError(file)
    _, meta = _sidecar(v)

    def pick(arg, key, default=None):
        return arg if arg is not None else meta.get(key, default)

    title = pick(title, "title")
    if not title:
        raise ValueError("A title is required (argument or sidecar JSON).")
    description = pick(description, "description", "") or ""
    tags = pick(tags, "tags", []) or []
    categoryId = str(pick(categoryId, "categoryId", "22"))
    privacy = pick(privacy, "privacy", CONFIG["default_privacy"])
    publishAt = pick(publishAt, "publishAt")
    madeForKids = bool(pick(madeForKids, "madeForKids", CONFIG["default_made_for_kids"]))
    language = pick(language, "language")
    thumbnail = pick(thumbnail, "thumbnail")
    playlistId = pick(playlistId, "playlistId")
    if publishAt:
        privacy = "private"

    # --- guards: metadata rules, duplicate file, quota
    problems = _validate_metadata(title, description, tags)
    if problems:
        return {"ok": False, "error": "metadata invalid", "problems": problems}
    dup = _find_duplicate(v)
    if dup and not force:
        return {"ok": False, "error": "duplicate", "message": "This exact file was already uploaded. Pass force=True to upload anyway.",
                "previousUpload": {k: dup.get(k) for k in ("at", "videoId", "url", "title")}}
    quota = _quota_summary()
    if quota["remaining"] < QUOTA_COST["upload"]:
        return {"ok": False, "error": "quota", "message": "Not enough YouTube API quota left today for an upload.", "quota": quota}
    if dry_run:
        return {"ok": True, "dryRun": True, "wouldUpload": {"file": str(v), "title": title, "description": description,
                "tags": tags, "categoryId": categoryId, "privacy": privacy, "publishAt": publishAt,
                "madeForKids": madeForKids, "language": language, "thumbnail": thumbnail, "playlistId": playlistId},
                "duplicate": bool(dup), "quota": quota}

    snippet: dict[str, Any] = {"title": title, "description": description, "tags": tags, "categoryId": categoryId}
    if language:
        snippet["defaultLanguage"] = language
        snippet["defaultAudioLanguage"] = language
    status: dict[str, Any] = {"privacyStatus": privacy, "selfDeclaredMadeForKids": madeForKids}
    if publishAt:
        status["publishAt"] = publishAt

    yt = _yt()
    media = MediaFileUpload(str(v), chunksize=8 * 1024 * 1024, resumable=True)
    req = yt.videos().insert(part="snippet,status", body={"snippet": snippet, "status": status}, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    _quota_add("upload")
    video_id = resp["id"]
    result: dict[str, Any] = {"ok": True, "videoId": video_id, "url": f"https://youtu.be/{video_id}", "title": title,
                              "privacy": privacy, "publishAt": publishAt, "sha256": _sha256(v)}

    if thumbnail:
        t = Path(thumbnail) if Path(thumbnail).is_absolute() else v.parent / thumbnail
        if t.exists():
            try:
                yt.thumbnails().set(videoId=video_id, media_body=str(t)).execute()
                _quota_add("thumbnail")
                result["thumbnail"] = "set"
            except Exception as e:  # noqa: BLE001
                result["thumbnail"] = f"failed: {e}"
        else:
            result["thumbnail"] = f"file not found: {t}"
    if playlistId:
        try:
            yt.playlistItems().insert(part="snippet", body={"snippet": {"playlistId": playlistId,
                                      "resourceId": {"kind": "youtube#video", "videoId": video_id}}}).execute()
            _quota_add("playlist_insert")
            result["playlist"] = playlistId
        except Exception as e:  # noqa: BLE001
            result["playlist"] = f"failed: {e}"

    if move_when_done and v.parent == _watch("incoming_dir"):
        result["movedTo"] = _move(v, "uploaded_dir")
    _log_upload({"at": datetime.now(timezone.utc).isoformat(), **result, "file": str(v)})
    result["quota"] = _quota_summary()
    if privacy == "private" and not publishAt:
        result["next"] = "Uploaded as PRIVATE. Review it in YouTube Studio, then tell Claude 'publish it' (publish_video)."
    return result


@mcp.tool()
def validate_metadata(title: str, description: str = "", tags: Optional[list[str]] = None) -> dict:
    """Check a draft against YouTube limits AND the channel's strict Shorts rules (#shorts present, 3-4 hashtags in
    the title, 5-10 hashtags in the description, max 15 in total, hashtag line in first 3 description lines, no
    cross-platform spam tags, description >=150 chars with hook + CTA).
    Call this on every draft before showing it to the user; upload_video refuses drafts that fail."""
    problems = _validate_metadata(title, description, tags or [])
    uniq = list(dict.fromkeys(_hashtags(title) + _hashtags(description)))
    return {"ok": not problems, "problems": problems, "titleLength": len(title), "descriptionLength": len(description),
            "hashtags": ["#" + h for h in uniq]}


@mcp.tool()
def get_style_profile(rebuild: bool = False) -> dict:
    """The channel's style profile learned from its best-performing videos (language mix, hashtags, title length,
    emoji use, CTA lines, example titles/descriptions). Read it BEFORE drafting any title/description. Built on
    first call and by the weekly task; rebuild=True refreshes now."""
    if rebuild or not _profile_file().exists():
        return _build_style_profile()
    return json.loads(_profile_file().read_text(encoding="utf-8"))


@mcp.tool()
def best_time_to_post() -> dict:
    """Suggest the best weekday and hour (IST) to publish, based on how this channel's own videos performed in
    their first 7 days by publish slot, plus where viewers are. Data is thin on a small channel, so a sensible
    default for an Indian audience is returned when fewer than 8 videos exist."""
    from zoneinfo import ZoneInfo
    ist = ZoneInfo("Asia/Kolkata")
    vids = list_my_videos(60)["videos"]
    rows = []
    for v in vids:
        if v["privacy"] != "public":
            continue
        pub = datetime.fromisoformat(v["publishedAt"].replace("Z", "+00:00")).astimezone(ist)
        d0 = pub.date()
        d1 = min(d0 + timedelta(days=6), date.today() - timedelta(days=2))
        if d1 < d0:
            continue
        try:
            q = _query("views", d0, d1, filters=f"video=={v['videoId']}")
            views7 = q["rows"][0]["views"] if q["rows"] else 0
        except Exception:  # noqa: BLE001
            views7 = int(v["views"] or 0)
        rows.append({"videoId": v["videoId"], "title": v["title"], "weekday": pub.strftime("%A"), "hourIST": pub.hour,
                     "slot": f"{(pub.hour // 3) * 3:02d}-{(pub.hour // 3) * 3 + 3:02d}", "views7d": views7})

    def avg_by(key: str) -> list[dict]:
        groups: dict[str, list[int]] = {}
        for r in rows:
            groups.setdefault(r[key], []).append(r["views7d"])
        return sorted([{key: k, "videos": len(v), "avgViews7d": round(sum(v) / len(v), 1)} for k, v in groups.items()],
                      key=lambda x: -x["avgViews7d"])

    by_slot, by_day = avg_by("slot"), avg_by("weekday")
    start, end = _period(28)
    try:
        countries = _query("views", start, end, dimensions="country", sort="-views", max_results=5)["rows"]
    except Exception:  # noqa: BLE001
        countries = []
    thin = len(rows) < 8
    if thin or not by_slot:
        rec = {"weekday": "Friday / Saturday / Sunday", "hourIST": "18:00-21:00",
               "why": "Default for Indian Shorts audiences (evening commute and after-dinner scrolling); not enough own data yet."}
    else:
        rec = {"weekday": by_day[0]["weekday"], "hourIST": by_slot[0]["slot"],
               "why": f"Best average first-7-day views in your own uploads ({by_slot[0]['videos']} videos in that slot)."}
    return {"recommendation": rec, "dataPoints": len(rows), "thinData": thin, "bySlotIST": by_slot, "byWeekday": by_day,
            "topCountries28d": countries, "perVideo": rows,
            "howToUse": "Use upload_video(publishAt=<RFC3339 UTC>) to schedule; IST = UTC+5:30 (18:00 IST = 12:30Z)."}


@mcp.tool()
def list_unpublished() -> dict:
    """Private videos on the channel (uploaded but not yet published). Say 'publish <id>' to make one public."""
    vids = [v for v in list_my_videos(100)["videos"] if v["privacy"] in ("private", "unlisted")]
    return {"count": len(vids), "videos": vids}


@mcp.tool()
def publish_video(videoId: str, publishAt: Optional[str] = None) -> dict:
    """Make a private video public now, or schedule it (publishAt RFC3339 UTC, e.g. 2026-10-20T12:30:00Z).
    Only call after the user explicitly says to publish."""
    yt = _yt()
    cur = yt.videos().list(part="status", id=videoId).execute().get("items", [])
    if not cur:
        raise ValueError(f"Video not found: {videoId}")
    st = cur[0]["status"]
    status = {"privacyStatus": "private" if publishAt else "public", "selfDeclaredMadeForKids": st.get("selfDeclaredMadeForKids", False)}
    if publishAt:
        status["publishAt"] = publishAt
    r = yt.videos().update(part="status", body={"id": videoId, "status": status}).execute()
    _quota_add("update")
    return {"videoId": videoId, "url": f"https://youtu.be/{videoId}", "privacy": r["status"]["privacyStatus"],
            "publishAt": r["status"].get("publishAt")}


def _weekly_report_md() -> str:
    ch = _my_channel()
    this_s, this_e = _period(7)
    prev_s, prev_e = this_s - timedelta(days=7), this_s - timedelta(days=1)
    m = "views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments,shares"
    cur = (_query(m, this_s, this_e)["rows"] or [{}])[0]
    prev = (_query(m, prev_s, prev_e)["rows"] or [{}])[0]

    def delta(k: str) -> str:
        a, b = float(cur.get(k, 0) or 0), float(prev.get(k, 0) or 0)
        if b == 0:
            return f"{a:g} (prev 0)"
        return f"{a:g} ({'+' if a >= b else ''}{(a - b) / b * 100:.0f}% vs prev week)"

    top = _query("views,estimatedMinutesWatched,averageViewDuration", this_s, this_e, dimensions="video", sort="-views", max_results=5)["rows"]
    titles = {}
    if top:
        r = _yt().videos().list(part="snippet", id=",".join(t["video"] for t in top)).execute()
        titles = {v["id"]: v["snippet"]["title"] for v in r.get("items", [])}
    traffic = _query("views", this_s, this_e, dimensions="insightTrafficSourceType", sort="-views")["rows"]
    try:
        comments = list_comments(max_results=50)["count"]
    except Exception:  # noqa: BLE001
        comments = "n/a"
    alerts = [a for a in performance_alerts(50)["alerts"]
              if datetime.fromisoformat(a["at"]) >= datetime.now(timezone.utc) - timedelta(days=7)]
    unpub = list_unpublished()["videos"]
    uploads = [u for u in _read_uploads() if datetime.fromisoformat(u["at"]) >= datetime.now(timezone.utc) - timedelta(days=7)]

    L = [f"# Weekly report: {ch['title']} ({ch['handle']})", f"Period {this_s} to {this_e}. Subscribers {ch['subscribers']}, total views {ch['views']}, videos {ch['videos']}.", "",
         "## This week vs last week"]
    for k, label in (("views", "Views"), ("estimatedMinutesWatched", "Watch time (min)"), ("averageViewDuration", "Avg view duration (s)"),
                     ("subscribersGained", "Subs gained"), ("subscribersLost", "Subs lost"), ("likes", "Likes"), ("comments", "Comments"), ("shares", "Shares")):
        L.append(f"- {label}: {delta(k)}")
    L += ["", "## Top videos this week"]
    L += [f"- {titles.get(t['video'], t['video'])}: {t['views']} views, {t['estimatedMinutesWatched']} min, avg {t['averageViewDuration']}s" for t in top] or ["- none"]
    L += ["", "## Traffic sources"] + ([f"- {t['insightTrafficSourceType']}: {t['views']} views" for t in traffic] or ["- none"])
    L += ["", f"## Uploads this week: {len(uploads)}"] + [f"- {u.get('title')} ({u.get('url')})" for u in uploads]
    L += ["", "## New-video verdicts (last 7 days)"] + ([f"- {a.get('title')}: day {a['checkDay']} → {a['verdict']} (ratio {a.get('viewsRatioVsBaseline')})" for a in alerts] or ["- none yet"])
    L += ["", f"## Waiting to publish: {len(unpub)}"] + [f"- {v['title']} ({v['videoId']})" for v in unpub]
    L += ["", f"## Unanswered comments: {comments}", "", f"## API quota today: {_quota_summary()['uploadsLeftToday']} uploads left"]
    return "\n".join(L)


@mcp.tool()
def weekly_report() -> dict:
    """Assemble this week's Markdown report: week-over-week numbers, top videos, traffic sources, uploads,
    new-video verdicts, videos waiting to publish, unanswered comments, quota. Also saved under data/reports/."""
    md = _weekly_report_md()
    out = _p(f"data/reports/{date.today().isoformat()}.md")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    return {"savedTo": str(out), "markdown": md}


@mcp.tool()
def quota_status() -> dict:
    """How much of today's YouTube API quota this connector has used, and how many uploads are still possible."""
    return _quota_summary()


@mcp.tool()
def set_thumbnail(videoId: str, image_path: str) -> dict:
    """Set a custom thumbnail (.jpg/.png, <2MB) on a video. The channel must be verified (phone) on YouTube."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(image_path)
    r = _yt().thumbnails().set(videoId=videoId, media_body=str(p)).execute()
    _quota_add("thumbnail")
    return {"videoId": videoId, "thumbnails": r.get("items", [{}])[0]}


# --------------------------------------------------------------------------- videos & metadata
@mcp.tool()
def list_my_videos(max_results: int = 25) -> dict:
    """List the channel's most recent uploads with id, title, publish date, privacy and basic stats."""
    ch = _my_channel()
    yt = _yt()
    ids, page = [], None
    while len(ids) < max_results:
        r = yt.playlistItems().list(part="contentDetails", playlistId=ch["uploadsPlaylist"],
                                    maxResults=min(50, max_results - len(ids)), pageToken=page).execute()
        ids += [i["contentDetails"]["videoId"] for i in r.get("items", [])]
        page = r.get("nextPageToken")
        if not page:
            break
    out = []
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="snippet,status,statistics,contentDetails", id=",".join(ids[i:i + 50])).execute()
        for v in r.get("items", []):
            out.append({"videoId": v["id"], "title": v["snippet"]["title"], "publishedAt": v["snippet"]["publishedAt"],
                        "privacy": v["status"]["privacyStatus"], "duration": v["contentDetails"]["duration"],
                        "views": v["statistics"].get("viewCount"), "likes": v["statistics"].get("likeCount"),
                        "comments": v["statistics"].get("commentCount")})
    return {"channel": ch["title"], "videos": out}


@mcp.tool()
def update_video(videoId: str, title: Optional[str] = None, description: Optional[str] = None,
                 tags: Optional[list[str]] = None, categoryId: Optional[str] = None,
                 privacy: Optional[str] = None, language: Optional[str] = None) -> dict:
    """Update title/description/tags/category/privacy/language of an existing video. Only given fields change."""
    yt = _yt()
    cur = yt.videos().list(part="snippet,status", id=videoId).execute().get("items", [])
    if not cur:
        raise ValueError(f"Video not found: {videoId}")
    sn, st = cur[0]["snippet"], cur[0]["status"]
    body = {"id": videoId, "snippet": {"title": title or sn["title"], "description": description if description is not None else sn.get("description", ""),
                                       "tags": tags if tags is not None else sn.get("tags", []), "categoryId": categoryId or sn["categoryId"]}}
    if language or sn.get("defaultLanguage"):
        body["snippet"]["defaultLanguage"] = language or sn.get("defaultLanguage")
    parts = "snippet"
    if privacy:
        body["status"] = {"privacyStatus": privacy, "selfDeclaredMadeForKids": st.get("selfDeclaredMadeForKids", False)}
        parts += ",status"
    r = yt.videos().update(part=parts, body=body).execute()
    _quota_add("update")
    return {"videoId": videoId, "title": r["snippet"]["title"], "privacy": r.get("status", st).get("privacyStatus")}


# --------------------------------------------------------------------------- playlists
@mcp.tool()
def list_playlists() -> dict:
    """List the channel's playlists."""
    r = _yt().playlists().list(part="snippet,contentDetails", mine=True, maxResults=50).execute()
    return {"playlists": [{"playlistId": p["id"], "title": p["snippet"]["title"], "videos": p["contentDetails"]["itemCount"]}
                          for p in r.get("items", [])]}


@mcp.tool()
def create_playlist(title: str, description: str = "", privacy: str = "public") -> dict:
    """Create a playlist on the channel."""
    r = _yt().playlists().insert(part="snippet,status", body={"snippet": {"title": title, "description": description},
                                                             "status": {"privacyStatus": privacy}}).execute()
    _quota_add("playlist_create")
    return {"playlistId": r["id"], "title": title}


@mcp.tool()
def add_to_playlist(playlistId: str, videoId: str) -> dict:
    """Add a video to a playlist."""
    r = _yt().playlistItems().insert(part="snippet", body={"snippet": {"playlistId": playlistId,
                                     "resourceId": {"kind": "youtube#video", "videoId": videoId}}}).execute()
    _quota_add("playlist_insert")
    return {"playlistItemId": r["id"], "playlistId": playlistId, "videoId": videoId}


# --------------------------------------------------------------------------- performance reports
@mcp.tool()
def video_stats(videoIds: list[str], days: int = 28) -> dict:
    """Per-video performance for the last N days (analytics) plus lifetime counters: views, watch time (min),
    average view duration (s), average % viewed, likes, comments, shares, subscribers gained. Note: impressions and
    CTR are not exposed by the YouTube Analytics API; they are only visible in YouTube Studio."""
    start, end = _period(days)
    yt = _yt()
    lifetime = {}
    for i in range(0, len(videoIds), 50):
        r = yt.videos().list(part="snippet,statistics", id=",".join(videoIds[i:i + 50])).execute()
        for v in r.get("items", []):
            lifetime[v["id"]] = {"title": v["snippet"]["title"], "publishedAt": v["snippet"]["publishedAt"], **v["statistics"]}
    q = _query("views,estimatedMinutesWatched,averageViewDuration,averageViewPercentage,likes,comments,shares,subscribersGained",
               start, end, dimensions="video", filters="video==" + ",".join(videoIds), sort="-views")
    period = {row["video"]: row for row in q["rows"]}
    return {"period": {"start": start.isoformat(), "end": end.isoformat()},
            "videos": [{"videoId": vid, "lifetime": lifetime.get(vid), "period": period.get(vid)} for vid in videoIds]}


@mcp.tool()
def channel_overview(days: int = 28) -> dict:
    """Channel overview for the last N days: totals, daily trend, and top 10 videos by views."""
    start, end = _period(days)
    totals = _query("views,estimatedMinutesWatched,averageViewDuration,subscribersGained,subscribersLost,likes,comments,shares", start, end)
    daily = _query("views,estimatedMinutesWatched,subscribersGained,subscribersLost", start, end, dimensions="day", sort="day")
    top = _query("views,estimatedMinutesWatched,averageViewDuration,likes", start, end, dimensions="video", sort="-views", max_results=10)
    titles = {}
    ids = [r["video"] for r in top["rows"]]
    if ids:
        r = _yt().videos().list(part="snippet", id=",".join(ids)).execute()
        titles = {v["id"]: v["snippet"]["title"] for v in r.get("items", [])}
    for row in top["rows"]:
        row["title"] = titles.get(row["video"])
    return {"channel": _my_channel(), "period": {"start": start.isoformat(), "end": end.isoformat()},
            "totals": totals["rows"][0] if totals["rows"] else {}, "daily": daily["rows"], "topVideos": top["rows"]}


@mcp.tool()
def traffic_and_audience(days: int = 28, videoId: Optional[str] = None) -> dict:
    """Traffic sources, YouTube search terms, countries, device types, and age/gender for the channel
    (or one video) over the last N days."""
    start, end = _period(days)
    flt = f"video=={videoId}" if videoId else None
    join = lambda extra: f"{flt};{extra}" if flt else extra  # noqa: E731
    out = {"period": {"start": start.isoformat(), "end": end.isoformat()}, "videoId": videoId}
    out["trafficSources"] = _query("views,estimatedMinutesWatched", start, end, dimensions="insightTrafficSourceType", filters=flt, sort="-views")["rows"]
    try:
        out["searchTerms"] = _query("views", start, end, dimensions="insightTrafficSourceDetail",
                                    filters=join("insightTrafficSourceType==YT_SEARCH"), sort="-views", max_results=25)["rows"]
    except Exception as e:  # noqa: BLE001
        out["searchTerms"] = f"unavailable: {e}"
    out["countries"] = _query("views,estimatedMinutesWatched", start, end, dimensions="country", filters=flt, sort="-views", max_results=15)["rows"]
    out["devices"] = _query("views", start, end, dimensions="deviceType", filters=flt, sort="-views")["rows"]
    try:
        out["ageGender"] = _query("viewerPercentage", start, end, dimensions="ageGroup,gender", filters=flt, sort="-viewerPercentage")["rows"]
    except Exception as e:  # noqa: BLE001
        out["ageGender"] = f"unavailable: {e}"
    return out


@mcp.tool()
def compare_new_video(videoId: str, window_days: int = 7, baseline_videos: int = 10) -> dict:
    """Compare a video's first N days (views, watch time, avg view duration, subs gained) against the average
    first N days of the previous `baseline_videos` uploads. Tells you if a new video is over- or under-performing."""
    yt = _yt()
    ch = _my_channel()
    # Recent uploads, newest first
    items, page = [], None
    while len(items) < baseline_videos + 25:
        r = yt.playlistItems().list(part="contentDetails,snippet", playlistId=ch["uploadsPlaylist"], maxResults=50, pageToken=page).execute()
        items += r.get("items", [])
        page = r.get("nextPageToken")
        if not page:
            break
    pub = {i["contentDetails"]["videoId"]: i["contentDetails"].get("videoPublishedAt") or i["snippet"]["publishedAt"] for i in items}
    if videoId not in pub:
        r = yt.videos().list(part="snippet", id=videoId).execute().get("items", [])
        if not r:
            raise ValueError(f"Video not found on this channel: {videoId}")
        pub[videoId] = r[0]["snippet"]["publishedAt"]
    order = sorted(pub, key=lambda k: pub[k], reverse=True)
    older = [v for v in order if pub[v] < pub[videoId]][:baseline_videos]

    def first_window(vid: str) -> dict:
        d0 = datetime.fromisoformat(pub[vid].replace("Z", "+00:00")).date()
        d1 = min(d0 + timedelta(days=window_days - 1), date.today() - timedelta(days=2))
        q = _query("views,estimatedMinutesWatched,averageViewDuration,subscribersGained,likes", d0, d1, filters=f"video=={vid}")
        row = q["rows"][0] if q["rows"] else {}
        return {"videoId": vid, "publishedAt": pub[vid], "daysCovered": (d1 - d0).days + 1, **row}

    target = first_window(videoId)
    base = [first_window(v) for v in older]
    keys = ["views", "estimatedMinutesWatched", "averageViewDuration", "subscribersGained", "likes"]
    avg = {k: round(sum(float(b.get(k, 0) or 0) for b in base) / len(base), 2) for k in keys} if base else {}
    ratio = {k: (round(float(target.get(k, 0) or 0) / avg[k], 2) if avg.get(k) else None) for k in keys}
    return {"windowDays": window_days, "target": target, "baselineAverage": avg, "baselineCount": len(base),
            "ratioVsBaseline": ratio, "baseline": base}


# --------------------------------------------------------------------------- comments
@mcp.tool()
def list_comments(videoId: Optional[str] = None, max_results: int = 50, only_without_owner_reply: bool = True) -> dict:
    """List recent top-level comments for one video (or the whole channel). By default only threads the channel
    owner has not replied to yet."""
    yt = _yt()
    ch = _my_channel()
    kwargs: dict[str, Any] = dict(part="snippet,replies", maxResults=min(100, max_results), order="time", textFormat="plainText")
    if videoId:
        kwargs["videoId"] = videoId
    else:
        kwargs["allThreadsRelatedToChannelId"] = ch["channelId"]
    r = yt.commentThreads().list(**kwargs).execute()
    out = []
    for t in r.get("items", []):
        top = t["snippet"]["topLevelComment"]["snippet"]
        replies = [c["snippet"] for c in t.get("replies", {}).get("comments", [])]
        owner_replied = any(c.get("authorChannelId", {}).get("value") == ch["channelId"] for c in replies)
        if only_without_owner_reply and owner_replied:
            continue
        out.append({"threadId": t["id"], "videoId": top.get("videoId"), "author": top["authorDisplayName"],
                    "text": top["textDisplay"], "likes": top["likeCount"], "publishedAt": top["publishedAt"],
                    "replyCount": t["snippet"]["totalReplyCount"], "ownerReplied": owner_replied})
    return {"count": len(out), "comments": out}


@mcp.tool()
def reply_to_comment(threadId: str, text: str) -> dict:
    """Post a reply to a comment thread as the channel. Only call after the user approved the exact text."""
    r = _yt().comments().insert(part="snippet", body={"snippet": {"parentId": threadId, "textOriginal": text}}).execute()
    _quota_add("comment_insert")
    return {"commentId": r["id"], "threadId": threadId, "text": r["snippet"]["textOriginal"]}


@mcp.tool()
def upload_history(limit: int = 20) -> dict:
    """Show the last uploads made through this connector."""
    return {"uploads": _read_uploads()[-limit:]}


# --------------------------------------------------------------------------- snapshots & alerts
@mcp.tool()
def snapshot_stats() -> dict:
    """Record today's channel totals and every video's lifetime views/likes/comments into the local history
    database. A scheduled task runs this daily; call it manually to refresh."""
    return _take_snapshot()


@mcp.tool()
def video_trend(videoId: str, days: int = 30) -> dict:
    """Day-by-day views/likes/comments for a video from the local daily snapshots (growth per day), plus the
    YouTube Analytics daily views for the same period as a cross-check."""
    con = _db()
    rows = con.execute("SELECT day, views, likes, comments FROM video_snapshots WHERE videoId=? ORDER BY day", (videoId,)).fetchall()
    con.close()
    rows = rows[-days:]
    trend, prev = [], None
    for day, views, likes, comments in rows:
        trend.append({"day": day, "views": views, "likes": likes, "comments": comments,
                      "viewsGained": (views - prev) if prev is not None else None})
        prev = views
    start, end = _period(days)
    try:
        api_daily = _query("views,estimatedMinutesWatched", start, end, dimensions="day", filters=f"video=={videoId}", sort="day")["rows"]
    except Exception as e:  # noqa: BLE001
        api_daily = f"unavailable: {e}"
    return {"videoId": videoId, "snapshotDays": len(trend), "snapshots": trend, "analyticsDaily": api_daily,
            "note": "Snapshots start from the day the daily task first ran; earlier days come only from analyticsDaily."}


@mcp.tool()
def channel_trend(days: int = 30) -> dict:
    """Subscribers / total views / video count per day from the local daily snapshots."""
    con = _db()
    rows = con.execute("SELECT day, subscribers, views, videos FROM channel_snapshots ORDER BY day").fetchall()
    con.close()
    out, prev = [], None
    for day, subs, views, vids in rows[-days:]:
        out.append({"day": day, "subscribers": subs, "views": views, "videos": vids,
                    "subsGained": (subs - prev[0]) if prev else None, "viewsGained": (views - prev[1]) if prev else None})
        prev = (subs, views)
    return {"days": len(out), "trend": out}


@mcp.tool()
def performance_alerts(limit: int = 20, run_now: bool = False) -> dict:
    """Automatic verdicts recorded 1 and 3 days after each upload (better / about average / worse than the
    previous 10 uploads). run_now=True evaluates any pending checks immediately instead of waiting for the daily task."""
    new = _run_checks() if run_now else []
    alerts = []
    if _alerts_file().exists():
        for line in _alerts_file().read_text(encoding="utf-8").splitlines():
            try:
                alerts.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return {"newThisCall": len(new), "alerts": alerts[-limit:]}


# --------------------------------------------------------------------------- entry
if __name__ == "__main__":
    if "--auth" in sys.argv:
        _credentials(interactive=True)
        ch = _my_channel()
        print("Authorized. Connector will act on channel:", json.dumps(ch, indent=2))
    elif "--weekly" in sys.argv:
        # Monday task: refresh style profile and write the weekly report.
        log = _p("data/daily.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        try:
            _build_style_profile()
            r = weekly_report()
            msg = f"{datetime.now().isoformat(timespec='seconds')} weekly report ok {r['savedTo']}"
        except Exception as e:  # noqa: BLE001
            msg = f"{datetime.now().isoformat(timespec='seconds')} WEEKLY FAILED {e!r}"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
        print(msg)
    elif "--daily" in sys.argv:
        # Run by the Windows scheduled task: snapshot stats, then evaluate pending new-video checks.
        log = _p("data/daily.log")
        log.parent.mkdir(parents=True, exist_ok=True)
        try:
            snap = _take_snapshot()
            alerts = _run_checks()
            msg = f"{datetime.now().isoformat(timespec='seconds')} snapshot ok {snap} alerts={len(alerts)}"
        except Exception as e:  # noqa: BLE001
            msg = f"{datetime.now().isoformat(timespec='seconds')} FAILED {e!r}"
        with log.open("a", encoding="utf-8") as fh:
            fh.write(msg + "\n")
        print(msg)
    else:
        mcp.run()
