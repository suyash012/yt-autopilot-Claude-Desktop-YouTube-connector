# Brag Plan: yt-autopilot (9:16)

This is the vertical run. The angle, tone and timeline are the same as the landscape run in `brag-output/`, so one voiceover script fits both. What changes here is the format, the layout (re-composed for a tall frame, not cropped), a "Claude Desktop" label on the chat window, the wording of the second highlight, and the voiceover script.

## What is this app?

A small local MCP connector that lets you talk to Claude Desktop to upload videos to your YouTube channel and review how they perform. It runs on your PC, uses Google's own YouTube APIs, and has no subscriptions or third-party services.

## The angle

The upload button is a sentence. You type "upload <part of the file name> to YouTube" into a chat. Claude drafts the title and hashtags in your channel's style, checks them against the Shorts rules, uploads the video as private, and waits for you to say "publish it". The joke is that all the work fits in one sentence, and you still decide when it goes public.

## Hook (first 2-3 seconds)

Four stacked lines in large display type: "Your upload / button" lands on the first beat (0.27 s), then "is one / sentence." lands on the next beat (0.82 s), with "one sentence." in the accent colour. The first two lines are on screen from frame 0.

## Key moments (the middle)

- The working flow in a tall chat window, read top to bottom: the user's message "upload launch-cut to YouTube", a draft card (title with 3 hashtags, description with 5 tags), tool calls `validate_metadata` and `upload_video`, and the status "Uploaded · private".
- The user says "publish it", `publish_video` runs, and the status flips to "Published" on the strongest cue in the track.
- Two rules the product keeps, as short highlight lines: Shorts hashtag rules checked before upload, and the weekly report every Monday at 9:15.

## Outro / punchline

"Upload by name. Publish when you say so." Then a two-line credit: name and MIT, and the music credit. The credit is required by the bundled track's CC BY 4.0 licence.

## User flow worth showing

- Entry: say "upload <part of the file name> to YouTube".
- Key action: Claude drafts title, description and hashtags, checks YouTube's rules, and uploads as private.
- Result: "Uploaded · private", then "publish it", then "Published".

Scene 3 shows this flow.

## Tone

- Preset: `default`
- Creative direction: a calm chat window that is quietly pleased with itself. Understated, never shouty.
- Interpretation: short lines, one accent colour, large type at the start and end, and the middle is the working chat at real pace. Restraint over effects.

## Format: vertical — 1080x1920

Platform safe zones: no text in the bottom 20% of the frame (below y = 1536), where Shorts, Reels and TikTok place their captions and controls; no text in the top 150 px; the right-aligned chat bubbles stay clear of the like/share column. `hyperframes check --caption-zone` enforces the bottom band.

## Duration: 22 seconds

## Visual identity (from the project)

The repo has no stylesheet and no brand colours, so the palette and faces are chosen for this video, the same as the landscape run:

- Background: `#0C0D11`
- Accent: `#FF8A5B`
- Text: `#F3F1EA`
- Success (for "Published"): `#6EE7B0`
- Display font: Archivo Black. Body: Inter. Tool trace and credit: JetBrains Mono. All three are bundled with Hyperframes.
- Sizes are larger than the landscape run so text reads on a phone: headline 144 px, name 150 px, chat text 38 to 46 px, highlights 72 px, outro 100 px, nothing under 32 px.
- Strongest visual element: the chat window with the draft card and the tool trace. It is a stylised recreation of the flow from the README's daily-use examples and the tool names in `server.py`, not a screen capture of Claude Desktop. The window bar names the app ("Claude Desktop"); there are no logos.

## Share copy (draft)

Made yt-autopilot. Your upload button is one sentence: "upload <part of the file name> to YouTube." Claude drafts the title, checks the Shorts hashtags, uploads it as private, and waits for you to say "publish it."

## Voiceover script

The user records the voice; nothing is generated. The lines complement the visuals instead of reading them. Full cue sheet, recording notes and mix notes are in `voiceover-script.md`.

1. (0.40) What if uploading was just a sentence?
2. (3.45) Meet yt-autopilot.
3. (6.45) Claude drafts the title and hashtags,
4. (8.40) uploads it private.
5. (9.75) Then you say, "publish it."
6. (11.10) And it's live.
7. (14.25) It checks Shorts hashtag rules first.
8. (16.10) Plus a weekly report.
9. (18.05) Upload by name.
10. (19.15) Publish when you say so.
11. (20.80, optional) yt-autopilot.

About 45 words, roughly 14 s of speech inside the 22 s. The window holds whether or not narration is on.

## Audio direction

- Role: warm bed with sparse professional accents.
- Music: `happy-beats-business-moves-vol-10-by-ende-dot-app.mp3` (Sascha Ende, CC BY 4.0). Compact, punchy, 109.96 BPM. Volume 0.35, fades out over the last 1.6 s.
- Music treatment: starts at 0 s, no ducking in `brag.mp4`. `brag-vo-bed.mp4` is the same render with the music at 0.14 (the 0.12 to 0.15 level the brag workflow uses under narration) and the sound effects at about 75%.
- Music cue guidance: bundled preset `cues/happy-beats-business-moves-vol-10-by-ende-dot-app.music-cues.md`. Three major locks, each within ±0.15 s: 3.553 s (name lands), 6.281 s (draft card), 11.459 s ("Published"). Sequential items snap to the beat grid at 5.735, 7.349, 7.79, 8.22, 8.731, 10.379, 14.20, 15.28, 18.01 and 18.55 s.
- Audio-reactive treatment: subtle. The background glow follows a 2-second smoothed bass envelope of the track (opacity 0.24 to 0.38). No waveform or equaliser graphics.
- Audio-coupled moments: hook hit at 0.27 s; name lands at 3.553 s; the two user messages click at 5.735 and 10.379 s; the draft card slides in at 6.26 s; "Published" bell at 11.459 s; highlight cards at 14.20 and 15.28 s; outro hit at 18.01 s.
- SFX posture: sparse (9 hits), motion-matched.
- Restraint rule: no SFX under the credit. The music fades out and the credit lands quietly.

## Storyboard

### Scene 1 — Hook — 0.00–2.95 s
On screen: "Your upload / button / is one / sentence." in four stacked lines.
Sequential/interaction: none.
Audio intent: a single soft hit on the first beat.
Audio-coupled idea: impact on the first two lines at 0.27 s.
Transition mood: hard, all four lines blur out together at 2.80 s.

### Scene 2 — Reveal — 3.00–5.50 s
On screen: "yt-autopilot" in large display type, landing on the strong cue at 3.553 s. Beneath it, in two lines: "Upload to YouTube / by talking."
Sequential/interaction: the subline arrives word by word.
Audio intent: a bell-like hit when the name lands.
Audio-coupled idea: name landing on the strong cue at 3.553 s.
Transition mood: soft blur out at 5.15 s.

### Scene 3 — The working flow — 5.20–13.80 s (centrepiece)
On screen: a tall chat window (936x1380) titled "Claude Desktop", read top to bottom:
- 5.30 s: window comes in with a blur.
- 5.735 s (beat): user message "upload launch-cut to YouTube".
- 6.281 s (strong cue): draft card. Title "Our launch day in 30 seconds #Shorts #launch #behindthescenes" arrives word by word from 6.50 s.
- 7.349 s (beat): description "Shot on a phone, edited in one afternoon."
- 7.79 s (beat): tags "#Shorts #creator #tips #making #indie".
- 8.22 s (beat): tool block `validate_metadata ✓` with "3 title tags · 5 description tags".
- 8.731 s (beat): tool block `upload_video ✓` with "private", and the status pill "Uploaded · private".
- 10.379 s (beat): user message "publish it".
- 11.459 s (strong cue): tool block `publish_video ✓` with "public", and the pill changes to "Published" in mint with a small pulse.
- 13.40 s: window blurs out.
Sequential/interaction: yes. The draft card and tool blocks build in order; the user messages arrive as sent messages.
Audio intent: clicks for each user message, a card slide for the draft, a bell for "Published".
Audio-coupled idea: user messages on beats 5.735 and 10.379 s; "Published" on the strong cue at 11.459 s.
Transition mood: blur swap on the same stage, no hard cut.

### Scene 4 — Highlights — 13.60–18.00 s
On screen: two lines with an accent marker, left-aligned, two lines each:
- 14.20 s (beat): "Shorts hashtag rules, / checked before upload."
- 15.28 s (beat): "Weekly report, / every Monday at 9:15."
Both hold to 17.80 s, then fade.
Sequential/interaction: yes, one per beat.
Audio intent: a card placement sound for each.
Audio-coupled idea: the two reveals on beats 14.20 and 15.28 s.
Transition mood: soft, blur out at 17.80 s.

### Scene 5 — Punchline and credit — 18.00–22.00 s
On screen: "Upload by name." (beat 18.01 s), then "Publish when / you say so." (beat 18.55 s, word by word, "Publish" in accent). The two-line credit "yt-autopilot · MIT / Music: Sascha Ende, ende.app (CC BY 4.0)" arrives at 18.55 s and holds to the end. The punchline blurs out at 21.60 s.
Sequential/interaction: none beyond the word-by-word reveal.
Audio intent: one hit on the first line, then the music fades out under the credit.
Audio-coupled idea: outro hit at 18.01 s.
Transition mood: hard entrance, quiet exit.

**Music mood for this video:** upbeat, clean (`default`).
**Audio summary:** a steady bed with one hit per scene change. The user messages click, the draft slides in, the bell marks the publish, and the music fades out under the credit.

## Claims and where they come from

Every line on screen is either from the project or is framing. Sources:

| On screen or spoken | Source in this repo |
|---|---|
| "Upload to YouTube by talking." (paraphrased); "Claude Desktop" on the window bar | `README.md` line 3 |
| "upload <part of the file name> to YouTube" | `README.md` daily use |
| Claude drafts title, description and hashtags, checks YouTube's rules, uploads as private | `README.md` "What it does" |
| 3 to 4 title hashtags, 5 to 10 description hashtags | `README.md` "Safety" |
| "Shorts hashtag rules, checked before upload" and "It checks Shorts hashtag rules first" | `README.md` "Safety" and "What it does" |
| "Then you say, publish it" and "And it's live" | `README.md` "What it does" and daily use (`publish_video`) |
| "Publish when you say so" | `SETUP GUIDE.md` "What this helper never does" |
| "Weekly report, every Monday at 9:15" and "Plus a weekly report" | `README.md` "What it does" and "Install" |
| Tool names `validate_metadata`, `upload_video`, `publish_video` | `server.py` function definitions |
| "MIT" | `README.md` "License" |
| Music credit "Sascha Ende, ende.app (CC BY 4.0)" (silent versions only) | `skills/brag/assets/music/README.md` in the brag repo |

Framing, not claims: "Your upload button is one sentence", "What if uploading was just a sentence?", the chat window, and the draft title, description and tags. The draft is a fictional example. No channel name, email address, file path or personal data appears in the video.

## Voiced cut (24.5 s)

`brag-voiced.mp4` is this plan with the user's recorded voiceover mixed in (`composition-voiced/`). The recording ran slower than the cue sheet and included a closing line of the user's own ("If you want the repo, comment for the link."), so the tail was retimed by whole beats and the video grew from 22 s to 24.5 s:

- Highlight 2 appears at 15.82 s (was 15.28 s); both highlights hold until 18.30 s.
- The outro lines appear at 18.55 s and 19.10 s (were 18.01 s and 18.55 s) and clear at 20.95 s. The credit appears at 20.19 s (was 18.55 s) and holds to the end.
- The music and effects are an original score written for this cut (`sound-design/`: 110 BPM, A minor into C major, beat grids anchored on 3.553 s and 11.459 s), mixed under the voice with per-band ducking; the sound is −13.6 LUFS. This replaces the stock track and the nine small effects of the first voiced mix (commit 9104186).
- Because the music is original, the credit is one line, `yt-autopilot · MIT`. The music credit in the sections above applies to the silent versions only.
- The optional "yt-autopilot." sign-off is not used (it would push the video past 25 s).
- The closing line is on screen, word by word with the voice (21.15–23.13 s): "If you want the repo," in grey and "comment for the link." large in the accent colour, above the credit. It holds to the end (24.5 s).
- Captions appear only in the chat section (6.35–12.05 s), where the spoken words are not otherwise on screen. The chat window is drawn at 90% size and sits higher, to leave a caption strip below it and above the platform UI band.

Scenes 1 and 2 are unchanged. Scene 3 keeps its timing; only the window's size and position change, and the captions are added. See `voiceover-mix-notes.md` for the findings on the recording and where each line lands.
