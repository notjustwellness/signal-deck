#!/usr/bin/env python3
"""
Signal — sonic asset for the v4 "Already in you" turn-inward meditation.

Concept (codex Ch.03 §4 · brand-kit §09): the brand's entrainment mechanic
is two tones drifting to UNISON at A4. Here it runs SLOW across the whole
film: the tones begin only ~4 Hz apart and drift almost imperceptibly into
one over ~60s, settling exactly as the wordmark drifts to one. A warm,
STEADY heartbeat underneath (no acceleration). The convergence is the
recognition — a soft arrival, not a trigger.

Output:
  signal_meditation.wav  — the full ~60s bed: slow drift to unison A4 +
                           steady ~60 bpm heartbeat + warm sub. Resolves
                           and settles at the end (the wordmark moment).

Speaker note: renders a MONAURAL beat (both tones in both channels) so the
slow beating is audible on speakers, not just headphones. BINAURAL=True
for the literal one-tone-per-ear version.

Delivery: loudness-normalize to -14 LUFS, e.g.
  ffmpeg -i signal_meditation.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 out.wav
"""
import wave, struct, math
from array import array

SR          = 44100
DUR         = 60.0      # full film length
A4          = 440.0
START_SPREAD= 4.0       # Hz apart at the very start (a slow, gentle beat)
BPM         = 60.0      # steady heartbeat — never accelerates
BINAURAL    = False

def write_wav(name, left, right):
    peak = 1e-9
    for x in left:  peak = max(peak, abs(x))
    for x in right: peak = max(peak, abs(x))
    g = (10 ** (-3 / 20)) / peak           # -3 dBFS peak; loudness-normalize at delivery
    with wave.open(name, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        frames = bytearray()
        for l, r in zip(left, right):
            frames += struct.pack("<hh",
                                  int(max(-1, min(1, l * g)) * 32767),
                                  int(max(-1, min(1, r * g)) * 32767))
        w.writeframes(bytes(frames))

def render_meditation():
    n = int(SR * DUR)
    L = array('d', bytes(8 * n))
    R = array('d', bytes(8 * n))
    pl = ph = psub = 0.0
    fade_in, settle = 1.2, 3.0             # gentle in; long soft settle at the end
    for i in range(n):
        t = i / SR
        prog = t / DUR
        half = (START_SPREAD / 2.0) * (1 - prog) ** 1.6   # lingers apart, resolves near the end
        pl   += 2 * math.pi * (A4 - half) / SR
        ph   += 2 * math.pi * (A4 + half) / SR
        psub += 2 * math.pi * 110.0 / SR
        if t < fade_in:
            env = 0.5 - 0.5 * math.cos(math.pi * t / fade_in)
        elif t > DUR - settle:
            env = 0.5 + 0.5 * math.cos(math.pi * (t - (DUR - settle)) / settle)
        else:
            env = 1.0
        lo, hi, sub = math.sin(pl), math.sin(ph), 0.10 * math.sin(psub)
        if BINAURAL:                       # one tone per ear (headphones only)
            L[i] = (0.40 * lo + sub) * env
            R[i] = (0.40 * hi + sub) * env
        else:                              # monaural beat — both tones both ears
            tone = (0.32 * lo + 0.32 * hi + sub) * env
            L[i] = tone; R[i] = tone
    # steady heartbeat — additive, cheap (one pass over beats)
    thump_len = int(0.22 * SR)
    b = 0.0
    while b < DUR - 0.3:
        start = int(b * SR)
        for k in range(thump_len):
            d = k / SR
            amp = 0.22 * math.sin(2 * math.pi * 50 * d) * math.exp(-d * 20)
            idx = start + k
            if idx < n:
                L[idx] += amp; R[idx] += amp
        b += 60.0 / BPM
    write_wav("signal_meditation.wav", L, R)

if __name__ == "__main__":
    render_meditation()
    print(f"wrote signal_meditation.wav · {DUR:.0f}s · {SR}Hz stereo · "
          f"{'binaural' if BINAURAL else 'monaural beat'} · slow drift {START_SPREAD:.0f}Hz→unison A4")
