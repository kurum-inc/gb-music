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
uint32  wave_output_level      (wave only: 0=mute, 1=25%, 2=50%, 3=100%)
uint32  wave_waveform_index    (0-15)
uint32  noise_counter_step     (noise only: 0=15-bit, 1=7-bit/metallic)
[Subpattern]                   1089 bytes
```

### Subpattern Format (1089 bytes)
```
int8    enabled                (0=off, 1=on)
[64 cells × 17 bytes]:
  uint32  note
  uint32  jump_target (unused, write 0)
  uint32  unused (write 0)
  uint32  effect_code
  uint8   effect_param
```

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

| Code | Name | Param |
|------|------|-------|
| 0    | None | - |
| 1    | Arpeggio | upper/lower nibble = semitones |
| 2    | Portamento up | speed |
| 3    | Portamento down | speed |
| 4    | Vibrato | speed/depth |
| 12   | Set volume | 0-F |
| 15   | Set speed | new ticks_per_row |
