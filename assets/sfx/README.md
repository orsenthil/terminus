# Sound effects

Drop files here named exactly as below. `.ogg` is preferred; a `.wav` with the same name
also works. Missing files are silent (one warning per cue). No code changes are needed.
Filenames are defined in `AUDIO_CUES` in `game/settings.py`.

Looping cues are started while an action is held and stopped when it ends, so they should
loop seamlessly.

| File | Used for | Loops? | Suggested length / mood |
|------|----------|--------|-------------------------|
| `jump.ogg` | Player jumps | No | 0.1-0.2 s. Light whoosh. |
| `land.ogg` | Player lands | No | < 0.1 s. Soft sand thump. |
| `pickup.ogg` | Collecting a sand pile (+5 s) | No | 0.2 s. Glittery chime. |
| `borrow_loop.ogg` | While holding Shift to borrow | Yes | ~1 s seamless loop. Rushing sand with an uneasy undertone. |
| `interest_tick.ogg` | Debt grows by 10% (every 10 s) | No | 0.2-0.4 s. Coin-like clink, slightly ominous. |
| `flip_glass.ogg` | Flipping a pedestal hourglass | No | 0.2 s. Glass-and-wood turn. |
| `gate_open.ogg` | A gate opens | No | 0.3-0.6 s. Stone grinding down. |
| `gate_close.ogg` | A gate closes | No | 0.3-0.6 s. Stone slam. |
| `lock_start.ogg` | Starting a timer lock | No | 0.1-0.2 s. Click. |
| `lock_success.ogg` | Timer lock opens | No | 0.5-1 s. Satisfying chime. |
| `lock_fail.ogg` | Timer lock resets | No | 0.3-0.5 s. Dull buzz. |
| `shrine_pour_loop.ogg` | While holding E at a shrine to repay | Yes | ~1 s seamless loop. Sand pouring. |
| `collector_hit.ogg` | The Collector touches you | No | 0.5 s. Cold, heavy impact. |
| `death.ogg` | Player dies | No | 0.5-1 s. Sand scattering. |
| `menu_move.ogg` | Moving the menu selection | No | < 0.1 s. Tick. |
| `menu_select.ogg` | Choosing a menu item / starting | No | 0.1-0.2 s. Confirm blip. |

## Placeholders

`uv run python tools/make_placeholder_sfx.py` writes simple sine-wave beeps as `<cue>.wav`
here for testing sound timing. They are placeholders only and are git-ignored; real
`.ogg` files with the same name take precedence.
