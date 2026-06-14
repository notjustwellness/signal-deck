#!/usr/bin/env python3
"""
Signal — the "signal sound" sonic mark generator.

Canon spec (codex Ch.03 §4 · brand-kit §09):
  Two tones start ~10 Hz apart and drift to UNISON at A4 (440 Hz) over ~1.5s,
  then hold. The brand calls the mechanic "entrainment" — the body's pull
  toward sync, made audible. Heard once at the open or close, never mid-roll.

Engineering note (deliberate deviation, flagged for the brand owner):
  Canon says "binaural beat." A true binaural beat puts one tone in each ear
  and only fuses on HEADPHONES — on speakers there is no audible beat. For a
  brand sting that must read on any device, this renders a MONAURAL beat:
  both tones in both channels, so the ~10 Hz beating is acoustically real on
  phones, laptops, and TVs alike. If you specifically want the headphone-only
  binaural version, set BINAURAL = True below.

Output: signal_sound.wav (stereo, 16-bit PCM, 44.1 kHz).
Final delivery: loudness-normalize to -14 LUFS, e.g.
  ffmpeg -i signal_sound.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 signal_sound_-14LUFS.wav
  ffmpeg -i signal_sound_-14LUFS.wav -b:a 256k signal_sound.mp3
"""
import wave, struct, math

SR        = 44100
DUR       = 2.0          # total seconds
GLIDE     = 1.5          # seconds spent converging; then hold unison
A4        = 440.0
SPREAD    = 10.0         # Hz apart at the start (the binaural-beat interval)
SUB_AMP   = 0.12         # subtle 220 Hz body under the two tones
TONE_AMP  = 0.42         # each of the two main tones
BINAURAL  = False        # True = one tone per ear (headphones only)

def freq_pair(t):
    """Two frequencies that glide symmetrically from A4±5 to A4 over GLIDE sec."""
    if t < GLIDE:
        k = t / GLIDE          # 0 -> 1
        # ease-out so the lock-to-unison feels settled, not linear
        k = 1 - (1 - k) ** 2
    else:
        k = 1.0
    half = (SPREAD / 2.0) * (1 - k)
    return A4 - half, A4 + half

def envelope(t):
    """Attack ~120ms; long release over the last 700ms so the mark reads clear
    exactly as the sound fades (per canon)."""
    atk, rel = 0.12, 0.70
    if t < atk:
        return 0.5 - 0.5 * math.cos(math.pi * t / atk)        # raised-cosine in
    if t > DUR - rel:
        x = (t - (DUR - rel)) / rel
        return 0.5 + 0.5 * math.cos(math.pi * x)              # raised-cosine out
    return 1.0

n = int(SR * DUR)
phase_lo = phase_hi = phase_sub = 0.0
left, right = [], []

for i in range(n):
    t = i / SR
    f_lo, f_hi = freq_pair(t)
    phase_lo  += 2 * math.pi * f_lo  / SR
    phase_hi  += 2 * math.pi * f_hi  / SR
    phase_sub += 2 * math.pi * 220.0 / SR
    env = envelope(t)
    s_lo  = math.sin(phase_lo)
    s_hi  = math.sin(phase_hi)
    s_sub = math.sin(phase_sub) * SUB_AMP

    if BINAURAL:
        l = (TONE_AMP * s_lo + s_sub) * env
        r = (TONE_AMP * s_hi + s_sub) * env
    else:  # monaural beat — both tones both ears (default, speaker-safe)
        mix = (TONE_AMP * s_lo + TONE_AMP * s_hi + s_sub) * env
        l = r = mix

    left.append(l); right.append(r)

# normalize to -3 dBFS peak (loudness-normalize to -14 LUFS at delivery)
peak = max(max(abs(x) for x in left), max(abs(x) for x in right)) or 1.0
g = (10 ** (-3 / 20)) / peak

with wave.open("signal_sound.wav", "w") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    frames = bytearray()
    for l, r in zip(left, right):
        frames += struct.pack("<hh",
                              int(max(-1, min(1, l * g)) * 32767),
                              int(max(-1, min(1, r * g)) * 32767))
    w.writeframes(bytes(frames))

print(f"wrote signal_sound.wav  ·  {DUR}s  ·  {SR}Hz stereo  ·  "
      f"{'binaural' if BINAURAL else 'monaural beat'}  ·  glide {GLIDE}s -> A4 unison")
