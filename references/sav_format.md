# FX Hammer .sav Format Reference

Full specification of the FX Hammer sound effect format as used by GB Studio 4.x.

## File Structure

Total size: 32,768 bytes (8KB SRAM dump)

```
Offset  Size    Content
------  ------  -------
0x000   9       Padding (zeros)
0x009   9       Magic: "FX HAMMER"
0x012   ...     Padding
0x300   60      Channel flags (1 byte per effect slot)
0x400   15360   Effect data (60 slots × 256 bytes each)
```

## Channel Flags (offset 0x300)

One byte per effect slot (0-59):
- `0x00` = Empty/unused slot
- `0x30` = Ch2 (pulse) only
- `0x03` = Ch4 (noise) only
- `0x33` = Both Ch2 and Ch4

The high nibble controls Ch2, low nibble controls Ch4.

FX Hammer only uses channels 2 and 4, leaving channels 1 and 3 free for background music.

## Effect Data (offset 0x400 + index × 0x100)

Each effect slot is 256 bytes, containing up to 32 frames of 8 bytes each.

### Frame Format (8 bytes)

```
Byte  Purpose            GB Register
----  -------            -----------
0     Duration           (frames to hold, 0 = end marker)
1     Ch2 Panning        NR51 bits
2     Ch2 Volume/Env     NR22 (volume + envelope)
3     Ch2 Duty Cycle     NR21 (wave duty pattern)
4     Ch2 Frequency      NR23 (freq low byte)
5     Ch4 Panning        NR51 bits
6     Ch4 Volume/Env     NR42 (volume + envelope)
7     Ch4 Frequency      NR43 (polynomial counter)
```

### Duration
- 1 = shortest (1/60th second at 60fps)
- Higher values = longer hold
- 0 = end of effect (terminator)

### Panning
- `0x22` = Both L+R speakers (stereo center)
- `0x20` = Left only
- `0x02` = Right only
- `0x00` = Silent/muted

### Volume/Envelope Register (NR22/NR42)
```
Bits 7-4: Initial volume (0-15, F=loudest)
Bit  3:   Envelope direction (0=decrease, 1=increase)
Bits 2-0: Sweep pace (0=no envelope, 1-7=speed, 1=fastest)
```

Common values:
- `0xF8` = Max volume, no sweep (sustained)
- `0xF0` = Max volume, no envelope
- `0xB8` = Vol 11, decreasing
- `0x78` = Vol 7, decreasing
- `0x48` = Vol 4, decreasing (quiet)
- `0x08` = Nearly silent

### Duty Cycle Register (NR21, Ch2 only)
```
Bits 7-6: Wave duty
  00 = 12.5% (thin, buzzy)
  01 = 25%   (hollow, reed-like)
  10 = 50%   (full square wave, most common)
  11 = 75%   (same as 25% inverted)
```

Values: `0x00`, `0x40`, `0x80`, `0xC0`

### Ch2 Frequency (NR23)
Low byte of the 11-bit frequency register. Higher value = higher pitch.

Approximate ranges:
- `0x30-0x50` = Very low tones
- `0x60-0x80` = Low-mid tones
- `0x90-0xA0` = Mid tones
- `0xB0-0xC0` = High tones
- `0xD0-0xE0` = Very high tones

### Ch4 Noise Frequency (NR43)
Polynomial counter configuration. Lower value = higher pitch noise.

- `0x20` = White noise / crash
- `0x30-0x40` = Medium noise
- `0x50-0x70` = Filtered / soft noise

## Design Tips

### Impact Sounds
- Start with max volume, fast decay
- Use both channels: pulse for tone, noise for texture
- 2-4 frames, short durations

### Sweeps (jump, power-up)
- Ch2 only, ascending frequency across frames
- 4-8 frames, duration 1 each
- Volume can stay constant or slight decay

### Explosions / Crashes
- Noise channel dominant
- Start loud, long decay over many frames
- Optional low pulse tone underneath

### UI Sounds (confirm, cursor)
- Ch2 only, 1-2 frames
- Clean square wave (duty 0x80)
- Short duration

### Chimes (correct answer, collect)
- Two distinct pitches: low → high
- Longer duration on second note
- Minimal or no noise channel

## GB Studio Integration

In GB Studio, sound effects are played via events:
- **Play Sound Effect**: select the .sav file and effect index (0-59)
- Effects play on Ch2/Ch4, interrupting any music on those channels momentarily
- Ch1 (pulse) and Ch3 (wave) continue playing music uninterrupted
- Multiple .sav files can be used in a project
- Effects don't loop — they play once and stop
