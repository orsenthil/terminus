# Terminus

A PyWeek entry for the theme **"Borrowed Time"**.

> Terminus is the place where you can borrow time to accomplish a particular task. In the
> end you repay the time debt back and set yourself free.

The name comes from Terminus, the planet at the edge of the galaxy in Isaac Asimov's
*Foundation* stories. Your life is a water clock that is always draining. To get through each
task you can borrow time from your future, but the debt grows with interest and something
comes to collect it. The final door opens only when every borrowed second is repaid.

A short 2.5D side-scrolling platformer in five levels, built with Python and Panda3D. It is
set on an icy world at the edge of the galaxy: frost over dark volcanic rock, sulfur vents,
a dim red dwarf sun, four moons, and a cold sea of islands where a small colony keeps its
Archives. All geometry is generated in code; there are no image or model files.

## Running the game

**Windows or Linux, no Python needed:** download the standalone build for your system,
unzip it, and run `Terminus.exe` (Windows) or `./Terminus` (Linux).

- Windows may show a SmartScreen warning because the game isn't code-signed. Click
  "More info", then "Run anyway".
- On Linux you need working OpenGL drivers, which any desktop has.

**Any system (Windows, macOS, Linux) from the source release**, with Python 3.10 or newer:

    pip install -r requirements.txt
    python run_game.py

On macOS and Linux you may need `python3` and `pip3` instead. Using a virtual environment
keeps things tidy:

    python3 -m venv .venv
    source .venv/bin/activate            # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python run_game.py

**With [uv](https://docs.astral.sh/uv/)** (what the developer uses):

    uv sync                      # install everything
    uv run run_game.py           # play the game

The only dependency is Panda3D 1.10, which has ready-made packages for Windows, macOS
(Intel and Apple Silicon) and Linux (x86-64 and ARM) on Python 3.10 to 3.14.

## Controls

| Action | Keys |
|--------|------|
| Move | Arrow keys / A, D |
| Jump | Space / W / Up (release early for a shorter jump) |
| Borrow time | hold Left Shift |
| Interact (flip a water clock, repay at an Archive, use a lock) | E (hold at an Archive) |
| Hint (on a puzzle lock) | H |
| Restart level | R |
| Mute | M |
| Pause | Esc (Esc on the title screen quits) |

Key bindings can be changed in `KEYS` in `game/settings.py`.

## How to play

After the title screen, a short introduction tells you about Terminus and your goal
(Space to continue, Esc to skip).

- **The water clock** (top left) is your life. It drains at one second per second. When it
  runs out, you die and go back to the last Archive.
- **Sulfur crystals**, the planet's only wealth, each buy you 5 seconds.
- **Borrow:** hold Shift to pour 5 seconds per second into your water clock. Every borrowed
  second becomes debt, and every 10 seconds the debt grows by 10%. The orange ring counts
  down to the next interest tick. You can owe at most 60 seconds.
- **The Collector** appears whenever you owe time and drifts toward you through walls. The
  more you owe, the faster it moves. If it touches you, it takes time equal to your whole
  debt, and that can kill you.
- **Archives** (the colony's stone terminals) are checkpoints. Stand at one and hold E to
  pay off debt with your own time.
- **Pedestal water clocks:** press E to flip one. Linked doors stay open, and linked ice
  bridges stay solid, while its water is falling. Flipping a half-drained clock gives you
  back only the water that has already fallen.
- **Timer locks** show a length of time as tally marks. Press E to start one and E again to
  stop it. It opens if you stop it within one second of the target. No clock is shown
  anywhere, so you measure the time with the water clocks, which flash "EMPTY!" when they run
  out. Near a lock, the top of the screen shows only the problem (for example, "measure 15
  seconds using a 7s and an 11s water clock"). Press H to toggle a step-by-step hint.
- In the last level, the exit only opens if you owe nothing.
- **Day and night:** Terminus circles a dim red dwarf, so days are short and nights are
  long. At night it gets dark, four moons and the faint band of the galaxy come out, you
  carry a lantern, and the water in every clock glows purple.
- **Running out of time:** below 15 seconds of life, the whole screen pulses red, faster
  as the water runs out. That's your cue to borrow (hold Shift) or find sulfur crystals.

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

### Making a release

Put the final music and sound files in `assets/` first (`tools/make_audio.sh` or your own),
then:

    uv run pytest && uvx ruff check . && uv run python tools/check_levels.py
    uv run python tools/make_release.py                    # dist/terminus-<ver>-source.zip
    uv run --group build python setup.py bdist_apps        # Windows and Linux builds

`bdist_apps` uses Panda3D's own packager to build standalone games from any OS:
`dist/terminus-<ver>_win_amd64.zip` and `dist/terminus-<ver>_manylinux2014_x86_64.tar.gz`.
Upload those plus the source zip to PyWeek.

macOS players use the source release. Apps made by Panda3D 1.10's packager are rejected by
Apple Silicon's code-signing checks, and any downloaded Mac app that isn't notarized (which
needs a paid Apple Developer account) is blocked by Gatekeeper anyway.

`.github/workflows/tests.yml` runs the tests on Windows, macOS and Linux (Python 3.10 and
3.12) on every push, if the project is hosted on GitHub.

### Layout

    run_game.py          entry point (checks Python and Panda3D, then calls game.main.main)
    game/settings.py     every tunable number, colour, key binding and audio filename
    game/hourglass.py    Hourglass logic (no Panda3D)
    game/debt.py         debt and compound interest logic (no Panda3D)
    game/physics.py      AABB vs tile-grid collision (no Panda3D)
    game/player.py       movement controller + player model
    game/collector.py    the Collector
    game/level.py        map loading and level geometry
    game/backdrop.py     parallax sky and horizon (red dwarf, moons, galaxy, islands, domes)
    game/daynight.py     day / night cycle and its palette (no Panda3D)
    game/objects.py      sulfur crystals, archives, water clocks, gates, bridges, locks, exits, signs
    game/effects.py      pooled particles (water, snow, steam) and screen shake
    game/hud.py          HUD
    game/scenes.py       title, Terminus introduction, level intro, play (pause/death), win
    game/audio.py        AudioManager (works with no audio files present)
    game/main.py         ShowBase setup, fixed-timestep update task, scene fades
    data/levels/         tile maps (.txt) and metadata (.json)
    tools/               level checker, audio generator, release builder
    setup.py             standalone Windows/Linux builds (Panda3D build_apps)
    tests/               pytest suite

### Level format

Each level is `data/levels/<id>.txt` plus `<id>.json`. In the map file, row 0 is the
**top** of the level, and each character is one tile:

| Char | Meaning |
|------|---------|
| `#` | solid |
| `.` | empty |
| `P` | player start (exactly one) |
| `S` | sulfur crystal (+5 s) |
| `H` | Archive (checkpoint, repay debt) |
| `G` | pedestal glass |
| `D` | gate (connected `D` tiles form one gate) |
| `B` | ice bridge (connected `B` tiles form one bridge; solid while its clock runs) |
| `L` | timer lock |
| `E` | exit (at least one) |
| `^` | burning sulfur pit (instant death) |
| `?` | sign |

The JSON file holds `name`, `subtitle`, `start_time`, `allow_borrow`,
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

- Developer: Senthil Kumaran
- Testers: Siddhartha S Obla and Saharsha S Obla
- Inspired by Isaac Asimov's *Foundation* stories and the world of Terminus. This is a fan
  tribute made for PyWeek, not affiliated with the Asimov estate or publishers.
- The in-game credits (press C on the title screen, or finish the game) also list the open
  source libraries and tools used.
- Code, level design and all procedural visuals: original work made for this PyWeek. AI
  coding tools were used during development (the PyWeek rules allow this).
- [Panda3D](https://www.panda3d.org/) (Modified BSD license) is the only runtime dependency.
- Font: [Julius Sans One](https://fonts.google.com/specimen/Julius+Sans+One) by Luciano
  Vergara, LatinoType (2012), under the SIL Open Font License 1.1. The font and its licence are in
  `assets/fonts/` (`JuliusSansOne-Regular.ttf`, `OFL.txt`).
- No third-party art, music or sound is included yet. Record any audio added later here,
  with its source and license (it must be CC or OSI licensed, or public domain, and
  published at least 30 days before the challenge).
