"""All tunable constants for Terminus live here.

Nothing in this module imports Panda3D, so the pure-logic modules and tests can use it.
"""

import os
import sys

# --- Paths -------------------------------------------------------------------------------


def _find_root():
    """Where assets/ and data/ live: the project folder when run from source; next to the
    executable in a standalone Windows/Linux build; Contents/Resources in a macOS app."""
    if not getattr(sys, "frozen", False):
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    for candidate in (exe_dir, os.path.join(exe_dir, os.pardir, "Resources")):
        if os.path.isdir(os.path.join(candidate, "data")):
            return os.path.normpath(candidate)
    return exe_dir


ROOT_DIR = _find_root()
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
LEVELS_DIR = os.path.join(ROOT_DIR, "data", "levels")
# Julius Sans One (SIL Open Font License, see assets/fonts/OFL.txt) for all game text.
FONT_PATH = os.path.join(ASSETS_DIR, "fonts", "JuliusSansOne-Regular.ttf")
FONT_BOLDNESS = 0.5  # extra stroke thickness (the font has only one thin weight)
TEXT_WIDTH = 1.15  # horizontal stretch applied to all text, for a wider look

# --- Window / debug ----------------------------------------------------------------------
WINDOW_TITLE = "Terminus"
WINDOW_SIZE = (1280, 720)
DEBUG = bool(os.environ.get("BT_DEBUG"))

# --- Simulation --------------------------------------------------------------------------
PHYSICS_STEP = 1.0 / 120.0
MAX_FRAME_DT = 0.1  # clamp long frames so the accumulator can't spiral
FADE_TIME = 0.3  # scene transition fade (each direction)
LEVEL_INTRO_TIME = 2.0
CREDITS_SCROLL_SPEED = 0.11  # aspect2d units per second (the screen is 2 units tall)

# --- Camera ------------------------------------------------------------------------------
VIEW_WIDTH_TILES = 30.0
CAMERA_LOOKAHEAD = 3.0  # tiles ahead of the player in the facing direction
CAMERA_DAMPING = 6.0  # higher = snappier follow
CAMERA_Z_OFFSET = 2.5  # camera sits a little above the player
CAMERA_Y = -60.0
SHAKE_DECAY = 3.0
SHAKE_MAX = 0.6

# --- Player movement ---------------------------------------------------------------------
PLAYER_WIDTH = 0.7
PLAYER_HEIGHT = 0.9
RUN_SPEED = 8.0
GROUND_ACCEL = 70.0
GROUND_FRICTION = 60.0
AIR_ACCEL = 45.0
AIR_FRICTION = 12.0
GRAVITY = 40.0
JUMP_VELOCITY = 16.5
JUMP_CUT_MULTIPLIER = 0.45  # vz multiplier when jump is released early
MAX_FALL_SPEED = 26.0
COYOTE_TIME = 0.1
JUMP_BUFFER_TIME = 0.1
SQUASH_AMOUNT = 0.25
SQUASH_RECOVER = 10.0

# --- Life hourglass ----------------------------------------------------------------------
START_TIME = 60.0  # seconds of water in the life clock at the start of a level
LIFE_MAX = 99.0  # the top chamber can't hold more than this
PICKUP_TIME = 5.0  # seconds a sulfur crystal buys

# --- Debt --------------------------------------------------------------------------------
BORROW_RATE = 5.0  # seconds of time per second of holding borrow
INTEREST_RATE = 0.10
INTEREST_PERIOD = 10.0
DEBT_CAP = 60.0

# --- Collector ---------------------------------------------------------------------------
COLLECTOR_BASE_SPEED = 3.0
COLLECTOR_DEBT_FACTOR = 0.075  # extra tiles/s per second of debt
COLLECTOR_RADIUS = 0.6
COLLECTOR_FADE_SPEED = 2.0
COLLECTOR_STING_DISTANCE = 5.0
COLLECTOR_STING_REARM = 8.0
COLLECTOR_SPAWN_MARGIN = 1.5  # tiles beyond the left edge of the view
COLLECTOR_MIN_SPAWN_DISTANCE = 14.0  # never appear closer than this to the player

# --- Archives (checkpoints where you repay) ----------------------------------------------
ARCHIVE_POUR_RATE = 10.0
ARCHIVE_MIN_LIFE = 1.0  # repaying stops before it would kill you
ARCHIVE_RADIUS = 1.2

# --- Interactables -----------------------------------------------------------------------
INTERACT_RADIUS = 1.4
PICKUP_RADIUS = 0.7
LOCK_TOLERANCE = 1.0  # seconds either side of the target
PIT_HEIGHT = 0.45  # height of the deadly zone above a sulfur pit tile

# --- Particles ---------------------------------------------------------------------------
PARTICLE_POOL = 400
SNOWFALL_RATE = 9.0  # flakes per second drifting across the view
VENT_STEAM_RATE = 5.0  # steam puffs per second from each nearby vent
PARTICLE_GRAVITY = 12.0

# --- Colours (r, g, b, a) ----------------------------------------------------------------
# Terminus: ice and frost over dark basalt, sulfur the only colour in the rock.
FROST_TOP = (0.9, 0.94, 1.0, 1)  # snow on the upper face of exposed ground
ICE = (0.6, 0.7, 0.8, 1)  # front of the exposed ground
ROCK = (0.3, 0.29, 0.34, 1)  # basalt
ROCK_DEEP = (0.2, 0.19, 0.24, 1)
SULFUR = (0.95, 0.85, 0.2, 1)
SULFUR_GLOW = (1.0, 0.95, 0.55, 1)
GOLD = (1.0, 0.82, 0.3, 1)  # UI accent (titles, lock marks)
GOLD_GLOW = (1.0, 0.9, 0.5, 1)
STONE = (0.5, 0.52, 0.58, 1)
GATE_COLOR = (0.35, 0.25, 0.45, 1)
BRIDGE_COLOR = (0.55, 0.8, 1.0, 0.9)  # ice bridges
PIT_MOLTEN = (0.42, 0.07, 0.04, 1)  # molten sulfur runs dark red when hot
PIT_SURFACE = (0.95, 0.35, 0.1, 1)  # its glowing surface
PIT_FLAME = (0.3, 0.55, 1.0, 0.75)  # burning sulfur has a blue flame
PIT_FLAME_CORE = (0.75, 0.88, 1.0, 0.9)
PLAYER_CLOAK = (0.2, 0.55, 0.85, 1)
PLAYER_SKIN = (0.95, 0.8, 0.65, 1)
COLLECTOR_COLOR = (0.05, 0.0, 0.08, 0.8)
DEBT_RED = (0.9, 0.15, 0.1, 1)
TEXT_COLOR = (1.0, 0.93, 0.75, 1)
SNOW = (0.92, 0.95, 1.0, 1)
STEAM = (0.85, 0.85, 0.8, 0.6)
DEBT_TINT_MAX_ALPHA = 0.45
DEBT_TINT_COLOR = (0.08, 0.0, 0.16, 1)  # debt darkens the world with a violet shadow

# --- Day / night -------------------------------------------------------------------------
# A red dwarf sun: short, dim, reddish days and long, dark nights under four moons.
DAY_LENGTH = 20.0  # seconds of daylight (including dusk)
NIGHT_LENGTH = 40.0  # seconds of night (including dawn)
DUSK_LENGTH = 4.0  # blend time at each end of the day
DAY_SKY = (0.5, 0.36, 0.4, 1)
DUSK_SKY = (0.3, 0.12, 0.18, 1)
NIGHT_SKY = (0.01, 0.01, 0.035, 1)
DAY_AMBIENT = (0.55, 0.52, 0.6, 1)
DAY_SUN = (0.85, 0.55, 0.45, 1)  # red dwarf light
NIGHT_AMBIENT = (0.14, 0.13, 0.25, 1)
NIGHT_SUN = (0.18, 0.2, 0.38, 1)  # moonlight
DAY_LAYER_SCALE = (1.0, 0.92, 0.95, 1)
NIGHT_LAYER_SCALE = (0.3, 0.3, 0.5, 1)
WATER_DAY = (0.45, 0.8, 1.0, 1)  # the water in every clock
WATER_NIGHT = (0.72, 0.42, 1.0, 1)  # glows purple at night
LANTERN_COLOR = (1.0, 0.8, 0.5, 1)  # the player's light at night
LANTERN_ATTENUATION = (1.0, 0.0, 0.05)

# --- Running out of time -----------------------------------------------------------------
LOW_TIME = 15.0  # below this many seconds the whole screen starts turning red
LOW_TIME_TINT = (0.75, 0.0, 0.0, 1)
LOW_TIME_MAX_ALPHA = 0.38

# --- Input bindings ----------------------------------------------------------------------
# Panda3D button names. Movement / held actions are polled, the rest are events.
KEYS = {
    "left": ["arrow_left", "a"],
    "right": ["arrow_right", "d"],
    "jump": ["space", "w", "arrow_up"],
    "borrow": ["lshift", "shift"],
    "interact": ["e"],
    "restart": ["r"],
    "mute": ["m"],
    "pause": ["escape"],
    "menu_up": ["arrow_up", "w"],
    "menu_down": ["arrow_down", "s"],
    "confirm": ["space", "enter"],
    "hint": ["h"],
    "credits": ["c"],
}

# --- Audio -------------------------------------------------------------------------------
# Every cue maps to a file under assets/. .ogg is preferred; a .wav with the same stem is
# accepted too. Missing files are silent (one warning per cue).
AUDIO_CUES = {
    # music
    "title": "music/title.ogg",
    "level_calm": "music/level_calm.ogg",
    "level_debt": "music/level_debt.ogg",
    "collector_near": "music/collector_near.ogg",
    "level_complete": "music/level_complete.ogg",
    "game_over": "music/game_over.ogg",
    "win": "music/win.ogg",
    # sfx
    "jump": "sfx/jump.ogg",
    "land": "sfx/land.ogg",
    "pickup": "sfx/pickup.ogg",
    "borrow_loop": "sfx/borrow_loop.ogg",
    "interest_tick": "sfx/interest_tick.ogg",
    "flip_glass": "sfx/flip_glass.ogg",
    "gate_open": "sfx/gate_open.ogg",
    "gate_close": "sfx/gate_close.ogg",
    "lock_start": "sfx/lock_start.ogg",
    "lock_success": "sfx/lock_success.ogg",
    "lock_fail": "sfx/lock_fail.ogg",
    "shrine_pour_loop": "sfx/shrine_pour_loop.ogg",
    "collector_hit": "sfx/collector_hit.ogg",
    "death": "sfx/death.ogg",
    "menu_move": "sfx/menu_move.ogg",
    "menu_select": "sfx/menu_select.ogg",
}
# Looping music tracks (everything else under music/ is a one-shot sting).
MUSIC_LOOPS = {"title", "level_calm", "level_debt", "win"}
# Tracks started in sync with a base track, initially silent.
MUSIC_LAYERS = {"level_calm": ["level_debt"]}
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.7
SFX_VOLUME = 0.9

# --- Levels ------------------------------------------------------------------------------
LEVEL_ORDER = ["01_thaw", "02_the_loan", "03_interest", "04_flip", "05_measure"]
