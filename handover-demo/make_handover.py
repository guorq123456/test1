#!/usr/bin/env python3
"""Handover (交接): a 60-second demo of the "let the playback device decide who sings" mix.

Everything here is original and synthesized: the melody, the chords and both voices.
Neither voice is a real singer.
  - The "machine" voice has exact pitch, hard note edges, and never breathes.
  - The "human" voice has vibrato, pitch scoops, slow drift, breathiness and audible inhales.

Anything placed in anti-phase (left = +x, right = -x) is audible on headphones and cancels
to silence when the two channels are summed to mono (one speaker, or "Mono Audio" on a phone).

  0:00-0:06  pad only
  0:06-0:30  machine sings the melody (center); human sings a counter-line (anti-phase)
  0:30-0:54  roles swap: human sings the melody (center); machine sings the counter-line (anti-phase)
  0:54-end   human exhale (center); the machine's last note (anti-phase)

Run:  python3 make_handover.py
Writes handover.wav (stereo) and handover-mono-preview.wav ((L+R)/2) next to this file.
"""
from pathlib import Path
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
BEAT = 60 / 80  # 80 BPM
BAR = 4 * BEAT  # 3 s
TOTAL = 20 * BAR + 1.5  # 20 bars plus a reverb tail
N = int(TOTAL * SR)
OUT_DIR = Path(__file__).resolve().parent
rng = np.random.default_rng(1)

# Rough formants for a light voice: (Hz, gain) for F1-F3. Bandwidths are per formant index.
VOWELS = {
    "a": ((850, 1.0), (1220, 0.50), (2810, 0.25)),
    "e": ((560, 1.0), (2320, 0.40), (2950, 0.22)),
    "i": ((310, 1.0), (2790, 0.35), (3310, 0.20)),
    "o": ((560, 1.0), (920, 0.50), (2830, 0.15)),
    "u": ((370, 1.0), (950, 0.35), (2670, 0.12)),
}
BANDWIDTHS = (90, 130, 180)

# (start beat, length in beats, MIDI note, vowel), relative to the start of a section.
MELODY = [
    (0, 1, 69, "a"), (1, 1, 72, "e"), (2, 1.5, 76, "i"), (3.5, 0.5, 74, "a"),
    (4, 2, 72, "o"), (6, 2, 69, "a"),
    (8, 1, 67, "e"), (9, 1, 72, "a"), (10, 1, 76, "i"), (11, 1, 74, "o"),
    (12, 3, 74, "a"),
    (16, 1, 69, "a"), (17, 1, 72, "e"), (18, 1.5, 76, "i"), (19.5, 0.5, 79, "a"),
    (20, 2, 77, "o"), (22, 1, 76, "e"), (23, 1, 72, "a"),
    (24, 1.5, 74, "i"), (25.5, 0.5, 72, "a"), (26, 1, 69, "o"), (27, 1, 72, "e"),
    (28, 3, 71, "a"),
]
COUNTER = [
    (0, 4, 64, "u"),
    (4, 2, 65, "u"), (6, 2, 64, "o"),
    (8, 2, 64, "u"), (10, 2, 67, "o"),
    (12, 2, 71, "u"), (14, 2, 67, "o"),
    (16, 2, 64, "u"), (18, 1, 67, "o"), (19, 1, 69, "u"),
    (20, 4, 69, "o"),
    (24, 4, 65, "u"),
    (28, 4, 68, "o"),
]
PHRASE_STARTS = (0, 16)  # in beats

CHORDS = {  # pad notes, bass note
    "Am": ([57, 60, 64], 45),
    "Fmaj7": ([53, 57, 60, 64], 41),
    "C": ([55, 60, 64], 36),
    "G": ([55, 59, 62], 43),
    "Dm7": ([53, 57, 60, 62], 38),
    "E": ([56, 59, 64], 40),
}
SECTION = ["Am", "Fmaj7", "C", "G", "Am", "Fmaj7", "Dm7", "E"]
A_START = 2 * BAR  # 0:06
B_START = 10 * BAR  # 0:30
OUTRO = 18 * BAR  # 0:54


def s2i(t):
    return int(round(t * SR))


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def slow_noise(cutoff, std):
    """Smooth random wobble, generated at a control rate and interpolated to audio rate."""
    cr = 200
    m = int(TOTAL * cr) + 2
    x = sosfilt(butter(2, cutoff, "low", fs=cr, output="sos"), rng.standard_normal(m))
    x = (x - x.mean()) / (x.std() + 1e-12) * std
    return np.interp(np.arange(N) / SR, np.arange(m) / cr, x)


def smooth(x, seconds):
    """Centered moving average in O(n)."""
    w = max(1, int(seconds * SR))
    if w == 1:
        return x
    c = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(len(x))
    lo = np.clip(i - w // 2, 0, len(x))
    hi = np.clip(i + (w - w // 2), 0, len(x))
    return (c[hi] - c[lo]) / (hi - lo)


def fill_gaps(x):
    """Fill NaNs with the next defined value (so a note after a rest starts at its own pitch)."""
    y = x[::-1].copy()
    idx = np.where(np.isnan(y), 0, np.arange(len(y)))
    np.maximum.accumulate(idx, out=idx)
    y = y[idx][::-1]
    last = np.where(~np.isnan(y))[0][-1]
    y[last + 1:] = y[last]
    return y


def place(pattern, t0, human):
    """Turn a beat pattern into absolute (start, dur, midi, vowel) notes."""
    notes = []
    for beat, beats, midi, vowel in pattern:
        if human and beat + beats in (16, 32):
            beats -= 0.9  # leave room to breathe before the next phrase
        notes.append([t0 + beat * BEAT, beats * BEAT, midi, vowel])
    if human:  # loosen the timing a little, keeping legato notes joined
        for j in range(len(notes)):
            d = rng.uniform(-0.015, 0.015)
            if j > 0 and abs(notes[j - 1][0] + notes[j - 1][1] - notes[j][0]) < 1e-6:
                notes[j - 1][1] += d
            notes[j][0] += d
            notes[j][1] -= d
    return notes


def additive(f0, amp, formants, gains, tilt, odd_gain, harmonics=28, chunk=1 << 16):
    """Harmonic source shaped by time-varying formant resonances."""
    phase = 2 * np.pi * np.cumsum(f0) / SR
    out = np.zeros(N)
    k = np.arange(1, harmonics + 1)[:, None].astype(float)
    source = k ** -tilt * np.where(k % 2 == 1, odd_gain, 1.0)
    for s in range(0, N, chunk):
        e = min(s + chunk, N)
        if amp[s:e].max() < 1e-6:
            continue
        fk = k * f0[None, s:e]
        env = np.full_like(fk, 0.02)
        for F, G, bw in zip(formants, gains, BANDWIDTHS):
            env += G[None, s:e] / np.sqrt(1 + ((fk - F[None, s:e]) / (bw / 2)) ** 2)
        taper = 1 / (1 + (fk / 6500) ** 8)
        out[s:e] = amp[s:e] * np.sum(source * env * taper * np.sin(k * phase[None, s:e]), axis=0)
    return out


def render_voice(notes, human, level):
    midi = np.full(N, np.nan)
    amp = np.zeros(N)
    formants = [np.full(N, np.nan) for _ in range(3)]
    gains = [np.full(N, np.nan) for _ in range(3)]
    cents = np.zeros(N)
    vib_depth = np.zeros(N)
    attack, release = (0.07, 0.14) if human else (0.008, 0.025)
    for j, (t0, d, m, v) in enumerate(notes):
        i0, i1 = s2i(t0), s2i(t0 + d)
        n = i1 - i0
        legato_in = j > 0 and abs(notes[j - 1][0] + notes[j - 1][1] - t0) < 1e-6
        legato_out = j + 1 < len(notes) and abs(t0 + d - notes[j + 1][0]) < 1e-6
        env = np.ones(n)
        if not (human and legato_in):
            a = min(s2i(attack), n)
            env[:a] *= np.linspace(0, 1, a, endpoint=False)
        if not (human and legato_out):
            r = min(s2i(release), n)
            env[n - r:] *= np.linspace(1, 0, r)
        if human:
            t = np.arange(n) / SR
            env *= 0.85 + 0.15 * np.sin(np.pi * t / d)  # gentle swell over the note
            if not legato_in:  # scoop up into notes that start after a rest
                sc = min(s2i(0.12), n)
                cents[i0:i0 + sc] -= 45 * (1 - np.linspace(0, 1, sc)) ** 2
            if d > 0.6:  # vibrato settles in on longer notes
                vib_depth[i0:i1] = 28 * np.clip((t - 0.28) / 0.37, 0, 1)
        amp[i0:i1] = np.maximum(amp[i0:i1], env)
        midi[i0:i1] = m
        for f, (freq, gain) in enumerate(VOWELS[v]):
            formants[f][i0:i1] = freq
            gains[f][i0:i1] = gain

    midi = fill_gaps(midi)
    formants = [fill_gaps(x) for x in formants]
    gains = [fill_gaps(x) for x in gains]
    if human:
        midi = smooth(midi, 0.09)  # portamento between joined notes
        vib_phase = 2 * np.pi * np.cumsum(5.4 + slow_noise(0.5, 0.25)) / SR
        cents += smooth(vib_depth, 0.08) * np.sin(vib_phase) + slow_noise(2.0, 5.0)
        amp *= 1 + slow_noise(6.0, 0.05)
    blur = 0.06 if human else 0.015  # how quickly one vowel turns into the next
    formants = [smooth(x, blur) for x in formants]
    gains = [smooth(x, blur) for x in gains]

    f0 = hz(midi + cents / 100)
    out = additive(f0, amp, formants, gains, tilt=1.0 if human else 0.75, odd_gain=1.0 if human else 1.25)
    out /= np.abs(out).max()
    if human:  # breathiness
        noise = sosfilt(butter(2, [900, 5500], "bandpass", fs=SR, output="sos"), rng.standard_normal(N))
        out += 0.05 * noise / noise.std() * amp
    return level * out / np.abs(out).max()


def breath(start, dur, level, inhale=True):
    """Filtered-noise inhale or exhale, returned as a full-length track."""
    track = np.zeros(N)
    n = s2i(dur)
    lo, hi = (500, 3500) if inhale else (300, 2500)
    x = sosfilt(butter(2, [lo, hi], "bandpass", fs=SR, output="sos"), rng.standard_normal(n + 2000))[2000:]
    t = np.linspace(0, 1, n)
    if inhale:
        env = np.sin(np.pi / 2 * np.clip(t / 0.75, 0, 1)) ** 2 * np.clip((1 - t) / 0.18, 0, 1)
    else:
        env = np.clip(t / 0.15, 0, 1) * (1 - t) ** 1.5
    i0 = s2i(start)
    track[i0:i0 + n] = level * x / np.abs(x).max() * env
    return track


def pad_and_bass(progression):
    pad, bass = np.zeros(N), np.zeros(N)
    for start, length, release, name in progression:
        notes, root = CHORDS[name]
        i0 = s2i(start)
        n = min(s2i(length + release), N - i0)
        t = np.arange(n) / SR
        env = np.clip(t / 0.35, 0, 1) * np.clip((length + release - t) / release, 0, 1)
        for m in notes:
            for detune in (-5, 5):
                f = hz(m + detune / 100)
                for k in range(1, 7):
                    pad[i0:i0 + n] += env * k ** -1.6 * np.sin(2 * np.pi * k * f * t + rng.uniform(0, 2 * np.pi))
        fb = hz(root)
        benv = np.clip(t / 0.03, 0, 1) * np.exp(-t / 2.5) * np.clip((length + 0.3 - t) / 0.3, 0, 1)
        bass[i0:i0 + n] += benv * (np.sin(2 * np.pi * fb * t) + 0.25 * np.sin(4 * np.pi * fb * t))
    pad = sosfilt(butter(2, 2500, "low", fs=SR, output="sos"), pad)
    return pad / np.abs(pad).max(), bass / np.abs(bass).max()


def reverb(x, rt60=1.8, length=2.4):
    t = np.arange(s2i(length)) / SR
    ir = sosfilt(butter(2, 4500, "low", fs=SR, output="sos"), rng.standard_normal(len(t)) * np.exp(-6.91 * t / rt60))
    ir[: s2i(0.02)] = 0
    return fftconvolve(x, ir / np.sqrt(np.sum(ir ** 2)))[:N]


def write_wav(path, data):
    x = np.clip(np.round(data * 32767), -32768, 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1 if x.ndim == 1 else x.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x.tobytes())


def read_wav(path):
    with wave.open(str(path), "rb") as w:
        ch = w.getnchannels()
        x = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(float) / 32767
    return x.reshape(-1, ch)


def dbfs(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def main():
    progression = [(0, BAR, 0.9, "Am"), (BAR, BAR, 0.9, "Fmaj7")]
    for start in (A_START, B_START):
        progression += [(start + i * BAR, BAR, 0.9, name) for i, name in enumerate(SECTION)]
    progression.append((OUTRO, 2 * BAR, 1.5, "Am"))
    pad, bass = pad_and_bass(progression)

    # Section A: the machine leads from the center; the human answers in anti-phase.
    machine_a = render_voice(place(MELODY, A_START, human=False), human=False, level=0.5)
    human_a = render_voice(place(COUNTER, A_START, human=True), human=True, level=0.42)
    # Section B: the same two lines, with the singers and their positions swapped.
    human_b = render_voice(place(MELODY, B_START, human=True), human=True, level=0.5)
    machine_b = render_voice(place(COUNTER, B_START, human=False), human=False, level=0.42)
    # Outro: the machine's last note, and the human breathing out.
    ghost = render_voice([[OUTRO + 0.9, 3.5, 69, "u"]], human=False, level=0.25)

    inhales_a = sum(breath(A_START + b * BEAT - 0.56, 0.5, 0.1) for b in PHRASE_STARTS)
    inhales_b = sum(breath(B_START + b * BEAT - 0.56, 0.5, 0.1) for b in PHRASE_STARTS)
    exhale = breath(OUTRO + 0.35, 1.1, 0.12, inhale=False)

    center = 0.12 * pad + 0.14 * bass + machine_a + human_b + inhales_b + exhale
    side = human_a + inhales_a + machine_b + ghost
    center += 0.22 * reverb(center)
    side += 0.22 * reverb(side)  # same mono reverb, so the side stays exactly anti-phase

    fade = np.clip((TOTAL - np.arange(N) / SR) / 3.0, 0, 1)
    center, side = center * fade, side * fade
    left, right = center + side, center - side
    scale = 0.89 / max(np.abs(left).max(), np.abs(right).max())

    stereo_path = OUT_DIR / "handover.wav"
    mono_path = OUT_DIR / "handover-mono-preview.wav"
    write_wav(stereo_path, np.stack([left, right], axis=1) * scale)
    write_wav(mono_path, center * scale)

    # Check the trick on the written file: side = what only headphones carry, residual = side leaking into mono.
    x = read_wav(stereo_path)
    mono = (x[:, 0] + x[:, 1]) / 2
    for label, t0, t1 in (("A 0:06-0:30", A_START + 0.5, B_START - 1), ("B 0:30-0:54", B_START + 0.5, OUTRO - 1)):
        i0, i1 = s2i(t0), s2i(t1)
        side_level = dbfs((x[i0:i1, 0] - x[i0:i1, 1]) / 2)
        leak = dbfs(mono[i0:i1] - center[i0:i1] * scale)
        print(f"section {label}: anti-phase voice on headphones {side_level:6.1f} dBFS, left in mono {leak:6.1f} dBFS")
    print(f"wrote {stereo_path.name} ({len(x) / SR:.1f} s, peak {np.abs(x).max():.2f}) and {mono_path.name}")


if __name__ == "__main__":
    main()
