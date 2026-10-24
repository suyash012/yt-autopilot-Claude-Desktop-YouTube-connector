# Hyperframes Composition Brief: yt-autopilot (9:16)

## Objective
Create the vertical (9:16) version of the yt-autopilot brag video. Same story, timeline and audio as the landscape run, re-composed for a tall frame, with a voiceover recorded by the user afterwards.

## Output
- Composition directory: `composition/` (in this run's folder)
- Rendered videos: `brag.mp4` (normal mix) and `brag-vo-bed.mp4` (music ducked for a voiceover)
- Format: vertical — 1080x1920
- Duration: 22 seconds

## Source Material
- Project root: the repository root (`/home/user/yt-autopilot-Claude-Desktop-YouTube-connector`)
- Primary files read: `README.md`, `SETUP GUIDE.md`, `config.json`, `requirements.txt`, `server.py` (tool list)
- Product name: yt-autopilot
- Tagline / strongest claim: "Talk to Claude Desktop to upload videos to your YouTube channel and review how they perform."
- Key UI or visual moment to recreate: the chat flow, as in the landscape run, on a tall window titled "Claude Desktop".
- Copy that must appear verbatim (or near it):
  - "upload launch-cut to YouTube" (the user message)
  - "Upload by name." and "Publish when you say so."
  - "MIT" and the music credit line

## Creative Direction
- Tone preset: `default`
- Creative direction: a calm chat window that is quietly pleased with itself. Understated, never shouty.
- Interpretation: short lines, one accent colour, large type at start and end, the working chat at real pace in the middle.
- Angle: the whole upload is one sentence, and the human still chooses when it goes public. See `brag-plan.md`.
- Hook: "Your upload / button / is one / sentence." (0.27 s and 0.82 s)
- Outro / punchline: "Upload by name. Publish when you say so.", with the credit last.
- Avoid:
  - Generic SaaS language
  - Abstract filler visuals
  - Claude or YouTube logos. The chat window is a stylised stand-in, not a screenshot.
  - Any fabricated metric. Every number on screen is either from the project (the hashtag rules, 9:15) or part of the fictional draft (the "30 seconds" title and the tags).
  - Text in the bottom 20% of the frame (platform UI) or in the top 150 px.

## Visual Identity
- Background: `#0C0D11`
- Text: `#F3F1EA` (muted text `#A4AAB7`)
- Accent: `#FF8A5B`
- Success: `#6EE7B0`
- Display font: Archivo Black (bundled)
- Body font: Inter (bundled)
- Code and credit font: JetBrains Mono (bundled)
- Type sizes are set for a phone: nothing under 32 px; headline 144 px; chat text 38 to 46 px.

## Storyboard
Use the storyboard in `brag-plan.md` as the creative contract.

Scene summary:
1. Hook — 0.00–2.95 s — four stacked lines: "Your upload / button / is one / sentence."
2. Reveal — 3.00–5.50 s — "yt-autopilot" and "Upload to YouTube / by talking."
3. The working flow — 5.20–13.80 s — tall chat window: user message, draft card, tool trace, "Uploaded · private", "publish it", "Published".
4. Highlights — 13.60–18.00 s — "Shorts hashtag rules, / checked before upload." and "Weekly report, / every Monday at 9:15."
5. Punchline and credit — 18.00–22.00 s — "Upload by name." "Publish when / you say so." and the two-line credit.

## Audio
- Audio role: warm bed with sparse professional accents
- Audio arc: steady bed through the whole video; one hit per scene change; a click for each user message; the biggest hit on "Published"; music fades out under the credit.
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (in `composition/assets/music/`)
- Music treatment: `brag.mp4` has volume 0.35 and `data-fade-out="1.6"`. `brag-vo-bed.mp4` is the same composition with the music at 0.14 and the sound effects at about 75% of their levels, so a voice recorded later sits on top without further mixing.
- Music cue guidance: bundled preset, 109.96 BPM. Three major locks: 3.553 s, 6.281 s, 11.459 s (within ±0.15 s). Beat-grid snaps at 5.735, 7.349, 7.79, 8.22, 8.731, 10.379, 14.20, 15.28, 18.01 and 18.55 s (within ±0.10 s).
- Audio-reactive treatment: subtle. The background glow follows a 2-second smoothed bass envelope of the track, one value per second, opacity 0.24 to 0.38. Extracted with the media-use `extract-audio-data.py` (30 fps, 8 bands) and embedded as a short array.
- Voiceover: recorded by the user, not generated. Lines and cues are in `voiceover-script.md`. No Kokoro, no transcription, no ducking lane; the bed variant is a plain re-render with lower levels.
- Audio-coupled moments: hook hit 0.27 s; name bell 3.553 s; clicks 5.735 and 10.379 s; draft slide 6.26 s; "Published" bell 11.459 s; card placements 14.20 and 15.28 s; outro hit 18.01 s.
- Exact SFX choice: nine hits, listed in `composition/index.html`.
- Audio files: in `composition/assets/` (music, sfx, `vendor/gsap.min.js`).

## Voiced cut
`composition-voiced/` is a copy of `composition/` with the user's recorded voiceover added (`assets/vo/voiceover.wav`, a 24 s mono track already aligned to the timeline) and rendered to `brag-voiced.mp4`. Differences from `composition/`: duration 24 s; a `vo` audio element; a `data-automation` volume lane on the music that ducks it to 40% while the voice speaks; sound effects at about 75%; highlight 2, the outro lines and the credit retimed to the beats at 15.82, 18.55, 19.64 and 20.19 s. Details and measurements are in `voiceover-mix-notes.md`.

## Hyperframes Instructions
Same conventions as the landscape run (Hyperframes 0.8.191): one `index.html`, `data-composition-id="main"`, now `data-width="1080" data-height="1920"` and `data-resolution="portrait"`; scenes are timed `class="clip"` sections with their own `data-track-index`; one paused GSAP timeline on `window.__timelines["main"]`; GSAP vendored locally.

Gate: `npx hyperframes check --caption-zone "x0=0;y0=.8;x1=1;y1=1;severity=error"`. It passes with no layout issues, 40 of 40 text checks passing WCAG AA, and no text in the bottom band. `snapshot --review` was used to judge phone-size legibility.

Requirements:
- Shows real product copy and the flow it produces (chat, tool names, the states).
- Every on-screen text line holds at least its reading floor.
- Duration 22 seconds (15–25).
- Music and SFX included.
- Local creation and rendering only. No cloud render, no `publish`.
