"""
Audio-to-UGE Converter
Converts MP3/M4A/WAV to Game Boy .uge format via librosa analysis.

Requirements: pip install librosa --break-system-packages

Usage:
    python audio_to_uge.py input.mp3 output.uge [--key auto] [--tempo auto]
"""
import sys
import json
import numpy as np

try:
    import librosa
except ImportError:
    print("librosa not installed. Run: pip install librosa --break-system-packages")
    sys.exit(1)


def analyze_audio(filepath):
    """
    Analyze audio file and return musical properties.
    Returns dict with: tempo, key, key_scale, chords, melody_midi
    """
    y, sr = librosa.load(filepath, sr=22050, mono=True)
    duration = len(y) / sr
    print(f"Duration: {duration:.1f}s")

    # Tempo detection
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    tempo = float(tempo)
    print(f"Tempo: {tempo:.1f} BPM")

    # Key detection via chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
    chroma_mean = chroma.mean(axis=1)
    names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

    # Try major and minor keys, pick best fit
    major_template = [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1]  # Ionian
    minor_template = [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0]  # Aeolian

    best_key = 0
    best_score = -1
    best_mode = 'major'

    for root in range(12):
        for mode, template in [('major', major_template), ('minor', minor_template)]:
            rotated = template[-root:] + template[:-root]
            score = sum(chroma_mean[i] * rotated[i] for i in range(12))
            if score > best_score:
                best_score = score
                best_key = root
                best_mode = mode

    key_name = f"{names[best_key]} {best_mode}"
    print(f"Key: {key_name}")

    # Scale pitch classes for the detected key
    template = major_template if best_mode == 'major' else minor_template
    scale_pcs = set()
    for i in range(12):
        if template[i]:
            scale_pcs.add((best_key + i) % 12)

    # Chord progression (one chord per measure)
    quarter = 60.0 / tempo
    measure = quarter * 4
    num_measures = int(duration / measure)

    chords = []
    for m in range(min(num_measures, 32)):
        start = int(m * measure * sr / len(y) * chroma.shape[1])
        end = int((m + 1) * measure * sr / len(y) * chroma.shape[1])
        end = min(end, chroma.shape[1])
        if start >= end:
            break
        seg = chroma[:, start:end].mean(axis=1)
        root = int(np.argmax(seg))
        chords.append(names[root])
    print(f"Chords ({len(chords)} measures): {' '.join(chords[:8])}...")

    # Melody extraction via HPSS + pyin
    y_h, _ = librosa.effects.hpss(y, margin=3.0)
    f0, voiced, vprob = librosa.pyin(
        y_h,
        fmin=float(librosa.note_to_hz('A3')),
        fmax=float(librosa.note_to_hz('C6')),
        sr=sr, frame_length=2048
    )
    times = librosa.times_like(f0, sr=sr)

    # Sample at 8th-note grid
    eighth = quarter / 2
    num_eighths = int(duration / eighth)
    melody_midi = []

    for i in range(min(num_eighths, 128)):
        t = i * eighth
        mask = (times >= t) & (times < t + eighth)
        vals = f0[mask]
        vals = vals[~np.isnan(vals)]
        if len(vals) >= 3:
            midi = float(np.median(librosa.hz_to_midi(vals)))
            # Snap to scale
            midi_int = int(round(midi))
            for d in range(3):
                for s in (0, 1, -1):
                    if (midi_int + s * d) % 12 in scale_pcs:
                        midi_int = midi_int + s * d
                        break
                else:
                    continue
                break
            melody_midi.append(midi_int)
        else:
            melody_midi.append(None)

    # Fill None gaps and normalize octave
    last = None
    filled = []
    for n in melody_midi:
        if n is None:
            n = last
        filled.append(n)
        if n is not None:
            last = n

    # Octave normalization
    valid = [v for v in filled if v is not None]
    if valid:
        import statistics
        med = int(statistics.median(valid))
        for i, v in enumerate(filled):
            if v is None:
                continue
            while v - med > 7:
                v -= 12
            while med - v > 7:
                v += 12
            filled[i] = v

    print(f"Melody: {sum(1 for x in filled if x is not None)}/{len(filled)} notes extracted")

    return {
        'tempo': tempo,
        'key': key_name,
        'key_root': best_key,
        'key_mode': best_mode,
        'scale_pcs': list(scale_pcs),
        'chords': chords,
        'melody_midi': filled,
        'duration': duration,
    }


def midi_to_uge(midi_note):
    """Convert MIDI note to UGE note value. MIDI 48 = C3 = UGE 0."""
    if midi_note is None:
        return 90  # REST
    v = midi_note - 48
    if v < 0:
        v = v % 12
    if v > 71:
        v = 71
    return v


def tempo_to_ticks(bpm):
    """Convert BPM to appropriate UGE ticks_per_row value."""
    # With 4 rows per beat: ticks = 900 / bpm
    ticks = int(round(900 / bpm))
    return max(3, min(10, ticks))


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python audio_to_uge.py input.mp3 output.uge")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    result = analyze_audio(input_file)

    # Save analysis
    analysis_file = output_file.replace('.uge', '_analysis.json')
    with open(analysis_file, 'w') as f:
        json.dump({k: v for k, v in result.items() if k != 'melody_midi'}, f, indent=2)
    print(f"Analysis saved to {analysis_file}")
    print(f"\nUse this data to generate {output_file} with uge_template.py")
    print(f"Suggested ticks_per_row: {tempo_to_ticks(result['tempo'])}")
