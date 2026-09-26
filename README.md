# Terminus

A PyWeek entry for the theme **"Borrowed Time"**.

> Terminus is the place where you can borrow time to accomplish a particular task. In the
> end you repay the time debt back and set yourself free.

The name comes from Terminus, the planet at the edge of the galaxy in Isaac Asimov's
*Foundation* stories. Your life is an hourglass that is always draining. To get through each
task you can borrow sand from your future, but the debt grows with interest and something
comes to collect it. The final door opens only when every borrowed second is repaid.

A short 2.5D side-scrolling platformer in five levels, built with Python and Panda3D. It is
set in a clockwork world of clock towers, turning gears and floating islands. All geometry
is generated in code; there are no image or model files.

## Running the game

With [uv](https://docs.astral.sh/uv/) (recommended):

    uv sync                      # install everything
    uv run run_game.py           # play the game

Without uv (Python 3.10+):

    pip install -r requirements.txt && python run_game.py

The project targets Python 3.12 (see `.python-version`). Panda3D 1.10 wheels exist for
Windows, macOS and Linux.

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow keys / A, D |
| Jump | Space / W / Up (release early for a shorter jump) |
| Borrow time | hold Left Shift |
| Interact (flip a glass, repay at a shrine, use a lock) | E (hold at a shrine) |
| Restart level | R |
| Mute | M |
| Pause | Esc (Esc on the title screen quits) |

Key bindings can be changed in `KEYS` in `game/settings.py`.

## How to play

- **The hourglass** (top left) is your life. It drains at one second per second. When it
  runs out, you die and go back to the last shrine.
- **Golden sand piles** add 5 seconds.
- **Borrow:** hold Shift to pour 5 seconds per second into your hourglass. Every borrowed
  second becomes debt, and every 10 seconds the debt grows by 10%. The orange ring counts
  down to the next interest tick. You can owe at most 60 seconds.
- **The Collector** appears whenever you owe time and drifts toward you through walls. The
  more you owe, the faster it moves. If it touches you, it takes sand equal to your whole
  debt, and that can kill you.
- **Shrines** are checkpoints. Stand at one and hold E to pay off debt with your own sand.
- **Pedestal glasses:** press E to flip one. Linked doors stay open, and linked sand bridges
  stay solid, while its sand is falling. Flipping a half-drained glass gives you back only
  the sand that has already fallen.
- **Timer locks** show a length of time as tally marks. Press E to start one and E again to
  stop it. It opens if you stop it within one second of the target. No clock is shown
  anywhere, so you measure the time with the glasses. A step-by-step guide at the top of
  the screen walks you through each lock, and glasses flash "EMPTY!" when they run out.
- In the last level, the exit only opens if you owe nothing.
- **Day and night:** the world turns from day to night and back as you play. At night it
  gets dark, you carry a lantern, and every hourglass's sand glows purple.
- **Running out of time:** below 15 seconds of life, the whole screen pulses red, faster
  as the sand runs out. That's your cue to borrow (hold Shift) or find golden sand.

## Development

    uv run pytest                # run tests (headless; no window opens)
    uvx ruff check .             # lint
    uvx ruff format .            # format
    uv run python tools/check_levels.py        # check every level's exit is reachable
    uv run python tools/make_placeholder_sfx.py  # optional placeholder beeps (see below)

After changing dependencies, regenerate the pip fallback file:

    uv export --no-hashes --no-dev --format requirements-txt > requirements.txt

(`--no-dev` leaves pytest out, because players don't need it.)

Set `BT_DEBUG=1` to show the frame-rate meter.

### Layout

    run_game.py          entry point (checks Python and Panda3D, then calls game.main.main)
    game/settings.py     every tunable number, colour, key binding and audio filename
    game/hourglass.py    Hourglass logic (no Panda3D)
    game/debt.py         debt and compound interest logic (no Panda3D)
    game/physics.py      AABB vs tile-grid collision (no Panda3D)
    game/player.py       movement controller + player model
    game/collector.py    the Collector
    game/level.py        map loading and level geometry
    game/backdrop.py     clockwork parallax sky (sun/moon clocks, towers, gears, islands)
    game/daynight.py     day / night cycle and its palette (no Panda3D)
    game/objects.py      pickups, shrines, pedestal glasses, gates, bridges, locks, exits, signs
    game/effects.py      pooled sand particles and screen shake
    game/hud.py          HUD
    game/scenes.py       title, level intro, play (pause and death overlays), win
    game/audio.py        AudioManager (works with no audio files present)
    game/main.py         ShowBase setup, fixed-timestep update task, scene fades
    data/levels/         tile maps (.txt) and metadata (.json)
    tools/               level checker, placeholder SFX generator
    tests/               pytest suite

### Level format

Each level is `data/levels/<id>.txt` plus `<id>.json`. In the map file, row 0 is the
**top** of the level, and each character is one tile:

| Char | Meaning |
|------|---------|
| `#` | solid |
| `.` | empty |
| `P` | player start (exactly one) |
| `S` | sand pickup (+5 s) |
| `H` | shrine (checkpoint, repay debt) |
| `G` | pedestal glass |
| `D` | gate (connected `D` tiles form one gate) |
| `B` | sand bridge (connected `B` tiles form one bridge; solid while its glass runs) |
| `L` | timer lock |
| `E` | exit (at least one) |
| `^` | spikes (instant death) |
| `?` | sign |

The JSON file holds `name`, `subtitle`, `start_sand`, `allow_borrow`,
`exit_requires_no_debt`, and lists matched to map objects **in reading order** (top to
bottom, then left to right):

- `glasses`: `{"capacity": 7, "gates": [0], "bridges": []}` for each `G`
- `locks`: `{"target": 15, "gates": [1]}` for each `L`. Optional: `"glasses": [1, 2]`
  (reset when an attempt fails), `"title"`, and `"guide"`: a list of
  `{"text": "...", "on": ["flip:1", "flip:2"]}` steps shown on screen. A step completes
  once all its events have happened: `flip:N` / `empty:N` for glass N, and `start` / `stop`
  for this lock.
- `signs`: one string for each `?`

Gate and bridge indices count connected groups in reading order of each group's first tile.
The level order is `LEVEL_ORDER` in `settings.py`.

## Audio

The game runs with no audio files at all. Each missing cue prints one warning and then
stays silent. To add sound, drop correctly named `.ogg` files (or `.wav`) into
`assets/music/` and `assets/sfx/`; no code changes are needed. The expected files are
listed in [assets/music/README.md](assets/music/README.md) and
[assets/sfx/README.md](assets/sfx/README.md). For a step-by-step guide to making the music,
see [music.md](music.md).

**Quickest route:** `tools/make_audio.sh` synthesises all 23 sounds and music tracks with
ffmpeg (no other tools, no samples) and writes them straight into `assets/`. The tracks
are simple but complete, and you can edit the notes and formulas in the script and re-run
it.

`tools/make_placeholder_sfx.py` generates simple sine-wave **placeholder** beeps
(`assets/sfx/*.wav`) using only the standard library. They exist only for testing sound
timing and are git-ignored.

## Credits and licenses

- Code, level design and all procedural visuals: original work made for this PyWeek. AI
  coding tools were used during development (the PyWeek rules allow this).
- [Panda3D](https://www.panda3d.org/) (Modified BSD license) is the only runtime dependency.
- The UI uses Panda3D's built-in default font.
- No third-party art, music or sound is included yet. Record any audio added later here,
  with its source and license (it must be CC or OSI licensed, or public domain, and
  published at least 30 days before the challenge).
