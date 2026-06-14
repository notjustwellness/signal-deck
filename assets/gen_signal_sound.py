#!/usr/bin/env python3
"""
Signal — sonic assets for the "coil & deny" priming film.

Concept (codex Ch.03 §4 · brand-kit §09, adapted for the priming cut):
  The brand's entrainment mechanic = two tones drifting from ~10 Hz apart
  to UNISON at A4. In THIS film the unresolved beat IS the tension: the two
  tones are held apart for the whole film (a rising, uneasy bed) and snap
  to unison only at the very end — the single release, a STARTING GUN.

Outputs:
  signal_sound.wav        — THE GUN: the snap-to-unison lock + a low
                            transient. ~1.4s. The film's only release.
  signal_tension_bed.wav  — THE BED: two tones held ~10 Hz apart (beating,
                            never resolving) + an ACCELERATING heartbeat
                            pulse. ~12s, rising. Underlays the whole film;
                            cut/time it, then lay the gun over the end.

Two deliberate deviations from canon, flagged for the brand owner:
  1) The close SNAPS (a gun), it does not softly fade — the priming brief
     wants a trigger, not a sunset.
  2) The detuned tones run as a CONTINUOUS bed (not a single end-sting),
     resolving once. Brushes the "one sonic per piece / no mid-roll" rule;
     argued as one continuous element that resolves once, not a repeated
     chime. Set classic behavior by using only the gun if you disagree.

Speaker note: both files render a MONAURAL beat (both tones in both
channels) so the ~10 Hz beating is audible on speakers, not just
headphones. Set BINAURAL=True for the literal one-tone-per-ear version.

Delivery: loudness-normalize to -14 LUFS, e.g.
  ffmpeg -i signal_sound.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 out.wav
"""
import wave, struct, math

SR       = 44100
A4       = 440.0
SPREAD   = 10.0     # Hz apart (the unresolved beat)
BINAURAL = False    # True = one tone per ear (headphones only)

def write_wav(name, left, right):
    peak = max(max((abs(x) for x in left), default=1.0),
               max((abs(x) for x in right), default=1.0)) or 1.0
    g = (10 ** (-3 / 20)) / peak          # -3 dBFS peak; normalize to -14 LUFS at delivery
    with wave.open(name, "w") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        frames = bytearray()
        for l, r in zip(left, right):
            frames += struct.pack("<hh",
                                  int(max(-1, min(1, l * g)) * 32767),
                                  int(max(-1, min(1, r * g)) * 32767))
        w.writeframes(bytes(frames))

# ─────────────────────────── THE GUN ───────────────────────────
def render_gun(dur=1.4, glide=0.5):
    n = int(SR * dur)
    pl = ph = ps = 0.0
    left, right = [], []
    for i in range(n):
        t = i / SR
        if t < glide:
            k = 1 - (1 - t / glide) ** 3          # hard ease-out → a SNAP
            half = (SPREAD / 2.0) * (1 - k)
        else:
            half = 0.0
        f_lo, f_hi = A4 - half, A4 + half
        pl += 2 * math.pi * f_lo / SR
        ph += 2 * math.pi * f_hi / SR
        ps += 2 * math.pi * 58.0 / SR             # low transient body at the lock
        # envelope: fast in, peak AT the lock, clipped decay
        if t < 0.03:
            env = t / 0.03
        else:
            env = math.exp(-(t - 0.03) * 3.2)
        tone_lo = 0.42 * math.sin(pl)
        tone_hi = 0.42 * math.sin(ph)
        # the gun transient: a short sub thump that fires right at the lock
        thump = 0.0
        if glide - 0.04 < t < glide + 0.22:
            thump = 0.55 * math.sin(ps) * math.exp(-(t - (glide - 0.04)) * 14)
        if BINAURAL:
            l = (tone_lo + thump) * env
            r = (tone_hi + thump) * env
        else:
            mix = (tone_lo + tone_hi + thump) * env
            l = r = mix
        left.append(l); right.append(r)
    write_wav("signal_sound.wav", left, right)

# ─────────────────────────── THE BED ───────────────────────────
def render_bed(dur=12.0, bpm_start=60.0, bpm_end=140.0):
    n = int(SR * dur)
    pl = ph = 0.0
    # accelerating heartbeat onsets
    beats, tcur = [], 0.0
    while tcur < dur:
        beats.append(tcur)
        bpm = bpm_start + (bpm_end - bpm_start) * (tcur / dur)
        tcur += 60.0 / bpm
    beats = set(round(b, 4) for b in beats)
    beat_list = sorted(beats)
    left, right = [], []
    for i in range(n):
        t = i / SR
        prog = t / dur
        base = A4 + 8.0 * prog                     # slow upward creep = rising unease
        half = SPREAD / 2.0                         # held apart — NEVER resolves
        f_lo, f_hi = base - half, base + half
        pl += 2 * math.pi * f_lo / SR
        ph += 2 * math.pi * f_hi / SR
        amp = 0.18 + 0.34 * prog                    # rising intensity
        tone = amp * (math.sin(pl) + math.sin(ph)) * 0.5
        # accelerating sub-bass heartbeat thump
        thump = 0.0
        for b in beat_list:
            d = t - b
            if 0 <= d < 0.20:
                thump += (0.30 + 0.30 * prog) * math.sin(2 * math.pi * 52 * d) * math.exp(-d * 22)
        l = r = tone + thump
        left.append(l); right.append(r)
    write_wav("signal_tension_bed.wav", left, right)

if __name__ == "__main__":
    render_gun()
    render_bed()
    print("wrote signal_sound.wav (the gun, 1.4s) + signal_tension_bed.wav "
          f"(rising bed, 12s) · {'binaural' if BINAURAL else 'monaural beat'}")
