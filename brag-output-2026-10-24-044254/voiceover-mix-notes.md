# Voiceover mix notes

Your recording `Voice_261024_102410.m4a` (mono AAC, 128 kbps, 48 kHz, 28.7 s) mixed into the 9:16 video as `brag-voiced.mp4` (24.5 s, with captions in the chat section and your closing line on screen). The recording itself is not in the repo. The refined, aligned voice track is `composition-voiced/assets/vo/voiceover.wav`.

> **Update:** the music and sound effects in `brag-voiced.mp4` have since been replaced by an original, bolder score (the "Sound design" section at the end, and `sound-design/README.md`). The mix notes below describe your voice and where each line lands; the "Mixed" bullet is the current mix.

## What I found

| Check | Result |
|---|---|
| Content | The whole script, then the optional "yt-autopilot." sign-off, then your own closing line: "If you want the repo, comment for the link." |
| Level | Quiet: −21.8 LUFS integrated. Speech peaks −6 to −10 dBFS, no clipping in the speech. One thump at about 0.9 s (before the first word) reaches −0.5 dBFS. |
| Consistency | Even: 2.5 LU loudness range. Individual lines differ by up to 4.7 dB. |
| Noise | Floor around −46 dBFS. A 100 Hz mains hum (about 19 dB above the noise) and low-end rumble. |
| High end | Weak. Above 3 kHz the speech is only about 4 dB above the noise (about 0 dB above 6 kHz), so "s", "k" and "t" are faint. |
| Unclear words | "Claude drafts" (two transcribers heard "Lord draft" and "plot raspy"). "Shorts hashtag rules" lost its final "s" (heard "short hashtag rule"). "uploads" and "it's" are soft too. Nothing else was a problem. |
| Junk | 0–2.0 s: a thump, a breath and a false start. 26.8–28.7 s: handling noise. |
| Pace | Your lines run about 10% longer than my cue sheet assumed (about 15 s of speech against 14 s), and there are 0.5–0.7 s pauses between lines, so a few lines did not fit their windows (the name, "plus a weekly report", the outro). |

I used a local speech-to-text model (word timings, no prompt, so it could not be steered by the script) to find the lines and flag unclear words. I did not listen to the audio, so treat the "unclear words" as measurements, not a judgement of your voice.

## What I did

- **Cut** each line out of the take at its quietest point, with short fades, and dropped the junk.
- **Cleaned**: high-pass at 90 Hz, a narrow notch at 100 Hz for the hum, 2.5 dB less at 250 Hz, a little presence (+3 dB at 2.8 kHz) and air (+4 dB shelf from 5 kHz). I tested a denoiser and left it out: it only removed the little high end there was.
- **Leveled** every line to the same loudness (within ±3 dB), shaved two click transients ("it" in "publish it" and one in "hashtags"), then set the voice to −16 LUFS with a limiter that works at 4× oversampling, so the true peak is −1.9 dBFS.
- **Placed** each line on the video's timeline so your key words land on the visuals. Two lines (the first and "uploads it's private") are 5% faster; pauses inside "Meet … yt-autopilot" and "plus … a weekly report" are shorter.
- **Retimed the video** to your delivery: the second highlight appears at 15.82 s (was 15.28), the outro lines at 18.55 and 19.10 s (were 18.01 and 18.55), and the credit at 20.19 s. The video is 24.5 s instead of 22.0 s, still under the 25 s limit. The chat flow is unchanged, except that the chat window is drawn at 90% size and sits higher, to leave room for the captions.
- **Added text on screen**: your closing line, "If you want the repo, comment for the link.", appears word by word with your voice once the outro lines clear (20.95 s), with "comment for the link." large in the accent colour. Captions are on only for the chat section (6.35–12.05 s), where your words are not otherwise on screen: "Claude drafts the title and hashtags, uploads it private, then you say "publish it" and it's live." They pop in word by word in a strip below the chat window, above the platform UI band.
- **Mixed**: the voice is not processed beyond the cleanup above. Under it, the original score and effects are ducked per band and kept a set margin below your speech level (about 14 dB across 500 Hz–4 kHz), so they open up between phrases and on the big hits. The video's sound is −13.6 LUFS with a true peak of −1.4 dBFS. A transcription of the final mix finds the same sentences as your voice alone (mean word confidence 0.81 against 0.78), so the music is not hiding any words.

## Where your lines land

| Line | Plays at | Lands on |
|---|---|---|
| What if uploading was just a sentence? | 0.30–2.72 s | The headline |
| Meet … yt-autopilot. | 3.00–4.69 s | The name and the bell at 3.55 s |
| Claude drafts the title and hashtags, | 6.35–8.21 s | The draft card |
| uploads it's private, | 8.40–9.52 s | "Uploaded · private" |
| then you say publish it and it's live. | 9.80–11.90 s | "publish it" at 10.38 s, "live" on the bell at 11.46 s |
| It checks Shorts hashtag rules first. | 14.25–16.39 s | Highlight 1 |
| plus a weekly report | 16.55–18.24 s | Highlight 2 |
| upload by name, publish when you say so. | 18.58–20.70 s | The two outro lines |
| If you want the repo, comment for the link. | 21.15–23.41 s | The closing text, word by word |

## Left out

- The optional "yt-autopilot." sign-off. With it, the video runs to about 26 s, over the 25 s limit. Your recording of it is clear, so it can go back in if you want to trade length for it.
- Captions outside the chat section. The hook, the name, the two highlights and the outro already show the words you say, so a caption there would only repeat them. They are easy to add if you would rather caption every line.

## If you re-record

Only "Claude drafts the title and hashtags" needs it. Hold the phone 10–15 cm from your mouth, slightly off to one side, switch off any "voice clarity" or noise-suppression setting, and say the "cl" of Claude and the "ts" of drafts a little harder. A single line is enough; it drops straight in at 6.35 s.

## Sound design (second pass)

The first mix used a stock track (Happy Beats, Sascha Ende, CC BY 4.0) and nine small effects (Kenney, CC0). It was clean but light, so it was replaced with a score written for this video. The old mix is still in the git history (commit 9104186).

- **Original and credit-free.** Everything is synthesised in code (`sound-design/build_score.py`, numpy and scipy, no samples), so the credit line is now just `yt-autopilot · MIT`.
- **Built around the story.** 110 BPM, with the beat grid anchored on the name (3.553 s) and on "Published" (11.459 s), so every visual accent lands on a beat. A minor for the build and the name, C major from "Published" on, so the payoff is a lift, not just a louder bar.
- **The big moments hit harder.** A boom on "Your upload button" (0.27 s), a rising build with a short silence and the drop on the name (3.55 s), a second build into the biggest hit on "Published" (11.46 s) followed by a full chorus, two smaller accents on the highlight cards, the outro hit on "Upload by name." (18.55 s), and a last hit with a long tail after "link." (23.46 s).
- **New interface sounds.** Message pops, a card slide, soft ticks as the title types in, and two rising bell pings for "validated" and "uploaded", all in key with the music.
- **Kept out of the way.** The spectral ducking described above; the first moments of each big hit skip it so they still land.
- **Rebuild.** `sound-design/README.md` has the command, the cue sheet and the options. Re-run it if you re-record a line.
