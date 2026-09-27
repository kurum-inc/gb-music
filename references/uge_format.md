# UGE v6 Binary Format Reference

Full specification of the hUGETracker v6 format as used by GB Studio 4.x.

## File Structure (byte-by-byte)

```
[Version]         uint32(6)
[Song Name]       uint8(len) + 255 bytes (zero-padded)
[Artist]          uint8(len) + 255 bytes
[Comment]         uint8(len) + 255 bytes

[Duty Instr ×15]  each 1385 bytes
[Wave Instr ×15]  each 1385 bytes
[Noise Instr ×15] each 1385 bytes

[Waveforms ×16]   each 32 bytes (samples 0-15)

[Ticks Per Row]   uint32
[Timer Enabled]   int8
[Timer Divider]   uint32

[Pattern Count]   uint32 (num_patterns × 4)
[Patterns...]     each: uint32(key) + 64 cells × 17 bytes

[Sequences ×4]    each: uint32(length+1) + entries + uint32(0) terminator

[Routines ×16]    each: uint32(0)
```

## Instrument Format (1385 bytes each)

All three instrument types share the same binary layout:

```
uint32  type                   (0=duty, 1=wave, 2=noise)
str256  name                   (uint8 len + 255 bytes)
uint32  length                 (sound length counter, usually 0)
uint8   length_enabled         (0=disabled)
uint8   initial_volume         (0-15, used by duty/noise)
uint32  volume_sweep_direction (0=up, 1=down)
uint8   volume_sweep_amount    (0=none, 1-7=pace)
uint32  freq_sweep_time        (duty only, 0=disabled)
uint32  freq_sweep_direction   (0=up, 1=down)
uint32  freq_sweep_shift       (0-7)
uint8   duty_cycle             (0=12.5%, 1=25%, 2=50%, 3=75%)
uint32  wave_output_level      (wave only: NR32 code — 0=mute, 1=100%, 2=50%, 3=25%. NOT ascending!)
uint32  wave_waveform_index    (0-15)
uint32  noise_counter_step     (noise only: 0=15-bit, 1=7-bit/metallic)
[Subpattern]                   1089 bytes
```

### Subpattern Format (1089 bytes)
```
int8    enabled                (0=off, 1=on)
[64 cells × 17 bytes]:
  uint32  note         (RELATIVE offset, 36 = ±0, 90 = no change — see below)
  uint32  unused (write 0)
  uint32  jump         (0 = none, n = jump to row n-1)
  uint32  effect_code
  uint8   effect_param
```

Only the first 32 rows are exported; GB Studio forces a jump back to row 0 on row 31.
The subpattern advances one row per **tick** (not per pattern row).

### ⚠️ Subpattern notes are relative, not absolute

hUGEDriver computes `pattern_note + (subpattern_note - 36)` on every tick
(`do_table` in `hUGEDriver.asm`: `sub 36 ; bring the number back in the range of -36, +35`).
So a subpattern value of 36 (C6) means "no offset", 48 (C7) means "+12", and so on.

This matters most for noise drums, which are built from subpatterns
(e.g. Tronimal's hi-hat is `[REST, G#8, G#8, ...]` = +32 over the pattern note):

- **Write drum hits in the pattern as C5 (24)**, like the Tronimal examples do,
  and shape the pitch inside the instrument's subpattern.
- **Do not raise the pattern note to "match" the subpattern pitch.** The offsets add
  up and the result runs past the noise table, which sounds like a buzzy "beeee"
  instead of a drum. (Seen in practice: pattern notes D#8/C8/A8 with subpatterns
  already at D#8/C8/A8 → broken buzz on every drum hit.)
- Row 0 of a drum subpattern is usually REST (90) = keep the triggered note.

### Noise pitch range (drums)

The noise channel turns the final note into NR43 with `v = 63 - note`
(`get_note_poly` in `hUGEDriver.asm`). Only **32-63** gives usable drum sounds:

| Final note | Result on hardware |
|---|---|
| 0-31 | LFSR clock 2-512 Hz — nearly silent / faint crackle. Drums written here are effectively missing |
| 32-63 | Usable. Roughly kick 40-46, snare 48-54, hi-hat 56-63 |
| 64+ | Overflows (wraps into 7-bit mode) — buzzy "beeee" |

"Final note" is the pattern note, plus the subpattern offset if the instrument has one.
Two ways that both work:
- **No subpattern:** write the drum hit directly at 32-63 (e.g. hat 57, snare 48, kick 40)
- **With subpattern (Tronimal style):** write the hit as C5 (24) and shape the pitch per tick in the
  subpattern (e.g. kick `[REST, D#8, A7, D7, G6, C6, C6]` = 51 → 24)

### Length field

`length` stores the hardware length-load value, not a duration. Bigger = shorter.
- Duty / noise: sound lasts `(64 - length) / 256` s (e.g. 48 → 62 ms, 22 → 164 ms)
- Wave: sound lasts `(256 - length) / 256` s
- Only takes effect when `length_enabled = 1`.

## Pattern Cell Format (17 bytes)

```
uint32  note           (0-71 = C3-B8, 90 = REST)
uint32  instrument     (0=none, 1=first instrument, 2=second, etc.)
uint32  unused         (always 0)
uint32  effect_code    (0=none, see effect table)
uint8   effect_param   (effect-specific parameter)
```

## Pattern Keys

Each pattern track has a unique key: `pattern_index * 4 + track_index`

For 2 patterns:
- Pattern 0: keys 0, 1, 2, 3 (tracks 0-3)
- Pattern 1: keys 4, 5, 6, 7 (tracks 0-3)

## Sequence Format

For each of 4 tracks:
```
uint32  entry_count    (number of entries + 1)
uint32  entry[0]       (pattern key)
uint32  entry[1]       ...
uint32  terminator     (0)
```

Sequence entries reference pattern keys:
`sequence_entry = pattern_order_index * 4 + track`

Example: sequence [0, 1, 0, 1] for track 0 → entries [0, 4, 0, 4]

## Note Value Table

| Octave | C  | C# | D  | D# | E  | F  | F# | G  | G# | A  | A# | B  |
|--------|----|----|----|----|----|----|----|----|----|----|----|----|
| 3      | 0  | 1  | 2  | 3  | 4  | 5  | 6  | 7  | 8  | 9  | 10 | 11 |
| 4      | 12 | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 |
| 5      | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 | 33 | 34 | 35 |
| 6      | 36 | 37 | 38 | 39 | 40 | 41 | 42 | 43 | 44 | 45 | 46 | 47 |

REST = 90

## Tempo to BPM (approximate)

The relationship is: `BPM ≈ 3600 / (ticks_per_row * rows_per_beat)`

With 4 rows per beat:
| Ticks | ~BPM |
|-------|------|
| 3     | 300  |
| 4     | 225  |
| 5     | 180  |
| 6     | 150  |
| 7     | 128  |
| 8     | 112  |
| 10    | 90   |

## Common Effects

Codes follow the jump table in `hUGEDriver.asm`. Code 0 with param 0 means "no effect".

| Code | Name | Param |
|------|------|-------|
| 0 (0x0) | Arpeggio | x/y nibbles = semitones above the note (e.g. 0x47 = major chord). 0x00 = no effect |
| 1 (0x1) | Portamento up | speed |
| 2 (0x2) | Portamento down | speed (Tronimal kick: C6 on a wave instrument + `2 80`, `2 40`, then `E 00`) |
| 3 (0x3) | Tone portamento | speed (slide toward the new note) |
| 4 (0x4) | Vibrato | x = speed, y = depth |
| 5 (0x5) | Set master volume | NR50 value (global) |
| 7 (0x7) | Note delay | ticks |
| 8 (0x8) | Set panning | NR51 value (global) |
| 9 (0x9) | Set duty | duty cycle |
| 10 (0xA) | Volume slide | x = up, y = down |
| 11 (0xB) | Position jump | order index (global) |
| 12 (0xC) | Set volume | channel volume / envelope |
| 13 (0xD) | Pattern break | row (global) |
| 14 (0xE) | Note cut | ticks (0 = cut immediately) |
| 15 (0xF) | Set speed | new ticks_per_row (global) |
