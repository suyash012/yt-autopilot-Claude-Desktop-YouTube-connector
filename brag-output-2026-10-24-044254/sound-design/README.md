# Sound design for the 9:16 voiced cut

The music and sound effects in `brag-voiced.mp4` are written in code, not taken from a library. `build_score.py` synthesises them with numpy and scipy, mixes them under the recorded voiceover and writes one stereo file, `composition-voiced/assets/audio/mix.wav`. There are no samples and no third-party music, so nothing needs a credit.

## Rebuild

```bash
pip install numpy scipy
cd sound-design
python build_score.py --vo ../composition-voiced/assets/vo/voiceover.wav \
                      --out ../composition-voiced/assets/audio/mix.wav
```

It takes about 30 seconds and gives the same file every time. Run it again after changing the voiceover (for example a re-recorded line): the ducking follows the speech it finds in the file. Then render with `npx hyperframes render` from `composition-voiced/`.

Options worth knowing: `--vo-db` (voice gain, default +3), `--music-db` (music and effects level, default −6; pass nothing to solve it for `--lufs` instead), `--ui-db` (interface sounds, default −12), `--lufs` (loudness target when solving), `--ceiling` (true-peak ceiling in dB, default −1.8), `--margin-shift` (positive makes the music stay further under the voice), `--duck-low` (how far the bass and kick give way under speech), `--stems DIR` (also write the music, interface sounds and voice separately; with `--bus-stems`, every instrument bus).

## What you hear

| Time (s) | What happens | On screen |
|---:|---|---|
| 0.27 | A swell that follows the focus-pull, then a boom | "Your upload button" lands |
| 0.83 | A thump | "is one sentence" |
| 1.5–3.5 | Tension under the first line: a rising sub-bass, heartbeat kicks, ticking hats, a snare roll, then 0.1 s of silence | |
| 3.55 | The drop (A minor): sub boom, kick, crash, chord stab, bell | The name lands |
| 5.7–6.3 | A fill into the chat window, a message pop, a card slide | Message sent, draft card |
| 6.5–8.7 | A lighter bed under the voice; soft ticks as the title types in; two rising bell pings for "validated" and "uploaded" | Draft, validate, upload |
| 10.4–11.35 | Second message pop, a rising sub-bass and a snare roll, then 0.1 s of silence | "publish it" |
| 11.46 | The biggest hit, and a lift to C major: sub boom, bell run, then the full chorus with claps, stabs, arpeggio and a bell line | "Published" |
| 14.19, 15.82 | Two smaller accents | The two highlight cards |
| 18.55 | The outro hit | "Upload by name." |
| 19.10, 20.19 | A bell for each | Second outro line, credit |
| 21–23.4 | A low riser and a heartbeat under your closing line, a gap, then the last hit with a long tail | "If you want the repo, comment for the link." |

Tempo is 110 BPM. Two beat grids are anchored on the two big moments (the name at 3.553 s and "Published" at 11.459 s), so every accent in the video lands on a beat.

## How it stays out of the voice's way

- The voice track is not touched here. The only thing that reaches it is the final limiter, which pulls the whole mix down by 2–3 dB for a split second on five of the big hits (0.3, 3.65, 11.5, 15.8 and 18.7 s).
- Under speech the music is ducked per band, and a spectral ceiling keeps it a set margin below your speech level in each band (about 14 dB across 500 Hz–4 kHz, less for the bass, none for the very top). Between phrases it opens up.
- Big hits skip the ducking for their first moments, so they land. After that they sit under the voice like everything else.
- A transcription of the rendered video's sound finds the same sentences as your voice alone (mean word confidence 0.81 against 0.78), so the music is not hiding any words.
- The loudness is −13.4 LUFS in the rendered video with a true peak of −1.6 dBFS. The kick, boom and bass are mostly below what a phone speaker plays, so the hits also carry mid and high content that does come through.

## Files

- `build_score.py`: the arrangement (what plays when), the interface sounds, the voice-aware mix and the loudness and limiting.
- `synth.py`: the instruments (kick, boom, claps, hats, bass, pads, plucks, bells, risers) and the DSP (filters, reverb, limiter, loudness meter, spectral ducking).
