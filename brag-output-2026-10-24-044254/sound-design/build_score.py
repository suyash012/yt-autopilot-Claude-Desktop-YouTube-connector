#!/usr/bin/env python3
"""Original score, sound effects and final mix for the 9:16 voiced brag video (24.5 s).

Everything is synthesised here with numpy and scipy (no samples, no third-party music), so the
result needs no attribution. The script reads the recorded voiceover, writes the music and effects
around it, ducks them under the speech, sets the loudness and writes one stereo file:

    python build_score.py --vo ../composition-voiced/assets/vo/voiceover.wav \
                          --out ../composition-voiced/assets/audio/mix.wav

Grid: 110 BPM. Two beat grids are anchored on the two big visual moments, so every accent lands on
a beat: G1 on the name reveal (3.553 s) and G2 on "Published" (11.459 s). A minor for the build and
the name, C major from "Published" on.

Cue sheet (seconds)
    0.00-0.27   swell that follows the focus-pull into the first hit
    0.27        boom: "Your upload button" lands            0.83  thump: "is one sentence"
    1.45-3.46   tension under the first line: sub riser, heartbeat kicks, ticking hats, snare roll
    3.55        drop: the name (A minor), groove under "yt-autopilot"
    5.74 6.28   chat window: message sent, draft card (F), lighter bed with sub bass, pad, quiet plucks
    7.35-8.73   interface sounds: description, tags, validate and upload ticks (rising bells)
    10.38       second message sent: sub riser, kicks and a snare roll into a 0.1 s silence
    11.46       "Published": the biggest hit, major lift (C), bell run, then the full chorus
    14.19 15.82 highlight cards: two smaller accents
    18.55       outro hit (F)       19.10 second outro line       20.19 credit (C)
    21.0-23.4   closing line: low riser and heartbeat under the voice, a silence, then the last hit (23.46)

Mix: the voice is untouched. Under it the music is ducked per band (gentle gate-driven duck, then a
spectral ceiling that keeps it a set margin below the speech level, band by band); big hits bypass the
ducking for their first moments. The music gain is solved so the integrated loudness hits the target,
then a true-peak limiter (4x oversampled detector) keeps the ceiling.
"""
import argparse
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import synth as sy  # noqa: E402
from synth import SR  # noqa: E402

DUR = 24.5
N = int((DUR + 1.5) * SR)          # render a little past the end so reverb tails are complete
BEAT = 60.0 / 110.0
T_NAME, T_PUB = 3.553, 11.459
# brief total silence in the music just before the three biggest hits: the drop lands from nothing
VACUUM = [(3.465, 3.550), (11.350, 11.456), (23.405, 23.460)]


def g1(k):
    return T_NAME + k * BEAT


def g2(k):
    return T_PUB + k * BEAT


# MIDI notes per chord: bass root, pad voicing, arpeggio tones, stab voicing, bell, sub-boom pitch (Hz)
CH = {
    "Am": dict(root=33, pad=[52, 57, 60, 64, 69], arp=[69, 72, 76, 81], stab=[57, 60, 64, 69, 76], bell=81, boom=55.0),
    "F": dict(root=29, pad=[53, 57, 60, 65, 69], arp=[69, 72, 77, 81], stab=[53, 57, 60, 65, 72], bell=77, boom=43.65),
    "C": dict(root=36, pad=[48, 55, 60, 64, 67], arp=[72, 76, 79, 84], stab=[55, 60, 64, 67, 72], bell=84, boom=65.41),
    "G": dict(root=31, pad=[50, 55, 59, 62, 67], arp=[71, 74, 79, 83], stab=[55, 59, 62, 67, 74], bell=79, boom=49.0),
}


# ---------------------------------------------------------------------------- score container
class Score:
    """Named stereo buses plus reverb/delay sends; remembers kick times (for the pump) and protected hits."""

    BUSES = ("kick", "low", "bass", "perc", "pad", "arp", "bell", "fx", "ui")
    # per-bus balance in dB (applied where events are placed, so reverb sends follow)
    TRIM = dict(kick=-1.0, low=-2.0, bass=-3.0, perc=0.0, pad=5.0, arp=8.0, bell=-1.0, fx=3.0, ui=0.0)

    def __init__(self):
        self.b = {k: np.zeros((2, N)) for k in self.BUSES}
        self.hall = np.zeros((2, N))
        self.room = np.zeros((2, N))
        self.dly = np.zeros((2, N))
        self.uihall = np.zeros((2, N))
        self.kicks = []
        self.protect = []

    def put(self, bus, sig, t, g=1.0, pan=0.0, hall=0.0, room=0.0, dly=0.0):
        sig = np.asarray(sig, dtype=float)
        if sig.ndim == 1:
            sig = sy.stereo(sig, pan)
        i = int(round(t * SR))
        if i < 0 or i >= N:
            return
        n = min(sig.shape[1], N - i)
        s = sig[:, :n] * (g * 10 ** (self.TRIM[bus] / 20))
        self.b[bus][:, i:i + n] += s
        if hall:
            (self.uihall if bus == "ui" else self.hall)[:, i:i + n] += s * hall
        if room:
            self.room[:, i:i + n] += s * room
        if dly:
            self.dly[:, i:i + n] += s * dly


# ---------------------------------------------------------------------------- instruments, placed
def place_kick(S, rng, t, vel=1.0, pump=True):
    S.put("kick", sy.kick(rng, vel=1.0, f_end=50.0), t, vel)
    if pump:
        S.kicks.append((t, vel))


def place_clap(S, rng, t, vel=1.0):
    S.put("perc", sy.clap(rng), t, vel * 0.9, pan=0.05, room=0.45)


def place_snare(S, rng, t, vel=1.0, pan=0.0):
    S.put("perc", sy.snare(rng), t, vel * 0.8, pan=pan, room=0.35)


def place_hat(S, rng, t, vel=1.0, open_=False, pan=0.0):
    S.put("perc", sy.unit(sy.hat(rng, open_=open_), 0.45), t, vel * 1.2, pan=pan)


def place_roll(S, rng, t_end, n, step, v0, v1):
    """Snare roll ending one step before t_end: n hits, step seconds apart, crescendo."""
    for j in range(n):
        t = t_end - (n - j) * step
        place_snare(S, rng, t, v0 + (v1 - v0) * j / max(n - 1, 1), pan=(-0.2 if j % 2 else 0.2))


def place_bass(S, t, chord, dur, vel=1.0):
    f = float(sy.mtof(CH[chord]["root"]))
    S.put("bass", sy.bass_note(f, dur), t, 0.8 * vel)


def place_pad(S, t, chord, dur, vel=1.0, rel=0.25):
    for k, m in enumerate(CH[chord]["pad"]):
        S.put("pad", sy.pad_tone(float(sy.mtof(m)), dur, atk=0.2, rel=rel, sub=0.5 if k == 0 else 0.0), t, 0.16 * vel, hall=0.35)


def place_stab(S, t, chord, vel=1.0, dur=0.32, bright=6200.0):
    out = None
    for m in CH[chord]["stab"]:
        s = sy.supersaw(float(sy.mtof(m)), dur, voices=5, detune=0.2, rel=0.28, atk=0.004,
                        fc0=bright, fc1=1300.0, tau_f=0.16)
        out = s if out is None else out + s
    S.put("pad", out, t, 0.12 * vel, hall=0.4)


def place_arp(S, t_bar, chord, vel=1.0, eighths=8, start=0):
    tones = CH[chord]["arp"]
    pat = [0, 1, 2, 3, 2, 1, 2, 3]
    for i in range(start, eighths):
        f = float(sy.mtof(tones[pat[i % 8]]))
        t = t_bar + i * BEAT / 2
        S.put("arp", sy.pluck(f, 0.42, bright=4600.0, tau=0.17), t, 0.22 * vel, pan=(-0.45 if i % 2 else 0.45),
              hall=0.3, dly=0.35)


def place_bell(S, t, midi, vel=1.0, dur=1.8, hall=0.65, ratio=3.5, pan=0.0):
    S.put("bell", sy.bell(float(sy.mtof(midi)), dur=dur, ratio=ratio), t, 0.5 * vel, pan=pan, hall=hall)


def sparkle(S, t, chord, vel=1.0, n=7, step=0.045):
    """Rising run of small bells: the 'it worked' glitter."""
    tones = [m + 12 for m in CH[chord]["arp"]] + [CH[chord]["arp"][0] + 24, CH[chord]["arp"][1] + 24, CH[chord]["arp"][2] + 24]
    for i in range(n):
        place_bell(S, t + i * step, tones[i % len(tones)], vel * (0.8 - 0.07 * i), dur=1.1, hall=0.7,
                   pan=(-0.6 if i % 2 else 0.6))


def hit(S, rng, t, chord, size=1.0, bell=True, crash_dur=2.4):
    """A composite accent: sub boom + kick + crack + crash + exhale + chord stab + bass + bell."""
    root = CH[chord]["boom"]
    boom_dur = 0.8 + 1.2 * min(1.0, size)
    S.put("low", sy.sub_boom(rng, root=root, dur=boom_dur, tau_a=0.28 + 0.3 * size), t, 0.85 * size)
    place_kick(S, rng, t, min(1.0, 0.55 + 0.45 * size), pump=True)
    S.put("fx", sy.crack(rng), t, 0.42 * size, hall=0.25)
    S.put("fx", sy.crash(rng, dur=crash_dur * (0.5 + 0.5 * size)), t, 0.30 * size, hall=0.5)
    S.put("fx", sy.air_tail(rng, dur=1.0 + 0.8 * size), t, 0.22 * size, hall=0.3)
    place_stab(S, t, chord, 0.55 * size)
    place_bass(S, t, chord, 0.45 + 0.3 * size, 1.0 * min(1.0, size + 0.15))
    if bell:
        place_bell(S, t, CH[chord]["bell"], 0.6 * size, dur=1.2 + 0.8 * size)
    S.protect.append((t, 0.07 + 0.07 * size))


def reverse_crash(S, rng, t_end, dur, vel=1.0):
    c = sy.crash(rng, dur=dur * 1.15)
    c = sy.unit(c[: int(dur * SR)][::-1])
    n = len(c)
    ramp = (np.arange(n) / n) ** 1.8
    S.put("fx", sy.stereo(c * ramp), t_end - dur, 0.34 * vel, hall=0.2)


# ---------------------------------------------------------------------------- arrangement
def arrange(S, rng):
    # ---- 0.00-3.55 hook: focus-pull swell into a boom, a second thump, then a tension build
    S.put("fx", sy.noise_riser(rng, 0.27, f0=400, f1=9000, power=1.4), 0.0, 0.5)
    hit(S, rng, 0.27, "Am", size=0.95, bell=False, crash_dur=1.8)
    t2 = g1(-5)
    S.put("low", sy.sub_boom(rng, 55.0, dur=0.9, tau_a=0.25), t2, 0.6)
    place_kick(S, rng, t2, 0.85)
    S.put("perc", sy.tom(rng, f=98.0, vel=1.0), t2, 0.7, room=0.4)
    S.put("fx", sy.crack(rng), t2, 0.28, hall=0.2)
    S.protect.append((t2, 0.1))
    # drone that swells under the line, pulsing with heartbeat kicks
    n_dr = int((3.46 - 0.85) * SR)
    td = np.arange(n_dr) / SR
    dr = sy.sweep(0.5 * (sy.saw(55.0 * 1.003, n_dr) + sy.saw(55.0 * 0.997, n_dr, 0.4)), sy.expcurve(n_dr, 140.0, 900.0), 1.1, "lp")
    dr = sy.sat(dr * 0.9 + 0.9 * np.sin(2 * np.pi * 55.0 * td), 1.5) * (td / td[-1]) ** 1.2
    S.put("low", sy.edge(dr, 0.05, 0.004), 0.85, 0.55)
    for j, k in enumerate((-4, -3, -2, -1)):
        place_kick(S, rng, g1(k), (0.5, 0.6, 0.72, 0.85)[j])
    for j in range(6):                                           # ticking hats, 8ths getting louder
        place_hat(S, rng, g1(-3) + j * BEAT / 2, 0.12 + 0.07 * j, pan=0.3 if j % 2 else -0.3)
    S.put("low", sy.sub_riser(38.0, 120.0, 3.45 - 1.45, power=1.6), 1.45, 0.8)
    S.put("fx", sy.noise_riser(rng, 3.46 - 1.45, f0=300, f1=9500, q=1.6, power=2.2), 1.45, 0.5)
    S.put("fx", sy.tone_riser(220.0, 880.0, 3.46 - 2.0, vel=1.0), 2.0, 0.5, hall=0.2)
    place_roll(S, rng, g1(0), 6, BEAT / 4 * 0.98, 0.25, 0.9)
    reverse_crash(S, rng, g1(0) - 0.09, 0.85, 0.9)

    # ---- 3.553 the name: drop
    hit(S, rng, g1(0), "Am", size=1.0, crash_dur=2.6)

    # bars of Am (k 0-3), F (4-7), C (8-11), then G leading into "Published"; bar 1 is the full groove under the name
    for k in range(0, 4):
        t = g1(k)
        if k > 0:
            place_kick(S, rng, t, 0.8)
        if k in (1, 3):
            place_clap(S, rng, t, 0.75)
        place_hat(S, rng, t + BEAT / 2, 0.55, open_=True, pan=0.25)
        for off, v in ((0.0, 0.34), (0.25, 0.16), (0.75, 0.2)):
            place_hat(S, rng, t + off * BEAT, v, pan=-0.2 if off else 0.1)
        place_bass(S, t + BEAT / 2, "Am", BEAT * 0.42, 0.9)
    place_pad(S, g1(0), "Am", 4 * BEAT, 0.9)
    place_roll(S, rng, g1(4), 4, BEAT / 4, 0.3, 0.8)          # fill into the chat window (5.735)
    reverse_crash(S, rng, g1(4), 0.55, 0.5)

    # bars 2-3: the chat window. Lighter: pulse, sub bass, pad, quiet plucks.
    place_pad(S, g1(4), "F", 4 * BEAT, 0.75)
    place_pad(S, g1(8), "C", 4 * BEAT, 0.75)
    for k in range(4, 12):
        t = g1(k)
        ch = "F" if k < 8 else "C"
        if k in (4, 6, 8, 10):
            place_kick(S, rng, t, 0.78 if k in (4, 8) else 0.62)
        if k == 5:                                              # the draft card lands
            place_kick(S, rng, t, 0.7)
            place_stab(S, t, "F", 0.45, dur=0.3, bright=4800.0)
        place_bass(S, t + (0.0 if k in (4, 6, 8, 10) else BEAT / 2), ch, BEAT * 0.9 if k in (4, 6, 8, 10) else BEAT * 0.4, 0.8)
        place_hat(S, rng, t + BEAT / 2, 0.22, pan=0.3 if k % 2 else -0.3)
    place_arp(S, g1(4), "F", 0.55)
    place_arp(S, g1(8), "C", 0.55)

    # ---- 10.10-11.46 pre-drop: the second message starts the build
    place_pad(S, g1(12), "G", T_PUB - 0.12 - g1(12), 0.8, rel=0.08)
    place_kick(S, rng, g1(12), 0.8)
    place_bass(S, g1(12), "G", BEAT * 0.9, 0.85)
    S.put("fx", sy.noise_riser(rng, T_PUB - 0.11 - 10.379, f0=500, f1=10000, q=1.5, power=1.8), 10.379, 0.55)
    S.put("fx", sy.tone_riser(392.0, 1568.0, T_PUB - 0.11 - 10.379, vel=1.0, fc1=8000.0), 10.379, 0.5, hall=0.2)
    S.put("low", sy.sub_riser(45.0, 140.0, T_PUB - 0.11 - 10.379, power=1.4), 10.379, 0.8)
    place_kick(S, rng, g1(13), 0.55)
    place_kick(S, rng, g1(14), 0.7)
    place_roll(S, rng, T_PUB - 0.11, 8, 0.1364, 0.25, 0.95)
    reverse_crash(S, rng, T_PUB - 0.11, 0.9, 0.9)

    # ---- 11.459 "Published": the biggest hit, then the full chorus (C major)
    hit(S, rng, T_PUB, "C", size=1.25, crash_dur=3.0)
    sparkle(S, T_PUB + 0.03, "C", 1.0, n=9, step=0.05)
    S.put("fx", sy.air_tail(rng, dur=2.2, f0=12000.0, f1=500.0, tau=0.9), T_PUB + 0.02, 0.2, hall=0.5)

    prog = {0: "C", 4: "G", 8: "Am", 12: "F", 16: "C", 20: "G"}
    for k0, ch in prog.items():
        place_pad(S, g2(k0), ch, (2 if k0 == 20 else 4) * BEAT, 1.0 if k0 < 16 else 0.8)
    place_pad(S, g2(22), "C", 1.6, 0.9, rel=0.8)               # the last chord resolves to C

    for k in range(0, 24):
        t = g2(k)
        bar = (k // 4) * 4
        ch = prog[bar]
        full = k < 16                 # chorus through the outro hit; stripped afterwards
        if k in (0, 5, 8, 13, 22):
            pass                      # the hit brings its own kick
        elif k == 21:
            place_kick(S, rng, t, 0.7)
        elif full or k % 2 == 0:
            place_kick(S, rng, t, 0.88 if full else 0.7)
        if full and k % 4 in (1, 3):
            place_clap(S, rng, t, 0.8)
        if full:
            place_hat(S, rng, t + BEAT / 2, 0.6, open_=True, pan=0.25)
            for off, v in ((0.0, 0.34), (0.25, 0.16), (0.75, 0.2)):
                place_hat(S, rng, t + off * BEAT, v, pan=-0.2 if off else 0.1)
        if k != 22:
            place_bass(S, t + BEAT / 2, ch, BEAT * 0.42, 0.9 if full else 0.7)
        if k % 4 == 0 and k > 0 and full:
            place_arp(S, t, ch, 0.9)
        if k % 4 == 2 and full:
            place_bell(S, t, CH[ch]["arp"][2] + 12, 0.35, dur=1.0, hall=0.7, pan=0.3)
    place_arp(S, g2(0), "C", 0.9, start=2)
    for k in range(0, 12):                                      # syncopated stabs: the "and" of 2 and of 4
        if k % 4 in (1, 3):
            place_stab(S, g2(k) + BEAT / 2, prog[(k // 4) * 4], 0.5, dur=0.14, bright=5200.0)
    motif = {"C": [(0, 88), (3, 91), (4, 96), (6, 91), (7, 88)], "G": [(0, 86), (3, 91), (4, 95), (6, 91), (7, 86)]}
    for bar, ch in ((0, "C"), (4, "G")):
        for e, m in motif[ch]:
            S.put("bell", sy.bell(float(sy.mtof(m)), dur=0.9, tau=0.4), g2(bar) + e * BEAT / 2, 0.4, pan=0.35 if e % 2 else -0.35, hall=0.5, dly=0.4)

    # highlight hits (14.187 and 15.823), fills, the outro hit (18.552)
    hit(S, rng, g2(5), "G", size=0.5, crash_dur=1.6)
    hit(S, rng, g2(8), "Am", size=0.5, crash_dur=1.6)
    place_roll(S, rng, g2(8), 4, BEAT / 4, 0.3, 0.8)
    place_roll(S, rng, g2(12), 4, BEAT / 4, 0.3, 0.85)
    reverse_crash(S, rng, g2(13), 0.5, 0.5)
    S.put("fx", sy.whoosh(rng, 0.3, f0=4500, f1=400, vel=1.0), 18.3, 0.5)
    hit(S, rng, g2(13), "F", size=1.0, crash_dur=2.4)
    S.put("fx", sy.whoosh(rng, 0.4, f0=400, f1=6000, vel=1.0), g2(14) - 0.15, 0.45)
    place_bell(S, g2(14), 81, 0.55, dur=1.4)                      # "Publish when you say so" arrives
    place_bell(S, g2(16), 84, 0.55, dur=1.8)                      # credit
    S.put("fx", sy.crash(rng, dur=1.6), g2(16), 0.2, hall=0.4)

    # ---- closing line: pad swell and a low riser under the voice, then a last full stop
    S.put("low", sy.sub_riser(40.0, 98.0, 23.40 - 21.0, power=1.3), 21.0, 0.6)
    S.put("fx", sy.tone_riser(130.8, 523.3, 23.40 - 21.0, vel=1.0, fc0=300, fc1=2800), 21.0, 0.5, hall=0.2)
    S.put("fx", sy.noise_riser(rng, 23.40 - 21.0, f0=150, f1=5200, q=1.3, power=2.4), 21.0, 0.3)
    place_kick(S, rng, g2(20), 0.55)
    place_kick(S, rng, g2(21), 0.62)
    S.put("fx", sy.whoosh(rng, 0.3, f0=3500, f1=300, vel=1.0), 20.95, 0.4)
    reverse_crash(S, rng, g2(22), 0.6, 0.6)
    hit(S, rng, g2(22), "C", size=1.15, crash_dur=3.0)
    sparkle(S, g2(22) + 0.02, "C", 0.8, n=7, step=0.06)


# ---------------------------------------------------------------------------- interface sounds
def ui_sounds(S, rng):
    U = lambda sig, t, g=1.0, pan=0.0, hall=0.0: S.put("ui", sig, t, g, pan, hall=hall)
    U(sy.whoosh(rng, 0.38, 300, 4200, shape=1.6), 5.2, 0.5)                       # window opens
    U(sy.pop(520, 980), 5.735, 0.55, 0.15)                                         # message 1 sent
    U(sy.tick(2600), 5.735, 0.2)
    U(sy.whoosh(rng, 0.3, 3800, 600, shape=1.3), 6.275, 0.55)                       # draft card slides in
    for i in range(9):                                                             # title words typed in
        U(sy.tick(2300 + 160 * (i % 3), vel=1.0), 6.5 + i * 0.067, 0.085, pan=0.3 if i % 2 else -0.3)
    U(sy.pluck(float(sy.mtof(76)), 0.3, bright=3500.0), 7.349, 0.25, -0.2)         # description line
    U(sy.tick(1900), 7.349, 0.2)
    U(sy.pluck(float(sy.mtof(79)), 0.3, bright=3500.0), 7.79, 0.25, 0.2)           # tags line
    U(sy.tick(2100), 7.79, 0.2)
    U(sy.bell(float(sy.mtof(88)), dur=0.7, tau=0.35, ratio=3.5), 8.22, 0.34, -0.1, hall=0.4)   # validate ok
    U(sy.tick(3200), 8.22, 0.18)
    U(sy.bell(float(sy.mtof(91)), dur=0.9, tau=0.4), 8.731, 0.36, 0.1, hall=0.5)   # upload ok
    U(sy.bell(float(sy.mtof(96)), dur=1.1, tau=0.5), 8.731 + 0.07, 0.34, 0.1, hall=0.5)
    U(sy.whoosh(rng, 0.22, 600, 5200, shape=1.6), 8.731 - 0.08, 0.35)
    U(sy.pop(480, 900), 10.379, 0.6, 0.15)                                         # message 2 sent
    U(sy.tick(2600), 10.379, 0.2)
    U(sy.whoosh(rng, 0.3, 3800, 500, shape=1.3), 13.4, 0.5)                       # window leaves
    for t in (14.2, 15.82):                                                        # highlight cards
        U(sy.pop(700, 1250, dur=0.12), t, 0.4, -0.1)
        U(sy.whoosh(rng, 0.42, 500, 5200, shape=1.8), t, 0.5)
    U(sy.whoosh(rng, 0.25, 4000, 500, shape=1.3), 18.3, 0.4)


# ---------------------------------------------------------------------------- mixing
def speech_gate(vo, thr_db=-32.0, merge=0.25):
    h = int(0.01 * SR)
    n = len(vo) // h
    rms = 10 * np.log10((vo[: n * h].reshape(n, h) ** 2).mean(axis=1) + 1e-12)
    act = rms > thr_db
    iv, i = [], 0
    while i < n:
        if act[i]:
            j = i
            while j < n and act[j]:
                j += 1
            iv.append([i * 0.01, j * 0.01])
            i = j
        else:
            i += 1
    out = []
    for a, b in iv:
        if out and a - out[-1][1] < merge:
            out[-1][1] = b
        else:
            out.append([a, b])
    return out


def smooth_gate(intervals, lead=0.06, hold=0.05, att=0.05, rel=0.26, rate=1000):
    n = int((DUR + 1.5) * rate)
    g = np.zeros(n)
    for a, b in intervals:
        g[max(0, int((a - lead) * rate)): int((b + hold) * rate)] = 1.0
    out = np.empty(n)
    ca, cr = 1 - np.exp(-1 / (att * rate)), 1 - np.exp(-1 / (rel * rate))
    y = 0.0
    for i in range(n):
        c = ca if g[i] > y else cr
        y += (g[i] - y) * c
        out[i] = y
    return np.interp(np.arange(N) / SR, np.arange(n) / rate, out)


def protect_curve(items, tau=0.05):
    p = np.zeros(N)
    for t, d in items:
        i0, i1 = int(max(0, t - 0.004) * SR), int((t + d) * SR)
        if i0 >= N:
            continue
        p[i0:i1] = 1.0
        m = min(int(0.4 * SR), N - i1)
        if m > 0:
            p[i1:i1 + m] = np.maximum(p[i1:i1 + m], np.exp(-np.arange(m) / SR / tau))
    return p


def vacuum_curve(windows, fade=0.006):
    g = np.ones(N)
    for a, c in windows:
        i0, i1, f = int(a * SR), int(c * SR), int(fade * SR)
        ramp = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, f))
        g[i0 - f:i0] = np.minimum(g[i0 - f:i0], ramp)
        g[i0:i1] = 0.0
        g[i1:i1 + f] = np.minimum(g[i1:i1 + f], 1 - ramp)
    return g


def pump_curve(kicks, depth=0.62, tau=0.12, atk=0.003):
    g = np.ones(N)
    for t, v in kicks:
        i = int(t * SR)
        m = min(int(0.7 * SR), N - i)
        if m <= 0:
            continue
        tt = np.arange(m) / SR
        dip = depth * min(1.0, 0.4 + 0.6 * v) * np.exp(-tt / tau) * np.minimum(1.0, tt / atk)
        g[i:i + m] = np.minimum(g[i:i + m], 1 - dip)
    return g


def db(x):
    return 10 ** (x / 20)


def margin_db(c, shift=0.0):
    """How far under the speech level (dB) the music must stay in the band around c Hz."""
    if c < 250:
        m = 4.0
    elif c < 500:
        m = 10.0
    elif c < 4000:
        m = 14.0
    elif c < 8000:
        m = 6.0
    else:
        m = -8.0
    return m + shift


def mix(S, vo, args):
    """Bus processing: reverbs, kick pump, voice-aware ducking. Returns unscaled music and ui buses."""
    ir_hall = sy.make_ir(2.6, np.random.default_rng(11), predelay=0.02)
    ir_room = sy.make_ir(0.55, np.random.default_rng(12), predelay=0.006, hf_decay=0.35)
    wet_hall = sy.reverb(S.hall, ir_hall)
    wet_room = sy.reverb(S.room, ir_room)
    wet_dly = sy.pingpong(S.dly, BEAT * 0.75)
    wet_dly_hall = sy.reverb(wet_dly, ir_hall) * 0.6

    pump = pump_curve(S.kicks)
    pump_soft = 1 - (1 - pump) * 0.55
    b = S.b
    dry = (b["kick"] + b["low"] + b["perc"] + b["fx"] + b["bell"]
           + b["bass"] * pump + b["pad"] * pump + b["arp"] * pump_soft)
    music = dry + wet_hall * 0.9 + wet_room * 0.9 + wet_dly * 0.7 + wet_dly_hall

    # tone: no rumble below the kick, a little less sub, a little less fizz
    music = sy.hp(music, 30.0)
    music = sy.shelf(music, 110.0, args.low_shelf, "low")
    music = sy.shelf(music, 7000.0, args.high_shelf, "high")

    # voice-aware ducking: a gentle gate-driven duck per band, then a spectral ceiling under the speech level
    iv = speech_gate(vo)
    gate = smooth_gate(iv)
    prot = protect_curve(S.protect)
    low = sy.lp0(music, 200.0)
    high = sy.hp0(music, 5500.0)
    mid = music - low - high

    def band_gain(depth_db):
        return 1 - (1 - db(depth_db)) * gate * (1 - prot)

    music = low * band_gain(args.duck_low) + mid * band_gain(args.duck_mid) + high * band_gain(args.duck_high)
    music = sy.unmask(music, vo, gate, lambda c: margin_db(c, args.margin_shift), protect=prot)
    music = music * vacuum_curve(VACUUM)[None, :]

    ui = b["ui"] + sy.reverb(S.uihall, ir_hall) * 0.8
    ui = ui * (1 - (1 - db(args.duck_ui)) * gate * 0.8)
    return music, ui, iv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--stems", default=None, help="directory for debugging stems")
    ap.add_argument("--bus-stems", action="store_true", help="also dump each dry bus (needs --stems)")
    ap.add_argument("--duck-low", type=float, default=-5.0)
    ap.add_argument("--duck-mid", type=float, default=-3.0)
    ap.add_argument("--duck-high", type=float, default=-3.0)
    ap.add_argument("--low-shelf", type=float, default=-3.0)
    ap.add_argument("--high-shelf", type=float, default=-3.0)
    ap.add_argument("--margin-shift", type=float, default=0.0)
    ap.add_argument("--duck-ui", type=float, default=-2.0)
    ap.add_argument("--music-db", type=float, default=None, help="fix the music level instead of solving for the loudness target")
    ap.add_argument("--ui-db", type=float, default=-8.0)
    ap.add_argument("--clip", type=float, default=0.9, help="soft-clip threshold on the music bus")
    ap.add_argument("--lufs", type=float, default=-13.5)
    ap.add_argument("--ceiling", type=float, default=-1.8)
    args = ap.parse_args()

    sr, vo = wavfile.read(args.vo)
    assert sr == SR
    vo = vo.astype(float) / 32768.0
    vo = np.concatenate([vo, np.zeros(N - len(vo))])[:N]

    rng = np.random.default_rng(2026)
    S = Score()
    arrange(S, rng)
    ui_sounds(S, rng)
    music, ui, iv = mix(S, vo, args)
    print("speech regions:", [(round(a, 2), round(b, 2)) for a, b in iv])

    n_out = int(DUR * SR)
    vo2 = np.stack([vo, vo])[:, :n_out] * 0.7071            # centred, -3 dB per side: same loudness as the mono track
    music, ui = music[:, :n_out], ui[:, :n_out] * db(args.ui_db)
    fade = np.ones(n_out)
    fade_n = int(0.5 * SR)
    fade[-fade_n:] = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, fade_n))

    def render(m_db):
        m = sy.softclip(music * db(m_db), args.clip)
        return (vo2 + (m + ui) * fade[None, :])

    def finish(m_db, ceiling):
        return sy.limit(render(m_db), ceiling)

    ceiling = args.ceiling
    if args.music_db is not None:
        m_db = args.music_db
    else:
        lo, hi = -40.0, 10.0
        for _ in range(22):
            m_db = 0.5 * (lo + hi)
            y, _g = finish(m_db, ceiling)
            lo, hi = (m_db, hi) if sy.lufs_integrated(y) < args.lufs else (lo, m_db)
        m_db = 0.5 * (lo + hi)
    for it in range(6):
        y, gain = finish(m_db, ceiling)
        tp = sy.true_peak_db(y)
        print(f"music {m_db:+.2f} dB  LUFS {sy.lufs_integrated(y):.2f}  TP {tp:.2f}  max GR {20*np.log10(gain.min()):.2f} dB")
        if tp <= args.ceiling + 0.05:
            break
        ceiling -= (tp - args.ceiling) + 0.02
    print(f"voice alone: {sy.lufs_integrated(vo2):.2f} LUFS")
    gr = -20 * np.log10(gain)
    ev, i = [], 0
    while i < len(gr):
        if gr[i] > 1.5:
            j = i
            while j < len(gr) and gr[j] > 0.5:
                j += 1
            ev.append((i / SR, gr[i:j].max()))
            i = j
        else:
            i += 1
    print("limiter reduction > 1.5 dB at:", ", ".join(f"{t:.2f}s ({g:.1f} dB)" for t, g in ev))
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    wavfile.write(args.out, SR, (np.clip(y.T, -1, 1) * 32767).astype(np.int16))
    print("wrote", args.out)
    if args.stems:
        os.makedirs(args.stems, exist_ok=True)
        def w(name, x):
            wavfile.write(os.path.join(args.stems, name), SR, (np.clip(x.T, -1, 1) * 32767).astype(np.int16))
        w("music.wav", sy.softclip(music * db(m_db), args.clip) * fade[None, :] * gain[None, :])
        w("ui.wav", ui * fade[None, :] * gain[None, :])
        w("vo.wav", vo2 * gain[None, :])
        if args.bus_stems:
            for name, x in S.b.items():
                w(f"bus_{name}.wav", x[:, :n_out] * db(m_db) * gain[None, :])


if __name__ == "__main__":
    main()
