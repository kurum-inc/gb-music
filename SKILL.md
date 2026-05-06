---
name: gb-music
description: |
  Generate Game Boy music (.uge) and sound effects (.sav) for GB Studio projects. Use this skill whenever the user wants to create chiptune BGM, sound effects, or convert audio files to Game Boy format. Triggers include: any mention of 'BGM', 'SFX', 'UGE', '.uge', 'FX Hammer', '.sav sound', 'Game Boy music', 'GB Studio music', 'chiptune', '8-bit music', 'retro game music', 'sound effects for game', or requests to make music/sounds for a Game Boy or GB Studio project. Also triggers when converting MP3/M4A/WAV to Game Boy format. Use this skill even if the user just says "make me some game music" or "I need a theme song for my game" — if the project is GB Studio or Game Boy related, this skill applies.
---

# GB Music & SFX Generator

Generate Game Boy compatible music (.uge) and sound effects (.sav) programmatically using Python. All output is binary-compatible with GB Studio 4.x.

## Quick Reference

Two output formats:
- **`.uge`** — hUGETracker v6 music files (BGM, jingles). Loops automatically in GB Studio.
- **`.sav`** — FX Hammer sound effect banks. Up to 60 effects per file, played via "Play Sound Effect" event.

## How to Use This Skill

1. Read the user's request to understand genre, mood, tempo, key, duration
2. Choose the appropriate format (.uge for BGM/jingles, .sav for short SFX)
3. Read `references/uge_format.md` for BGM generation or `references/sav_format.md` for SFX
4. Write a Python script using the patterns in `scripts/uge_template.py` or `scripts/sav_template.py`
5. Run it to produce the binary file

## UGE Format Overview

The .uge file is a binary format (little-endian) with this structure:
- Version header (uint32: 6)
- Song name, artist, comment (each: uint8 length + 255 bytes)
- 15 Duty instruments, 15 Wave instruments, 15 Noise instruments (each 1385 bytes)
- 16 waveforms (each 32 bytes)
- Timing: ticks_per_row (uint32), timer_enabled (int8), timer_divider (uint32)
- Patterns: count (uint32), then pattern data (each: uint32 track_key + 64 cells × 17 bytes)
- Sequences: 4 tracks × (uint32 length+1, entries as uint32, uint32 terminator)
- 16 routines (uint32 zeros)

Each cell: uint32 note, uint32 instrument (1-based, 0=none), uint32 unused, uint32 effect_code, uint8 effect_param.

Note values: 0=C3, 12=C4, 24=C5, 36=C6, 90=REST.

Tempo guide: 4=fast/energetic, 5=moderate, 6=relaxed, 7-8=slow/calm, 10+=very slow.

## SAV Format Overview

FX Hammer .sav is a 32,768-byte SRAM dump:
- Magic `"FX HAMMER"` at offset 0x009
- Channel flags at 0x300 (one byte per effect: 0x30=Ch2 pulse, 0x03=Ch4 noise, 0x33=both)
- Effect data at 0x400 + index×0x100 (up to 32 frames × 8 bytes each)

Each frame: duration, ch2_pan, ch2_vol, ch2_duty, ch2_freq, ch4_pan, ch4_vol, ch4_freq.
Duration 0 = end marker. Pan 0x22 = both speakers.

## Audio-to-UGE Conversion

When converting MP3/M4A/WAV to Game Boy format:

1. Install librosa: `pip install librosa --break-system-packages`
2. Analyze: tempo detection, chroma features for key, chord progression via chroma segmentation
3. Melody extraction: use HPSS (harmonic-percussive separation) then pyin pitch detection
4. Map MIDI notes to UGE values: `uge_note = midi_note - 48` (MIDI 48 = C3 = UGE 0)
5. Snap to detected key's scale, normalize octave range
6. Generate .uge with extracted melody on Ch1, chords on Ch2, bass on Ch3, drums on Ch4

Note: polyphonic sources often produce noisy melody extraction. When pyin returns mostly None or flat values, fall back to hand-crafting a melody from the detected chord progression and key.

## Composition Guidelines

### Channel Allocation
- **Ch1 (Duty):** Lead melody — bright, prominent
- **Ch2 (Duty):** Harmony/rhythm — chords, arpeggios, counter-melody
- **Ch3 (Wave):** Bass line — root notes, walking bass
- **Ch4 (Noise):** Percussion — hats, snare, kick, shaker

### SFX Design Patterns

| Sound | Approach |
|-------|----------|
| Hit/Impact | High vol, fast decay, both channels |
| Jump | Ascending pitch sweep (Ch2 only) |
| Coin/Collect | Two quick high notes |
| Explosion/Crash | Max vol noise, slow decay |
| Rolling | Descending pitch + continuous noise |
| Chime/Correct | Two-tone (low→high), sustained |
| Cursor/UI | Single short blip |

## File Size Reference

Expected .uge file sizes (for validation):
- 1 pattern, 1-entry sequence: ~68,102 bytes
- 2 patterns, 2-entry sequence: ~72,486 bytes
- 2 patterns, 4-entry sequence: ~72,518 bytes
- 3 patterns, 4-entry sequence: ~76,886 bytes

## Important Notes

- Instrument index in cells is 1-based (instrument 0 in array → write 1 in cell)
- Pattern keys must be unique: `pattern_index * 4 + track_index`
- Sequence entries reference pattern keys: `sequence_pattern * 4 + track`
- All instruments are exactly 1385 bytes (296 header + 1089 subpattern)
- Subpattern: 1 byte enabled + 64 cells × 17 bytes
- GB Studio BGM always loops — for one-shot sounds, use .sav format or stop via event
- .sav effects use only Ch2 (pulse) and Ch4 (noise), leaving Ch1 and Ch3 free for music
