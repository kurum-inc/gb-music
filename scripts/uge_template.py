"""
UGE v6 File Generator Template for GB Studio 4.x
Usage: Copy this template and customize the musical content.
"""
import struct


def generate_uge(filename, song_name="Untitled", artist="", comment="",
                 tempo=6, num_patterns=2, sequence=None, patterns_data=None):
    """
    Generate a complete .uge file.

    Args:
        filename: Output file path
        song_name: Song title (max 255 chars)
        artist: Artist name
        comment: Comment string
        tempo: Ticks per row (4=fast, 6=moderate, 8=slow)
        num_patterns: Number of patterns (each has 4 tracks × 64 rows)
        sequence: List of pattern indices for playback order (same for all tracks)
        patterns_data: Function that returns note data per pattern/track/row
    """
    data = bytearray()

    # === Helper functions ===
    def u32(v): data.extend(struct.pack('<I', v & 0xFFFFFFFF))
    def u8(v): data.extend(struct.pack('B', v & 0xFF))
    def i8(v): data.extend(struct.pack('b', v))
    def sstr(s):
        e = s.encode('utf-8')[:255]
        u8(len(e)); data.extend(e); data.extend(b'\x00' * (255 - len(e)))
    def cell(note, inst, effect_code=0, effect_param=0):
        u32(note); u32(inst); u32(0); u32(effect_code); u8(effect_param)
    def subpattern_empty():
        i8(0)  # not enabled
        for _ in range(64):
            u32(90); u32(0); u32(0); u32(0); u8(0)

    # === Instrument helpers (unified 1385-byte format) ===
    def duty_instrument(name, vol=15, vol_sweep=0, duty_cycle=2):
        """Add a Duty (pulse) instrument. duty_cycle: 0=12.5%, 1=25%, 2=50%, 3=75%"""
        u32(0)  # type = duty
        sstr(name)
        u32(0); u8(0)  # length, length_enabled
        u8(vol)
        u32(1 if vol_sweep < 0 else 0)  # vol_sweep_direction
        u8((8 - abs(vol_sweep)) if vol_sweep else 0)  # vol_sweep_amount
        u32(0); u32(0); u32(0)  # freq_sweep_time, freq_sweep_dir, freq_sweep_shift
        u8(duty_cycle)
        u32(0); u32(0); u32(0)  # wave_output_level, wave_waveform_index, noise_counter_step
        subpattern_empty()

    def wave_instrument(name, vol=2, waveform_index=0):
        """Add a Wave instrument. vol: 0=mute, 1=25%, 2=50%, 3=100%"""
        u32(1)  # type = wave
        sstr(name)
        u32(0); u8(0); u8(0)  # length, length_enabled, initial_volume (unused)
        u32(0); u8(0)  # vol_sweep_direction, vol_sweep_amount (unused)
        u32(0); u32(0); u32(0)  # freq_sweep (unused)
        u8(0)  # duty_cycle (unused)
        u32(vol)  # wave_output_level
        u32(waveform_index)
        u32(0)  # noise_counter_step (unused)
        subpattern_empty()

    def noise_instrument(name, vol=15, vol_sweep=0, bit_count=15):
        """Add a Noise instrument. bit_count: 15=normal, 7=metallic"""
        u32(2)  # type = noise
        sstr(name)
        u32(0); u8(0); u8(vol)
        u32(1 if vol_sweep < 0 else 0)
        u8((8 - abs(vol_sweep)) if vol_sweep else 0)
        u32(0); u32(0); u32(0)  # freq_sweep (unused)
        u8(0)  # duty_cycle (unused)
        u32(0); u32(0)  # wave fields (unused)
        u32(1 if bit_count == 7 else 0)
        subpattern_empty()

    def empty_duty():
        duty_instrument("", vol=0, duty_cycle=0)

    def empty_wave():
        wave_instrument("", vol=0)

    def empty_noise():
        noise_instrument("", vol=0)

    # === File header ===
    u32(6)  # version
    sstr(song_name)
    sstr(artist)
    sstr(comment)

    # === Instruments (override these in your script) ===
    # Default: 2 usable duty + 13 empty, 1 usable wave + 14 empty, 2 usable noise + 13 empty
    duty_instrument("Lead", vol=14, vol_sweep=-1, duty_cycle=2)
    duty_instrument("Harmony", vol=10, vol_sweep=-2, duty_cycle=1)
    for _ in range(13): empty_duty()

    wave_instrument("Bass", vol=2, waveform_index=0)
    for _ in range(14): empty_wave()

    noise_instrument("HiHat", vol=7, vol_sweep=-4, bit_count=7)
    noise_instrument("Snare", vol=12, vol_sweep=-3)
    for _ in range(13): empty_noise()

    # === Waveforms (16 × 32 samples, values 0-15) ===
    # Wave 0: triangle-ish
    wave0 = [0, 2, 4, 6, 8, 10, 12, 14, 15, 15, 14, 12, 10, 8, 6, 4,
             2, 0, 0, 0, 2, 4, 6, 8, 10, 12, 14, 15, 14, 12, 8, 4]
    for wi in range(16):
        if wi == 0:
            for s in wave0: u8(s)
        else:
            for _ in range(32): u8(8)  # flat

    # === Timing ===
    u32(tempo)
    i8(0)   # timer_enabled
    u32(0)  # timer_divider

    # === Patterns ===
    u32(num_patterns * 4)  # total pattern tracks

    if patterns_data:
        for pi in range(num_patterns):
            for ti in range(4):
                u32(pi * 4 + ti)  # pattern key (MUST be unique!)
                for row in range(64):
                    note, inst, ec, ep = patterns_data(pi, ti, row)
                    cell(note, inst, ec, ep)
    else:
        # Empty patterns
        for pi in range(num_patterns):
            for ti in range(4):
                u32(pi * 4 + ti)
                for _ in range(64):
                    cell(90, 0, 0, 0)

    # === Sequences ===
    if sequence is None:
        sequence = list(range(num_patterns))

    for track in range(4):
        u32(len(sequence) + 1)
        for pat_idx in sequence:
            u32(pat_idx * 4 + track)
        u32(0)  # terminator

    # === Routines (16 × uint32 zeros) ===
    for _ in range(16):
        u32(0)

    # === Write ===
    with open(filename, 'wb') as f:
        f.write(data)
    print(f"Written {len(data)} bytes to {filename}")
    return len(data)


# === Note Constants ===
# UGE note 0 = C3, 12 = C4, 24 = C5, 36 = C6, 90 = REST
C3, Cs3, D3, Ds3, E3, F3, Fs3, G3, Gs3, A3, As3, B3 = range(12)
C4, Cs4, D4, Ds4, E4, F4, Fs4, G4, Gs4, A4, As4, B4 = range(12, 24)
C5, Cs5, D5, Ds5, E5, F5, Fs5, G5, Gs5, A5, As5, B5 = range(24, 36)
C6, Cs6, D6, Ds6, E6, F6, Fs6, G6, Gs6, A6, As6, B6 = range(36, 48)
REST = 90

# Instrument indices (1-based for cell data)
LEAD = 1
HARMONY = 2
BASS = 1      # first wave instrument
HIHAT = 1     # first noise instrument
SNARE = 2     # second noise instrument


# === Example usage ===
if __name__ == '__main__':
    def my_patterns(pattern_idx, track_idx, row):
        """Return (note, instrument, effect_code, effect_param) for each cell."""
        if track_idx == 0:  # Lead
            if row % 4 == 0:
                notes = [C5, E5, G5, C6]
                return notes[row // 16], LEAD, 0, 0
        elif track_idx == 1:  # Harmony
            if row % 8 == 0:
                return E4, HARMONY, 0, 0
        elif track_idx == 2:  # Bass
            if row % 4 == 0:
                return C3, BASS, 0, 0
        elif track_idx == 3:  # Drums
            if row % 4 == 0:
                return B3, HIHAT, 0, 0
            elif row % 8 == 4:
                return B3, SNARE, 0, 0
        return REST, 0, 0, 0

    generate_uge(
        '/tmp/example_bgm.uge',
        song_name="Example",
        artist="TBB",
        tempo=6,
        num_patterns=2,
        sequence=[0, 1, 0, 1],
        patterns_data=my_patterns
    )
