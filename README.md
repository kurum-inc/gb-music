# gb-music

A Claude Code / Cowork skill for generating Game Boy music (.uge) and sound effects (.sav).

Programmatically generate BGM and SFX compatible with GB Studio 4.x using Python scripts.

## Features

- **BGM Generation** (.uge) — hUGETracker v6 format with genre, key, and tempo control
- **SFX Generation** (.sav) — FX Hammer format, up to 60 effects per file
- **Audio Conversion** — Convert MP3/M4A/WAV to Game Boy audio using librosa

## Install

### Claude Code / Cowork

Clone into your project's `.claude/skills/` directory:

```bash
git clone https://github.com/kurum-inc/gb-music.git .claude/skills/gb-music
```

Or download and extract the `.skill` file:

```bash
unzip gb-music.skill -d .claude/skills/gb-music
```

## Usage

Just ask Claude naturally:

- "Create a Hawaiian BGM"
- "Make bowling sound effects"
- "Convert this MP3 to Game Boy audio"
- "Generate a game over jingle"

## Supported Genres

| Genre | Example Key | Tempo |
|-------|-------------|-------|
| Beach / Hawaiian | C, F major | 6-8 |
| Rock / Band | A, E minor | 4-5 |
| Tropical | F major | 6-7 |
| Shooting | E minor | 3-4 |
| Swimming | F minor | 4 |
| Boss Battle | D minor | 3-4 |
| Bowling / Funk | Eb major | 5 |
| Game Over | A minor | 5-10 |

## File Structure

```
gb-music/
├── SKILL.md              # Skill definition (read by Claude)
├── README.md             # This file
├── scripts/
│   ├── uge_template.py   # UGE generation template
│   ├── sav_template.py   # SAV generation template + common SFX patterns
│   └── audio_to_uge.py   # Audio-to-UGE converter
└── references/
    ├── uge_format.md     # UGE v6 binary format specification
    └── sav_format.md     # FX Hammer SAV format specification
```

## Requirements

- Python 3.8+
- librosa (only for audio conversion): `pip install librosa`

## Compatibility

- GB Studio 4.x
- hUGETracker v6 format
- FX Hammer .sav format

## License

MIT
