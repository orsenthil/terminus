"""All tunable constants for Borrowed Time live here.

Nothing in this module imports Panda3D, so the pure-logic modules and tests can use it.
"""

import os

# --- Paths -------------------------------------------------------------------------------
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
LEVELS_DIR = os.path.join(ROOT_DIR, "data", "levels")

# --- Window / debug ----------------------------------------------------------------------
WINDOW_TITLE = "Borrowed Time"
WINDOW_SIZE = (1280, 720)
DEBUG = bool(os.environ.get("BT_DEBUG"))

# --- Simulation --------------------------------------------------------------------------
PHYSICS_STEP = 1.0 / 120.0
MAX_FRAME_DT = 0.1  # clamp long frames so the accumulator can't spiral
FADE_TIME = 0.3  # scene transition fade (each direction)
LEVEL_INTRO_TIME = 2.0

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
START_SAND = 60.0
LIFE_MAX = 99.0  # the top chamber can't hold more than this
PICKUP_SAND = 5.0

# --- Debt --------------------------------------------------------------------------------
BORROW_RATE = 5.0  # seconds of sand per second of holding borrow
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

# --- Shrines -----------------------------------------------------------------------------
SHRINE_POUR_RATE = 10.0
SHRINE_MIN_LIFE = 1.0  # pouring stops before it would kill you
SHRINE_RADIUS = 1.2

# --- Interactables -----------------------------------------------------------------------
INTERACT_RADIUS = 1.4
PICKUP_RADIUS = 0.7
LOCK_TOLERANCE = 1.0  # seconds either side of the target
SPIKE_HEIGHT = 0.45

# --- Particles ---------------------------------------------------------------------------
PARTICLE_POOL = 220
PARTICLE_GRAVITY = 12.0

# --- Colours (r, g, b, a) ----------------------------------------------------------------
SKY_COLOR = (0.05, 0.07, 0.2, 1)
SAND_TOP = (0.93, 0.78, 0.45, 1)
SAND_BODY = (0.72, 0.52, 0.3, 1)
SAND_DEEP = (0.5, 0.34, 0.2, 1)
GOLD = (1.0, 0.82, 0.3, 1)
GOLD_GLOW = (1.0, 0.9, 0.5, 1)
STONE = (0.55, 0.47, 0.4, 1)
GLASS = (0.75, 0.88, 1.0, 0.25)
GATE_COLOR = (0.35, 0.25, 0.45, 1)
BRIDGE_COLOR = (1.0, 0.8, 0.35, 0.9)
SPIKE_COLOR = (0.9, 0.1, 0.1, 1)  # red: danger, day or night
PLAYER_CLOAK = (0.2, 0.55, 0.85, 1)
PLAYER_SKIN = (0.95, 0.8, 0.65, 1)
COLLECTOR_COLOR = (0.05, 0.0, 0.08, 0.8)
DEBT_RED = (0.9, 0.15, 0.1, 1)
TEXT_COLOR = (1.0, 0.93, 0.75, 1)
DEBT_TINT_MAX_ALPHA = 0.45
DEBT_TINT_COLOR = (0.08, 0.0, 0.16, 1)  # debt darkens the world with a violet shadow

# --- Day / night -------------------------------------------------------------------------
DAY_LENGTH = 35.0  # seconds of daylight (including dusk)
NIGHT_LENGTH = 25.0  # seconds of night (including dawn)
DUSK_LENGTH = 5.0  # blend time at each end of the day
DAY_SKY = (0.42, 0.68, 0.95, 1)
DUSK_SKY = (0.85, 0.42, 0.38, 1)
NIGHT_SKY = (0.02, 0.02, 0.07, 1)
DAY_AMBIENT = (0.6, 0.58, 0.62, 1)
DAY_SUN = (0.8, 0.72, 0.55, 1)
NIGHT_AMBIENT = (0.14, 0.12, 0.26, 1)
NIGHT_SUN = (0.14, 0.15, 0.32, 1)
DAY_LAYER_SCALE = (1.0, 0.95, 1.0, 1)
NIGHT_LAYER_SCALE = (0.28, 0.26, 0.48, 1)
SAND_DAY = GOLD
SAND_NIGHT = (0.72, 0.42, 1.0, 1)  # hourglass sand glows purple at night
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
LEVEL_ORDER = ["01_sand", "02_the_loan", "03_interest", "04_flip", "05_measure", "06_settlement"]
