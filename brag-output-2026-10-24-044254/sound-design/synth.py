"""Synthesis and mixing toolkit for the yt-autopilot brag video score (numpy and scipy only).

Instruments return plain arrays at 48 kHz; build_score.py places them on the timeline.
Sections: basics, filters, oscillators, reverb and delay, loudness and limiting,
percussion, tonal instruments, risers and interface sounds, shelving EQ, voice-aware ducking.
"""
import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d
from scipy.signal import butter, fftconvolve, istft, lfilter, resample_poly, sosfilt, sosfiltfilt, stft

SR = 48000


# ----------------------------------------------------------------- basics
def mtof(m):
    return 440.0 * 2.0 ** ((np.asarray(m, dtype=float) - 69.0) / 12.0)


def unit(x, peak=1.0):
    return x / (np.abs(x).max() + 1e-12) * peak


def tarr(n):
    return np.arange(n) / SR


def noise(n, rng):
    return rng.standard_normal(n)


def edge(x, fi=0.001, fo=0.005):
    """Raised-cosine fades so no event starts or stops with a click."""
    x = np.array(x, dtype=float, copy=True)
    n = x.shape[-1]
    a, b = min(int(fi * SR), n), min(int(fo * SR), n)
    if a > 1:
        x[..., :a] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
    if b > 1:
        x[..., n - b:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
    return x


def sat(x, drive):
    """Symmetric tanh saturation, normalised so small signals keep their level."""
    return np.tanh(drive * x) / np.tanh(drive)


def softclip(x, thr=1.0):
    """Unity-slope soft clipper: leaves small signals alone, rounds peaks above ~thr."""
    return thr * np.tanh(x / thr)


def pan_gains(p):
    a = (np.clip(p, -1, 1) + 1) * np.pi / 4
    return np.cos(a), np.sin(a)


def stereo(x, p=0.0):
    gl, gr = pan_gains(p)
    return np.stack([x * gl, x * gr])


# ----------------------------------------------------------------- filters
def _clip_fc(fc):
    return np.clip(fc, 15.0, SR * 0.45)


def lp(x, fc, order=2):
    return sosfilt(butter(order, _clip_fc(fc) / (SR / 2), "lowpass", output="sos"), x, axis=-1)


def hp(x, fc, order=2):
    return sosfilt(butter(order, _clip_fc(fc) / (SR / 2), "highpass", output="sos"), x, axis=-1)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [_clip_fc(lo) / (SR / 2), _clip_fc(hi) / (SR / 2)], "bandpass", output="sos"), x, axis=-1)


def lp0(x, fc, order=4):
    """Zero-phase low-pass (used for band splitting so the bands add back exactly)."""
    return sosfiltfilt(butter(order, _clip_fc(fc) / (SR / 2), "lowpass", output="sos"), x, axis=-1)


def hp0(x, fc, order=4):
    return sosfiltfilt(butter(order, _clip_fc(fc) / (SR / 2), "highpass", output="sos"), x, axis=-1)


def _rbj(kind, fc, q):
    w0 = 2 * np.pi * float(_clip_fc(fc)) / SR
    al = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    if kind == "lp":
        b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    elif kind == "hp":
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    else:  # bp, constant 0 dB peak
        b = [al, 0.0, -al]
    a0 = 1 + al
    return np.array([b[0] / a0, b[1] / a0, b[2] / a0, 1.0, -2 * c / a0, (1 - al) / a0])


def sweep(x, fc_curve, q=0.8, kind="lp", block=32):
    """Filter whose cut-off follows fc_curve (Hz per sample); state carries across blocks."""
    y = np.empty_like(x)
    zi = np.zeros((1, 2))
    for s in range(0, len(x), block):
        e = min(s + block, len(x))
        y[s:e], zi = sosfilt(_rbj(kind, fc_curve[s:e].mean(), q)[None, :], x[s:e], zi=zi)
    return y


def expcurve(n, f0, f1):
    """Exponential glide from f0 to f1 over n samples."""
    return f0 * (f1 / f0) ** (np.arange(n) / max(n - 1, 1))


# ----------------------------------------------------------------- oscillators
def saw(freq, n, phase0=0.0):
    """Band-limited (PolyBLEP) sawtooth; freq may be a scalar or a per-sample array."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    dt = f / SR
    ph = (phase0 + np.cumsum(dt)) % 1.0
    y = 2.0 * ph - 1.0
    m = ph < dt
    x = ph[m] / dt[m]
    y[m] -= x + x - x * x - 1.0
    m = ph > 1.0 - dt
    x = (ph[m] - 1.0) / dt[m]
    y[m] -= x * x + x + x + 1.0
    return y


def pulse(freq, n, width=0.5, phase0=0.0):
    return saw(freq, n, phase0) - saw(freq, n, (phase0 + width) % 1.0)


# ----------------------------------------------------------------- reverb / delay
def make_ir(rt60, rng, predelay=0.012, hp_hz=180.0, lp_hz=9000.0, hf_decay=0.45):
    """Stereo noise-tail impulse response; highs decay faster than lows."""
    n = int((rt60 * 1.1 + predelay) * SR)
    t = tarr(n)
    out = np.zeros((2, n))
    for ch in range(2):
        w = rng.standard_normal(n)
        lo = lp(w, 450.0) * np.exp(-6.91 * t / (rt60 * 1.15))
        mid = bp(w, 450.0, 3000.0) * np.exp(-6.91 * t / rt60)
        hi = hp(w, 3000.0) * np.exp(-6.91 * t / (rt60 * hf_decay))
        out[ch] = lo + mid + hi
    out = hp(lp(out, lp_hz), hp_hz)
    d = int(predelay * SR)
    out = np.concatenate([np.zeros((2, d)), out[:, : n - d]], axis=1)
    out *= np.minimum(1.0, tarr(n) / 0.006)  # soft onset
    out /= np.sqrt((out ** 2).sum(axis=1, keepdims=True)) + 1e-12
    return out


def reverb(send, ir):
    """send: (2, n). Sums to mono and convolves with the left/right impulse responses: a wide, decorrelated return."""
    n = send.shape[1]
    m = send.mean(axis=0)
    return np.stack([fftconvolve(m, ir[0])[:n], fftconvolve(m, ir[1])[:n]])


def pingpong(x, delay_s, fb=0.38, taps=5, hp_hz=300.0, lp_hz=5200.0):
    """x: (2, n). Alternating-side delay with a darker repeat each time."""
    n = x.shape[1]
    d = int(delay_s * SR)
    out = np.zeros_like(x)
    src = lp(hp(x.mean(axis=0), hp_hz, 1), lp_hz, 1)
    for k in range(1, taps + 1):
        s = k * d
        if s >= n:
            break
        g = fb ** (k - 1) * 0.9
        side = 0 if k % 2 else 1
        out[side, s:] += g * src[: n - s]
        out[1 - side, s:] += 0.25 * g * src[: n - s]
        src = lp(src, lp_hz * 0.8, 1)
    return out


# ----------------------------------------------------------------- loudness helpers
_K1 = (np.array([1.53512485958697, -2.69169618940638, 1.19839281085285]),
       np.array([1.0, -1.69065929318241, 0.73248077421585]))
_K2 = (np.array([1.0, -2.0, 1.0]), np.array([1.0, -1.99004745483398, 0.99007225036621]))


def kweight(x):
    return lfilter(_K2[0], _K2[1], lfilter(_K1[0], _K1[1], x, axis=-1), axis=-1)


def lufs_blocks(x, win=0.4, hop=0.1):
    """Per-block (400 ms, 75 % overlap) K-weighted loudness for a (ch, n) or (n,) array."""
    x = np.atleast_2d(x)
    k = kweight(x)
    w, h = int(win * SR), int(hop * SR)
    nb = max(0, (k.shape[1] - w) // h + 1)
    ms = np.zeros(nb)
    cs = np.cumsum(np.concatenate([np.zeros((k.shape[0], 1)), (k ** 2)], axis=1), axis=1)
    for i in range(nb):
        s = i * h
        ms[i] = ((cs[:, s + w] - cs[:, s]) / w).sum()
    return -0.691 + 10 * np.log10(ms + 1e-12)


def lufs_integrated(x):
    b = lufs_blocks(x)
    if len(b) == 0:
        return -70.0
    g = b[b > -70.0]
    if len(g) == 0:
        return -70.0
    rel = 10 * np.log10(np.mean(10 ** (g / 10))) - 10.0
    g2 = g[g > rel]
    return float(-0.691 + 10 * np.log10(np.mean(10 ** ((g2 + 0.691) / 10)))) if len(g2) else -70.0


def true_peak_db(x):
    x = np.atleast_2d(x)
    os = resample_poly(x, 4, 1, axis=1)
    return 20 * np.log10(np.abs(os).max() + 1e-12)


def limit(x, ceiling_db=-1.5, lookahead=0.002, release=0.09):
    """Look-ahead peak limiter run on a 4x oversampled detector; gain applied at the original rate."""
    x = np.atleast_2d(x)
    c = 10 ** (ceiling_db / 20)
    os = resample_poly(x, 4, 1, axis=1)
    pk = np.abs(os).max(axis=0)
    blk = 48  # 0.25 ms at 192 kHz
    nb = len(pk) // blk
    env = pk[: nb * blk].reshape(nb, blk).max(axis=1)
    r = np.minimum(1.0, c / (env + 1e-12))
    W = max(2, int(lookahead * 4000))
    m = minimum_filter1d(r, size=2 * W - 1, mode="nearest")
    g = np.empty_like(m)
    a = 1 - np.exp(-1.0 / (release * 4000))
    prev = 1.0
    for i in range(nb):
        prev = min(m[i], prev + (1 - prev) * a)
        g[i] = prev
    g = uniform_filter1d(g, size=W, origin=(W - 1) // 2, mode="nearest")
    t_ctrl = (np.arange(nb) + 0.5) * blk / (SR * 4)
    t_aud = np.arange(x.shape[1]) / SR
    gain = np.interp(t_aud, t_ctrl, g)
    return x * gain, gain


# ----------------------------------------------------------------- percussion
def kick(rng, vel=1.0, f_end=47.0, f_start=170.0, tau_p=0.021, tau_a=0.18, dur=0.55, drive=1.9, click=0.30):
    n = int(dur * SR)
    t = tarr(n)
    f = f_end + (f_start - f_end) * np.exp(-t / tau_p)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau_a) * np.minimum(1.0, t / 0.0007)
    c = hp(noise(n, rng), 2200) * np.exp(-t / 0.0022) * click
    return edge(sat(body * 1.15 + c, drive), 0.0, 0.03) * vel


def sub_boom(rng, root=55.0, dur=2.8, tau_a=0.95, drop=3.0, tau_p=0.075, drive=1.7):
    """Cinematic sub hit: fast pitch drop onto the root, long decay, saturated so it reads on phones."""
    n = int(dur * SR)
    t = tarr(n)
    f = root + (root * drop - root) * np.exp(-t / tau_p)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / tau_a) * np.minimum(1.0, t / 0.0015)
    thump = np.sin(2 * np.pi * np.cumsum(root * 2 + root * 2.2 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.22)
    return edge(sat(body * 1.2 + 0.45 * thump, drive), 0.0, 0.25)


def crack(rng, dur=0.18, lo=900.0, hi=9000.0, tau=0.03):
    n = int(dur * SR)
    t = tarr(n)
    return unit(edge(bp(noise(n, rng), lo, hi) * np.exp(-t / tau) * np.minimum(1.0, t / 0.0004), 0.0, 0.02))


def air_tail(rng, dur=1.6, f0=9000.0, f1=350.0, tau=0.5, q=0.9):
    """Noise that exhales: low-pass sweeping down while it fades."""
    n = int(dur * SR)
    t = tarr(n)
    w = noise(n, rng)
    y = sweep(w, expcurve(n, f0, f1), q, "lp") * np.exp(-t / tau)
    return unit(edge(y, 0.002, 0.2))


def crash(rng, dur=2.4, n_partials=90, tau=0.55, bright=1.0):
    """Additive cymbal: inharmonic partials 2.5-15 kHz plus a little filtered noise."""
    n = int(dur * SR)
    t = tarr(n)
    y = np.zeros(n)
    fr = rng.uniform(2500, 15000, n_partials)
    am = rng.uniform(0.3, 1.0, n_partials) * (fr / 8000.0) ** (-0.3)
    ta = rng.uniform(0.25, 1.15, n_partials) * tau
    ph = rng.uniform(0, 2 * np.pi, n_partials)
    for f, a, d, p in zip(fr, am, ta, ph):
        y += a * np.sin(2 * np.pi * f * t + p) * np.exp(-t / d)
    y /= np.sqrt(n_partials) * 0.5
    nz = hp(noise(n, rng), 5200) * np.exp(-t / (tau * 0.9)) * 0.7
    out = (y + nz) * np.minimum(1.0, t / 0.0006)
    return unit(edge(lp(out, 15500 * bright + 1000), 0.0, 0.3))


def clap(rng, vel=1.0, tail=0.16):
    n = int((tail + 0.06) * SR)
    t = tarr(n)
    y = np.zeros(n)
    for off, a in [(0.0, 0.7), (0.009, 0.8), (0.018, 0.9), (0.029, 1.0)]:
        i = int(off * SR)
        m = n - i
        y[i:] += a * noise(m, rng) * np.exp(-tarr(m) / 0.004)
    i = int(0.029 * SR)
    y[i:] += 0.55 * noise(n - i, rng) * np.exp(-tarr(n - i) / (tail / 3.0))
    y = bp(y, 900, 3800, 2)
    return edge(sat(y * 1.3, 1.4), 0.0, 0.03) * vel


def snare(rng, vel=1.0, tone=190.0, tau_n=0.10, tau_t=0.07, dur=0.3):
    n = int(dur * SR)
    t = tarr(n)
    body = np.sin(2 * np.pi * np.cumsum(tone * 0.82 + tone * 0.35 * np.exp(-t / 0.012)) / SR) * np.exp(-t / tau_t)
    nz = bp(noise(n, rng), 1600, 9500) * np.exp(-t / tau_n) * 1.6
    return edge(sat(0.7 * body + nz, 1.5), 0.0, 0.05) * vel


def tom(rng, f=110.0, vel=1.0, dur=0.5, tau=0.16):
    n = int(dur * SR)
    t = tarr(n)
    fr = f + f * 0.9 * np.exp(-t / 0.03)
    y = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t / tau) + 0.2 * hp(noise(n, rng), 2500) * np.exp(-t / 0.01)
    return edge(sat(y, 1.5), 0.0, 0.05) * vel


def hat(rng, vel=1.0, open_=False):
    dur = 0.34 if open_ else 0.07
    tau = 0.085 if open_ else 0.016
    n = int(dur * SR)
    t = tarr(n)
    w = hp(noise(n, rng), 7000, 3)
    # a few fixed inharmonic partials give it a metal ring
    for f, a in [(6430, 0.30), (8920, 0.25), (11200, 0.2)]:
        w += a * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
    return unit(edge(w * np.exp(-t / tau) * np.minimum(1, t / 0.0005), 0.0, 0.01)) * vel


# ----------------------------------------------------------------- tonal
def bass_note(f, dur, vel=1.0, drive=1.8, cutoff0=2600.0, cutoff1=320.0):
    """Saw + sub with a plucky filter. Returns mono."""
    n = int((dur + 0.04) * SR)
    t = tarr(n)
    s = 0.5 * (saw(f * 1.004, n) + saw(f * 0.996, n, 0.3))
    fc = cutoff1 + (cutoff0 - cutoff1) * np.exp(-t / 0.075)
    s = sweep(s, fc, 1.2, "lp")
    sub = np.sin(2 * np.pi * f * t)
    y = sat(0.75 * s + 0.95 * sub, drive)
    a = np.minimum(1.0, t / 0.004)
    rel = np.clip((dur + 0.04 - t) / 0.04, 0, 1)
    return y * a * rel * vel


def supersaw(f, dur, voices=7, detune=0.18, rel=0.3, atk=0.02, fc0=5000.0, fc1=1200.0, tau_f=0.25, vel=1.0, spread=0.85):
    """Stereo detuned-saw chord tone; low-pass sweeps from fc0 to fc1."""
    n = int((dur + rel) * SR)
    t = tarr(n)
    out = np.zeros((2, n))
    offs = np.linspace(-1, 1, voices)
    rng = np.random.default_rng(int(f * 10) % 2 ** 31)
    for k, o in enumerate(offs):
        fv = f * 2 ** (o * detune / 12.0)
        s = saw(fv, n, rng.uniform())
        gl, gr = pan_gains(o * spread)
        out[0] += s * gl
        out[1] += s * gr
    out /= np.sqrt(voices)
    fc = fc1 + (fc0 - fc1) * np.exp(-t / tau_f)
    out = np.stack([sweep(out[0], fc, 0.8, "lp"), sweep(out[1], fc, 0.8, "lp")])
    env = np.minimum(1.0, t / max(atk, 1e-4)) * np.clip((dur + rel - t) / rel, 0, 1)
    return out * env * vel


def pad_tone(f, dur, vel=1.0, atk=0.18, rel=0.5, fc=1700.0, sub=0.5):
    """Warm slow pad voice: 3 detuned saws + a sine an octave down, panned apart."""
    n = int((dur + rel) * SR)
    t = tarr(n)
    L = saw(f * 2 ** (-0.09 / 12), n, 0.1) + 0.6 * saw(f * 2 ** (0.05 / 12), n, 0.5)
    R = saw(f * 2 ** (0.09 / 12), n, 0.7) + 0.6 * saw(f * 2 ** (-0.05 / 12), n, 0.2)
    low = sub * np.sin(2 * np.pi * (f / 2) * t)
    out = np.stack([lp(L, fc) + low, lp(R, fc) + low]) * 0.35
    env = np.minimum(1.0, (t / atk) ** 1.5) * np.clip((dur + rel - t) / rel, 0, 1)
    return out * env * vel


def pluck(f, dur=0.45, vel=1.0, bright=4800.0, tau=0.2):
    n = int(dur * SR)
    t = tarr(n)
    s = 0.6 * saw(f * 1.003, n) + 0.6 * saw(f * 0.997, n, 0.4) + 0.3 * pulse(f, n, 0.3)
    fc = 500 + bright * np.exp(-t / 0.07)
    s = sweep(s, fc, 1.5, "lp")
    return edge(s * np.exp(-t / tau) * np.minimum(1.0, t / 0.002) * 0.7, 0.0, 0.04) * vel


def bell(f, dur=1.8, vel=1.0, ratio=3.5, index=2.2, tau=0.9, shimmer=0.3):
    """FM bell: inharmonic modulator whose depth decays, plus a quiet octave partial."""
    n = int(dur * SR)
    t = tarr(n)
    idx = index * np.exp(-t / 0.35)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * ratio * t))
    y += shimmer * np.sin(2 * np.pi * f * 2.0 * t + 0.6 * idx * np.sin(2 * np.pi * f * 2.76 * t)) * np.exp(-t / (tau * 0.5))
    return edge(y * np.exp(-t / tau) * np.minimum(1.0, t / 0.0008) * 0.55, 0.0, 0.2) * vel


def noise_riser(rng, dur, f0=350.0, f1=9500.0, q=1.8, power=2.0, wide=True):
    n = int(dur * SR)
    t = tarr(n) / dur
    chans = []
    for ch in range(2 if wide else 1):
        chans.append(sweep(noise(n, rng), expcurve(n, f0, f1), q, "bp") * 3.0)
    y = np.stack(chans) if wide else np.stack([chans[0], chans[0]])
    return unit(y * (t ** power))


def sub_riser(f0, f1, dur, power=1.5, drive=1.4):
    """Sine gliding up in the sub range while it swells: tension the voice has no energy in."""
    n = int(dur * SR)
    t = np.arange(n) / n
    y = np.sin(2 * np.pi * np.cumsum(expcurve(n, f0, f1)) / SR)
    return edge(sat(y * 1.2, drive) * t ** power, 0.02, 0.003)


def tone_riser(f_start, f_end, dur, vel=1.0, voices=5, fc0=500.0, fc1=7000.0):
    """Detuned saws gliding up while the filter opens."""
    n = int(dur * SR)
    t = tarr(n) / dur
    fg = expcurve(n, f_start, f_end)
    out = np.zeros((2, n))
    for k, o in enumerate(np.linspace(-1, 1, voices)):
        s = saw(fg * 2 ** (o * 0.14 / 12), n, 0.13 * k)
        gl, gr = pan_gains(o * 0.8)
        out[0] += s * gl
        out[1] += s * gr
    out /= np.sqrt(voices)
    fc = expcurve(n, fc0, fc1)
    out = np.stack([sweep(out[0], fc, 1.0, "lp"), sweep(out[1], fc, 1.0, "lp")])
    return unit(out * (t ** 1.6)) * vel


def whoosh(rng, dur=0.28, f0=500.0, f1=5000.0, vel=1.0, shape=2.0, q=1.2):
    """Single swish: band-passed noise sweeping up (or down) under a bell-shaped level."""
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    env = np.sin(np.pi * x ** (1 / shape)) ** 2
    L = sweep(noise(n, rng), expcurve(n, f0, f1), q, "bp") * 3
    R = sweep(noise(n, rng), expcurve(n, f0, f1), q, "bp") * 3
    return unit(np.stack([L, R]) * env) * vel


def pop(f0=520.0, f1=980.0, dur=0.13, vel=1.0):
    """Chat 'sent' bloop: quick upward chirp with a tiny click."""
    n = int(dur * SR)
    t = tarr(n)
    f = f0 + (f1 - f0) * (1 - np.exp(-t / 0.018))
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.045) * np.minimum(1.0, t / 0.001)
    y += 0.25 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR) * np.exp(-t / 0.02)
    return edge(y, 0.0, 0.02) * vel


def tick(f=2400.0, dur=0.05, vel=1.0):
    n = int(dur * SR)
    t = tarr(n)
    y = (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.01 * t)) * np.exp(-t / 0.011) * np.minimum(1.0, t / 0.0005)
    return edge(y, 0.0, 0.01) * vel


# ----------------------------------------------------------------- shelving EQ
def shelf(x, fc, gain_db, kind="low"):
    """RBJ shelving filter (slope 1). kind: 'low' or 'high'."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * fc / SR
    cw, sw = np.cos(w0), np.sin(w0)
    al = sw / 2 * np.sqrt(2.0)
    sq = 2 * np.sqrt(A) * al
    if kind == "low":
        b0 = A * ((A + 1) - (A - 1) * cw + sq)
        b1 = 2 * A * ((A - 1) - (A + 1) * cw)
        b2 = A * ((A + 1) - (A - 1) * cw - sq)
        a0 = (A + 1) + (A - 1) * cw + sq
        a1 = -2 * ((A - 1) + (A + 1) * cw)
        a2 = (A + 1) + (A - 1) * cw - sq
    else:
        b0 = A * ((A + 1) + (A - 1) * cw + sq)
        b1 = -2 * A * ((A - 1) + (A + 1) * cw)
        b2 = A * ((A + 1) + (A - 1) * cw - sq)
        a0 = (A + 1) - (A - 1) * cw + sq
        a1 = 2 * ((A - 1) - (A + 1) * cw)
        a2 = (A + 1) - (A - 1) * cw - sq
    sos = np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]])
    return sosfilt(sos, x, axis=-1)


# ----------------------------------------------------------------- voice-aware spectral ducking
def band_edges():
    return np.array([120, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150,
                     4000, 5000, 6300, 8000, 10000, 13000, 17000], dtype=float)


def _band_rms(X, f, ed):
    out = np.empty((len(ed) - 1, X.shape[1]))
    for b in range(len(ed) - 1):
        k = (f >= ed[b]) & (f < ed[b + 1])
        out[b] = np.sqrt((np.abs(X[k]) ** 2).mean(axis=0))
    return out


def unmask(music, voice, gate, margin_db, max_cut_db=30.0, release=0.12, protect=None, nper=2048, hop=512):
    """Keep `music` (2, n) under the speech level, band by band, while `gate` (n,) says the voice is talking.

    The ceiling in each band is the voice's long-term speech level there minus margin_db(center_hz); music
    above the ceiling is pulled down (at most max_cut_db), fast on the way in and slowly released.
    protect: optional (n,) curve in [0, 1] that lets big hits through.
    """
    kw = dict(nperseg=nper, noverlap=nper - hop)
    f, t, V = stft(voice, SR, **kw)
    Ms = [stft(music[c], SR, **kw)[2] for c in range(2)]
    ed = band_edges()
    cen = np.sqrt(ed[:-1] * ed[1:])
    vb = _band_rms(V, f, ed)
    tot = np.sqrt((np.abs(V) ** 2).mean(axis=0)) + 1e-12
    tot_db = 20 * np.log10(tot)
    sp = tot_db > np.percentile(tot_db, 90) - 25.0
    ceil_db = 20 * np.log10(np.sqrt((vb[:, sp] ** 2).mean(axis=1)) + 1e-12) - np.array([margin_db(c) for c in cen])
    mb = np.sqrt(0.5 * sum(_band_rms(Mc, f, ed) ** 2 for Mc in Ms)) + 1e-12
    need = np.clip(20 * np.log10(mb) - ceil_db[:, None], 0.0, max_cut_db)
    g_t = np.interp(t * SR, np.arange(len(gate)), gate)
    need = need * g_t[None, :]
    rel = np.exp(-(hop / SR) / release)
    cut = np.zeros_like(need)
    prev = np.zeros(need.shape[0])
    for j in range(need.shape[1]):
        prev = np.maximum(need[:, j], prev * rel)
        cut[:, j] = prev
    if protect is not None:
        cut = cut * (1.0 - np.interp(t * SR, np.arange(len(protect)), protect))[None, :]
    lf = np.log(np.maximum(f, 1.0))
    G = np.empty((len(f), cut.shape[1]))
    for j in range(cut.shape[1]):
        G[:, j] = np.interp(lf, np.log(cen), cut[:, j], left=cut[0, j], right=cut[-1, j])
    G = 10 ** (-G / 20.0)
    out = np.zeros_like(music)
    for c in range(2):
        _, y = istft(Ms[c] * G, SR, nperseg=nper, noverlap=nper - hop)
        out[c, :min(len(y), music.shape[1])] = y[: music.shape[1]]
    return out
