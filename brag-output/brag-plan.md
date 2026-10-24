# Brag Plan: yt-autopilot

## What is this app?

A small local MCP connector that lets you talk to Claude Desktop to upload videos to your YouTube channel and review how they perform. It runs on your PC, uses Google's own YouTube APIs, and has no subscriptions or third-party services.

## The angle

The upload button is a sentence. You type "upload <part of the file name> to YouTube" into a chat. Claude drafts the title and hashtags in your channel's style, checks them against the Shorts rules, uploads the video as private, and waits for you to say "publish it". The joke is that all the work fits in one sentence, and you still decide when it goes public.

## Hook (first 2-3 seconds)

"Your upload button" lands on the first beat (0.27 s). "is one sentence." follows on the next beat (0.82 s), with "one sentence." in the accent colour. Plain, confident, a little smug. The full line is readable before 1 s.

## Key moments (the middle)

- The working flow, in a chat window at real pace: the user's message "upload launch-cut to YouTube" becomes a draft card (title with 3 hashtags, description with 5 tags), then tool calls `validate_metadata` and `upload_video`, then the status "Uploaded · private".
- The user says "publish it", `publish_video` runs, and the status flips to "Published". This is the payoff, on the strongest cue in the track.
- Two rules the product enforces, shown as short highlight lines: Shorts hashtag rules before upload, and the weekly report on Mondays at 9:15.

## Outro / punchline

"Upload by name." then "Publish when you say so." Then a credit line: name, MIT, and the music credit. The credit is required by the bundled track's CC BY 4.0 licence.

## User flow worth showing

- Entry: say "upload <part of the file name> to YouTube".
- Key action: Claude drafts title, description and hashtags, checks YouTube's rules, and uploads as private.
- Result: "Uploaded · private", then "publish it", then "Published".

The centrepiece scene (scene 3 below) shows this flow.

## Tone

- Preset: `default`
- Creative direction: a calm chat window that is quietly pleased with itself. Understated, never shouty.
- Interpretation: short lines, one accent colour, large type at the start and end, and the middle is the working chat rendered at real pace. Restraint over effects.

## Format: landscape — 1920x1080

## Duration: 22 seconds

## Visual identity (from the project)

The repo is a Python MCP server with no stylesheet and no brand colours, so there is nothing to copy. The palette and faces are chosen for this video:

- Background: `#0C0D11`
- Accent: `#FF8A5B`
- Text: `#F3F1EA`
- Success (for "Published"): `#6EE7B0`
- Display font: Archivo Black. Body: Inter. Tool trace and credit: JetBrains Mono. All three are bundled with Hyperframes.
- Strongest visual element: the chat window with the draft card and the tool trace. It is a stylised recreation of the flow from the README's daily-use examples and the tool names in `server.py`, not a screen capture of Claude Desktop.

## Share copy (draft)

Made yt-autopilot. Your upload button is one sentence: "upload <part of the file name> to YouTube." Claude drafts the title, checks the Shorts hashtags, uploads it as private, and waits for you to say "publish it."

## Audio direction

- Role: warm bed with sparse professional accents.
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (Sascha Ende, CC BY 4.0). Compact, punchy, 109.96 BPM. Volume 0.35, fades out over the last 1.6 s.
- Music treatment: starts at 0 s, no ducking, fade-out ends at 22 s.
- Music cue guidance: read from the bundled preset `cues/happy-beats-business-moves-vol-10-by-ende-dot-app.music-cues.md`. Three major locks, each within the ±0.15 s tolerance: 3.553 s (name lands), 6.281 s (draft card), 11.459 s ("Published"). Sequential items snap to the beat grid at 5.735, 7.349, 7.79, 8.22, 8.731, 10.379, 14.20, 15.28, 18.01, 18.55 and 19.64 s.
- Audio-reactive treatment: subtle. The background glow breathes with a 2-second smoothed bass envelope of the track (opacity 0.24 to 0.38). No waveform, equaliser or beat-pulse graphics.
- Audio-coupled moments: hook hit at 0.27 s; name lands at 3.553 s; draft card slides in at 6.26 s; the two user messages click at 5.735 and 10.379 s; "Published" bell at 11.459 s; highlight cards at 14.20 and 15.28 s; outro hit at 18.01 s.
- SFX posture: sparse (9 hits), motion-matched. No keyboard typing.
- Restraint rule: no SFX under the credit line. The music fades out and the credit lands quietly.

## Storyboard

### Scene 1 — Hook — 0.00–2.95 s
On screen: "Your upload button" (line 1), "is one sentence." (line 2, accent on the last two words). Dark ground, nothing else.
Sequential/interaction: none.
Audio intent: a single soft hit on the first beat.
Audio-coupled idea: impact on line 1 at 0.27 s.
Transition mood: hard, both lines blur out together at 2.95 s.

### Scene 2 — Reveal — 3.00–5.50 s
On screen: "yt-autopilot" in large display type, letters appearing one by one from beat 3.007 and landing together on the strong cue at 3.553 s. Beneath it: "Upload to YouTube by talking."
Sequential/interaction: yes, the name letters arrive one by one (0.05 s apart). The subline arrives word by word.
Audio intent: a bell-like hit when the name lands.
Audio-coupled idea: name landing on the strong cue at 3.553 s.
Transition mood: soft blur out at 5.15 s.

### Scene 3 — The working flow — 5.20–13.80 s (centrepiece)
On screen: a chat window (1360x780) with these beats:
- 5.30 s: window comes in with a blur.
- 5.735 s (beat): user message "upload launch-cut to YouTube".
- 6.281 s (strong cue): draft card. Title "Our launch day in 30 seconds #Shorts #launch #behindthescenes" arrives word by word from 6.50 s.
- 7.349 s (beat): description "Shot on a phone, edited in one afternoon."
- 7.79 s (beat): tags "#Shorts #creator #tips #making #indie".
- 8.22 s (beat): tool trace line "validate_metadata ✓ 3 title, 5 description tags".
- 8.731 s (beat): line "upload_video ✓ private" and status pill "Uploaded · private".
- 10.379 s (beat): user message "publish it".
- 11.459 s (strong cue): line "publish_video ✓ public", and the pill changes to "Published" in mint with a small pulse.
- 13.40 s: window blurs out.
Sequential/interaction: yes. The tool lines and the draft card build in order; the user messages arrive as sent messages.
Audio intent: clicks for each user message, a card slide for the draft, a bell for "Published".
Audio-coupled idea: user messages on beats 5.735 and 10.379 s; "Published" on the strong cue at 11.459 s.
Transition mood: blur swap on the same stage, no hard cut.

### Scene 4 — Highlights — 13.60–18.00 s
On screen: two lines with an accent marker, left-aligned:
- 14.20 s (beat): "Shorts hashtag rules, checked before upload."
- 15.28 s (beat): "Weekly report, saved every Monday at 9:15."
Both hold to 17.80 s, then fade.
Sequential/interaction: yes, one line per beat.
Audio intent: a card placement sound for each line.
Audio-coupled idea: the two line reveals on beats 14.20 and 15.28 s.
Transition mood: soft, blur out at 17.80 s.

### Scene 5 — Punchline and credit — 18.00–22.00 s
On screen: "Upload by name." (beat 18.01 s), then "Publish when you say so." (beat 18.55 s, word by word, "Publish" in accent). The credit line "yt-autopilot · MIT · Music: Sascha Ende, ende.app (CC BY 4.0)" arrives at 19.64 s and holds to the end. The two lines blur out at 21.60 s.
Sequential/interaction: none beyond the word-by-word reveal.
Audio intent: one hit on the first line, then the music fades out under the credit.
Audio-coupled idea: outro hit at 18.01 s.
Transition mood: hard entrance, quiet exit.

**Music mood for this video:** upbeat, clean (`default`).
**Audio summary:** a steady bed with one hit per scene change. The user messages click, the draft slides in, the bell marks the publish, and the music fades out under the credit.

## Claims and where they come from

Every line on screen is either from the project or is framing. Sources:

| On screen | Source in this repo |
|---|---|
| "Talk to Claude Desktop to upload videos to your YouTube channel" (subline, paraphrased) | `README.md` line 3 |
| "upload <part of the file name> to YouTube" | `README.md` daily use |
| Claude drafts title, description and hashtags, checks YouTube's rules, uploads as private | `README.md` "What it does" |
| 3 to 4 title hashtags, 5 to 10 description hashtags | `README.md` "Safety" |
| "Shorts hashtag rules, checked before upload" | `README.md` "Safety" and "What it does" |
| "Publish when you say so" | `SETUP GUIDE.md` "What this helper never does" |
| "Weekly report, saved every Monday at 9:15" | `README.md` "What it does" and "Install" |
| Tool names `validate_metadata`, `upload_video`, `publish_video` | `server.py` function definitions |
| "MIT" | `README.md` "License" |
| Music credit "Sascha Ende, ende.app (CC BY 4.0)" | `skills/brag/assets/music/README.md` in the brag repo |

Framing, not claims: "Your upload button is one sentence", the chat window, and the draft title, description and tags. The draft is a fictional example. No channel name, email address, file path or personal data appears in the video.
