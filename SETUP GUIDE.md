# YouTube Autopilot for Claude: Setup Guide

This lets you talk to Claude to upload videos to your YouTube channel and see how they
perform. No technical knowledge needed.

## Before you start

- A Windows PC.
- Claude Desktop installed and signed in (download: https://claude.ai/download).
- The Google account that owns your YouTube channel, and its password.
- Your own `client_secret.json` from Google. Follow **GOOGLE SETUP.md** first (10 minutes,
  free) and put the file next to `Install.bat`. The installer waits for it if it is missing.

## Install (about 2 minutes)

1. Close Claude Desktop completely: right-click the Claude icon near the clock, choose **Quit**.
2. Unzip the package anywhere, for example on the Desktop.
3. Double-click **Install.bat**.
   - If Windows shows "Windows protected your PC", click **More info**, then **Run anyway**.
   - A black window shows progress. Wait for "Sign in to YouTube".
4. Press Enter. A browser opens.
   - Choose the Google account that owns your channel.
   - If you see "Google hasn't verified this app": click **Advanced**, then **Go to yt-autopilot**.
   - Tick every box and click **Continue** or **Allow**.
   - The page says you can close the window. Close it.
5. The black window says **Done**. Press Enter.
6. Open Claude Desktop.

## First check

In a new chat, type:

```
check youtube auth status
```

Claude should answer with your channel name. The first time, Claude asks permission to use
the tool. Click **Allow always**.

## Uploading a video

1. Save the video anywhere on this PC, for example Downloads. Or put it in the
   **YouTube Upload Inbox** folder that is now on your Desktop.
2. In Claude, type: `upload <part of the file name> to YouTube` and say in one line what the
   video is about.
3. Claude writes a title, description, and hashtags in your channel's style and shows them to
   you. Say what to change, or say **ok**.
4. Claude uploads the video as **private**. Open YouTube Studio, watch it once.
5. Back in Claude, say **publish it**. Or say **schedule it for Friday 6 pm**.

## Checking performance

Type any of these:

- `channel overview for the last 28 days`
- `how did my last 5 videos do?`
- `compare my newest video with the previous 10`
- `where are my views coming from?`
- `best time to post`
- `weekly report`
- `show unanswered comments and draft replies`

Every Monday at 9:15 a weekly report is also saved automatically.

## If something stops working

- **"Not authorized"**: double-click **Sign in to YouTube** on the Desktop and sign in again.
  This is needed about every 7 days until the app is verified by Google.
- **Claude cannot see yt-autopilot**: quit Claude Desktop completely and open it again.
- **Anything else**: take a photo of the message and send it to the person who shared this.

## What this helper never does

- It never publishes without you saying "publish".
- It never replies to comments without you approving the text.
- It never shares your Google password; the sign-in happens on Google's own page.
