# yt-autopilot

Talk to Claude Desktop to upload videos to your YouTube channel and review how they perform.
A small local MCP connector built on Google's official YouTube Data API v3 and YouTube
Analytics API. No third-party services, no subscriptions, your data stays on your PC.

**Who it is for:** YouTube creators (especially Shorts) who use Claude Desktop on Windows.
No programming knowledge needed to install.

## What it does

- **Upload** any video on your PC by name. Claude drafts the title, description, and hashtags
  in your channel's own style, checks them against YouTube's rules, and uploads as **private**.
  You review in YouTube Studio and say "publish it", or schedule a time.
- **Review performance**: channel overview, per-video stats, traffic sources and search terms,
  audience by country and device, day-by-day growth, and a 1-day and 3-day verdict for every
  new upload compared with your previous ten.
- **Weekly report** every Monday, saved as Markdown.
- **Comments**: list unanswered comments, draft replies, post only what you approve.
- **Playlists and thumbnails**, edit existing video metadata.
- **Safety**: duplicate-upload guard, strict Shorts hashtag rules (3 to 4 in the title,
  5 to 10 in the description), YouTube API quota tracking, dry-run mode.

## Install (Windows)

1. Follow [GOOGLE SETUP.md](GOOGLE%20SETUP.md) to get your own `client_secret.json`
   (10 minutes, free, once).
2. Download this repository as a zip and unzip it. Put `client_secret.json` next to
   `Install.bat`.
3. Quit Claude Desktop completely, then double-click **Install.bat**.
4. Sign in with Google when the browser opens. Done.

Full plain-language walkthrough: [SETUP GUIDE.md](SETUP%20GUIDE.md).

The installer installs Python 3.12 if needed, sets up the connector under
`%LOCALAPPDATA%\yt-autopilot`, registers it in Claude Desktop, creates the
`YouTubeUploads` folder with a Desktop shortcut, and schedules the daily stats snapshot
(09:00) and the Monday weekly report (09:15). No admin rights required.

## Daily use

In Claude Desktop:

```
upload <part of the file name> to YouTube
channel overview for the last 28 days
how did my last 5 videos do?
compare my newest video with the previous 10
best time to post
weekly report
show unanswered comments and draft replies
publish it
```

## Tools exposed to Claude

| Tool | Purpose |
|------|---------|
| youtube_auth_status, youtube_categories | Channel bound to the connector, category IDs |
| find_video_files, list_incoming_videos, write_video_metadata | Locate videos, read/write sidecar metadata |
| validate_metadata, get_style_profile | Shorts rules check, channel style learned from best videos |
| upload_video, publish_video, list_unpublished | Private upload, publish or schedule, what is waiting |
| set_thumbnail, update_video, list_my_videos | Manage existing videos |
| list_playlists, create_playlist, add_to_playlist | Playlists |
| video_stats, channel_overview, traffic_and_audience, compare_new_video | Analytics |
| snapshot_stats, video_trend, channel_trend, performance_alerts | Local daily history and automatic verdicts |
| best_time_to_post, weekly_report, quota_status, upload_history | Timing, reporting, quota, log |
| list_comments, reply_to_comment | Comments |

## Manual setup (for developers)

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
mkdir data
copy client_secret.json data\
.venv\Scripts\python server.py --auth
```

Then add to `%APPDATA%\Claude\claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "yt-autopilot": {
      "command": "C:/path/to/.venv/Scripts/python.exe",
      "args": ["C:/path/to/server.py"],
      "env": { "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1" }
    }
  }
}
```

CLI modes: `server.py --auth` (sign in), `--daily` (snapshot + checks), `--weekly`
(style profile + report). Without arguments it runs as a stdio MCP server.

## Files and privacy

- `data/client_secret.json` and `data/token.json` are your Google credentials. Never commit
  or share them. `.gitignore` already excludes `data/` and `client_secret.json`.
- `data/uploads.jsonl`, `data/stats.db`, `data/alerts.jsonl`, `data/reports/` are local
  history created by the tools.

## Limits

- Impressions and click-through rate are not available through the YouTube Analytics API;
  see YouTube Studio for those.
- YouTube's API quota allows roughly 6 uploads per day per Google Cloud project.
- While your Google app is in Testing mode, sign-in expires every 7 days. Publish the app in
  Google Cloud to stop that (see GOOGLE SETUP.md).

## License

MIT
