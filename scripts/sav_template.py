"""
FX Hammer .sav Sound Effect Generator Template for GB Studio 4.x
Usage: Define effects as frame lists, then call generate_sav().
"""


def generate_sav(filename, effects):
    """
    Generate an FX Hammer .sav file (32,768 bytes).

    Args:
        filename: Output file path
        effects: List of effect dicts:
            {
                'flag': 0x30 (Ch2 pulse only), 0x03 (Ch4 noise only), or 0x33 (both),
                'frames': [(duration, ch2_pan, ch2_vol, ch2_duty, ch2_freq,
                            ch4_pan, ch4_vol, ch4_freq), ...]
            }
            Max 60 effects, max 32 frames per effect.
            Duration 0 = end marker (added automatically).
    """
    buf = bytearray(b'\x00' * 32768)

    # Magic header
    buf[0x009:0x012] = b'FX HAMMER'

    # Channel flags
    for i, ef in enumerate(effects[:60]):
        buf[0x300 + i] = ef['flag']

    # Effect data
    for i, ef in enumerate(effects[:60]):
        base = 0x400 + i * 0x100
        for fi, frame in enumerate(ef['frames'][:32]):
            off = base + fi * 8
            for bi, b in enumerate(frame):
                buf[off + bi] = b & 0xFF
        # Terminator (duration=0) already zeroed

    with open(filename, 'wb') as f:
        f.write(buf)
    print(f"Wrote {filename} ({len(effects)} effects)")


# === Constants ===
PAN_BOTH = 0x22   # Output to both L+R speakers
PAN_NONE = 0x00   # Silent/unused channel

# Volume register: upper nibble = initial volume (0-F), bit3 = direction, lower 3 = sweep pace
# Higher upper nibble = louder. Sweep pace 0 = no envelope change.
VOL_MAX = 0xF8          # Vol 15, no sweep
VOL_LOUD_DECAY = 0xB8   # Vol 11, decay
VOL_MED_DECAY = 0x78    # Vol 7, decay
VOL_QUIET = 0x48        # Vol 4, decay
VOL_SILENT = 0x08       # Nearly silent

# Duty cycle register
DUTY_12 = 0x00   # 12.5% - thin, buzzy
DUTY_25 = 0x40   # 25% - hollow
DUTY_50 = 0x80   # 50% - full square wave (most common)
DUTY_75 = 0xC0   # 75% - same as 25% but inverted

# Frequency: higher byte value = higher pitch (this is the low byte of GB freq register)
# Approximate note mapping:
# 0x40~0x50 = very low | 0x60~0x80 = low-mid | 0x90~0xA0 = mid
# 0xB0~0xC0 = high | 0xD0+ = very high

# Noise frequency: lower value = higher pitch noise
# 0x20 = crash/white noise | 0x30-0x40 = medium | 0x50-0x70 = soft/filtered


# === Common SFX Patterns ===

def sfx_hit(vol=VOL_MAX):
    """Sharp impact sound."""
    return {
        'flag': 0x33,
        'frames': [
            (1, PAN_BOTH, vol, DUTY_50, 0xB0, PAN_BOTH, vol, 0x20),
            (1, PAN_BOTH, 0xC8, DUTY_25, 0xA0, PAN_BOTH, 0xC8, 0x30),
            (1, PAN_BOTH, 0x98, DUTY_50, 0x90, PAN_BOTH, 0x88, 0x40),
            (1, PAN_BOTH, 0x58, DUTY_25, 0x80, PAN_BOTH, 0x48, 0x50),
        ]
    }

def sfx_jump():
    """Ascending pitch sweep."""
    return {
        'flag': 0x30,
        'frames': [(1, PAN_BOTH, 0xF8, DUTY_25, 0x80 + i * 0x10, 0, 0, 0)
                   for i in range(6)]
    }

def sfx_coin():
    """Quick two-tone collect sound."""
    return {
        'flag': 0x33,
        'frames': [
            (2, PAN_BOTH, VOL_MAX, DUTY_50, 0xB8, PAN_BOTH, 0x38, 0x60),
            (2, PAN_BOTH, VOL_MAX, DUTY_50, 0xC8, 0, 0, 0),
            (3, PAN_BOTH, 0xC8, DUTY_50, 0xC8, 0, 0, 0),
            (2, PAN_BOTH, 0x88, DUTY_50, 0xC8, 0, 0, 0),
        ]
    }

def sfx_explosion(length=8):
    """Loud noise burst with decay."""
    frames = []
    for i in range(length):
        vol = max(0x18, 0xF8 - i * 0x20)
        frames.append((2, PAN_BOTH, vol, DUTY_50, 0x60, PAN_BOTH, vol, 0x20 + i * 3))
    return {'flag': 0x33, 'frames': frames}

def sfx_confirm():
    """UI confirmation beep."""
    return {
        'flag': 0x30,
        'frames': [
            (2, PAN_BOTH, VOL_MAX, DUTY_50, 0xA0, 0, 0, 0),
            (4, PAN_BOTH, 0xD8, DUTY_50, 0xB0, 0, 0, 0),
        ]
    }

def sfx_cursor():
    """Subtle cursor movement tick."""
    return {
        'flag': 0x30,
        'frames': [
            (1, PAN_BOTH, 0xA8, DUTY_25, 0xA0, 0, 0, 0),
            (1, PAN_BOTH, 0x68, DUTY_25, 0xA8, 0, 0, 0),
        ]
    }

def sfx_pinpon():
    """Correct answer chime (ピンポーン)."""
    return {
        'flag': 0x30,
        'frames': [
            (8, PAN_BOTH, VOL_MAX, DUTY_50, 0xB0, 0, 0, 0),   # ピン
            (12, PAN_BOTH, 0xD8, DUTY_50, 0xC0, 0, 0, 0),     # ポーン
            (6, PAN_BOTH, 0xA8, DUTY_50, 0xC0, 0, 0, 0),      # fade
            (4, PAN_BOTH, 0x68, DUTY_50, 0xC0, 0, 0, 0),      # tail
        ]
    }


# === Example usage ===
if __name__ == '__main__':
    effects = [
        sfx_hit(),
        sfx_jump(),
        sfx_coin(),
        sfx_explosion(),
        sfx_confirm(),
        sfx_cursor(),
        sfx_pinpon(),
    ]
    generate_sav('/tmp/example_sfx.sav', effects)
