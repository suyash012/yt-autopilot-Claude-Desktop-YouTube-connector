# Hyperframes Composition Brief: yt-autopilot

## Objective
Create a short launch-style brag video for yt-autopilot: a local MCP connector that uploads videos to YouTube from Claude Desktop.

## Output
- Composition directory: `brag-output/composition/`
- Rendered video: `brag-output/brag.mp4`
- Format: landscape — 1920x1080
- Duration: 22 seconds

## Source Material
- Project root: the repository root (`/home/user/yt-autopilot-Claude-Desktop-YouTube-connector`)
- Primary files read: `README.md`, `SETUP GUIDE.md`, `config.json`, `requirements.txt`, `server.py` (tool list)
- Product name: yt-autopilot
- Tagline / strongest claim: "Talk to Claude Desktop to upload videos to your YouTube channel and review how they perform."
- Key UI or visual moment to recreate: the chat flow. A user message, a draft card with title and hashtags, the tool trace, "Uploaded · private", "publish it", "Published".
- Copy that must appear verbatim (or near it):
  - "upload launch-cut to YouTube" (the user message; from the README's "upload <part of the file name> to YouTube")
  - "Upload any video on your PC by name." paraphrased as "Upload by name."
  - "Publish when you say so." (from "It never publishes without you saying 'publish'.")
  - "MIT" and the music credit line

## Creative Direction
- Tone preset: `default`
- Creative direction: a calm chat window that is quietly pleased with itself. Understated, never shouty.
- Interpretation: short lines, one accent colour, large type at start and end, the working chat at real pace in the middle. Restraint over effects.
- Angle: the whole upload is one sentence, and the human still chooses when it goes public. See `brag-plan.md`.
- Hook: "Your upload button" (0.27 s) and "is one sentence." (0.82 s).
- Outro / punchline: "Upload by name." then "Publish when you say so.", with the credit line last.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Claude or YouTube logos. The chat window is a stylised stand-in, not a screenshot.
  - Any fabricated metric. Every number on screen is either from the project (the hashtag rules, 9:15) or part of the fictional draft (the "30 seconds" title and the tags).

## Visual Identity
- Background: `#0C0D11`
- Text: `#F3F1EA` (muted text `#A4AAB7`)
- Accent: `#FF8A5B`
- Success: `#6EE7B0`
- Display font: Archivo Black (bundled)
- Body font: Inter (bundled)
- Code and credit font: JetBrains Mono (bundled)
- Visual references from the project: the README's daily-use list and the tool names in `server.py`. The repo has no stylesheet to take colours from.

## Storyboard
Use the storyboard in `brag-output/brag-plan.md` as the creative contract.

Scene summary:
1. Hook — 0.00–2.95 s — "Your upload button is one sentence."
2. Reveal — 3.00–5.50 s — "yt-autopilot" and "Upload to YouTube by talking."
3. The working flow — 5.20–13.80 s — chat window: user message, draft card, tool trace, "Uploaded · private", "publish it", "Published".
4. Highlights — 13.60–18.00 s — "Shorts hashtag rules, checked before upload." and "Weekly report, saved every Monday at 9:15."
5. Punchline and credit — 18.00–22.00 s — "Upload by name." "Publish when you say so." and the credit line.

## Audio
- Audio role: warm bed with sparse professional accents
- Audio arc: steady bed through the whole video; one hit per scene change; a click for each user message; the biggest hit on "Published"; music fades out under the credit.
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (copied to `composition/assets/music/`)
- Music treatment: volume 0.35, no ducking, `data-fade-out="1.6"` over the final 22 s.
- Music cue guidance: bundled preset `skills/brag/assets/music/cues/happy-beats-business-moves-vol-10-by-ende-dot-app.music-cues.md`, 109.96 BPM. Three major locks: 3.553 s, 6.281 s, 11.459 s (strong cues, each within ±0.15 s of the planned reveal). Beat-grid snaps at 5.735, 7.349, 7.79, 8.22, 8.731, 10.379, 14.20, 15.28, 18.01, 18.55 and 19.64 s (within ±0.10 s).
- Audio-reactive treatment: subtle. The background glow follows a 2-second smoothed bass envelope of the track, one value per second, opacity 0.24 to 0.38. Extracted with `audio/scripts/extract-audio-data.py` (media-use skill, 30 fps, 8 bands) and embedded as a short array. No waveform, equaliser or heavy pulsing.
- Audio-coupled moments:
  - Hook — headline — impact hit at 0.27 s
  - Reveal — name landing — bell at 3.553 s
  - Scene 3 — user message — click at 5.735 s
  - Scene 3 — draft card — card slide at 6.26 s
  - Scene 3 — user message "publish it" — click at 10.379 s
  - Scene 3 — "Published" — bell at 11.459 s
  - Scene 4 — highlight lines — card placement at 14.20 s and 15.28 s
  - Scene 5 — "Upload by name." — hit at 18.01 s
- SFX selection guidance: picked from the bundled library per `sfx-analysis.md`. Low-risk files for polished moments.
- SFX analysis guidance: not used for filtering. The chosen files are short and mid-weight, with no sharp high-frequency transients.
- Exact SFX choice: nine hits, listed in `composition/index.html`.
- Audio files: copied into `composition/assets/` (music, sfx, and `vendor/gsap.min.js`).

## Hyperframes Instructions
Built from the Hyperframes 0.8.191 package docs and skill references (`hyperframes docs`, the `hyperframes`, `hyperframes-cli` and `media-use` skill references). The brag skill's own workflow applies:
- One composition file (`composition/index.html`), `data-composition-id="main"`, 1920x1080, `data-duration="22"`.
- Scenes are timed `class="clip"` elements with `data-start` and `data-duration`. Each scene has its own `data-track-index`.
- A single paused GSAP timeline is registered as `window.__timelines["main"]`. All motion is `fromTo`/`to`, with no CSS transforms on animated elements and no `requestAnimationFrame`.
- GSAP is vendored at `assets/vendor/gsap.min.js` (gsap 3.14.2, the version in the scaffold) so rendering does not need a CDN.
- Audio uses `<audio>` with `id`, `data-start`, `data-duration`, `data-track-index` and `data-volume`. The music has `data-fade-out`.
- `npx hyperframes check` is the gate before render. Render goes to `brag-output/brag.mp4`.

Requirements:
- Shows real product copy and the flow it produces (chat, tool names, the states).
- Every on-screen text line is readable: each holds at least the floor in `step-2-plan.md` (about 0.5 s plus 0.3 s a word).
- Duration 22 seconds (15–25).
- Music and SFX included.
- Local creation and rendering only. No cloud render, no `publish`.
