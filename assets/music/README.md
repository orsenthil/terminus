# Music

Step-by-step instructions for making these tracks are in [music.md](../../music.md).

Drop files here named exactly as below. `.ogg` is preferred; a `.wav` with the same name
also works. Missing files are fine: the game plays silence for that cue and prints one
warning. No code changes are needed when adding files. Filenames are defined in
`AUDIO_CUES` in `game/settings.py`.

| File | Used for | Loops? | Suggested length / mood |
|------|----------|--------|-------------------------|
| `title.ogg` | Title screen | Yes | 1-2 min. Calm, mysterious desert night; a slow ticking pulse. |
| `level_calm.ogg` | Base gameplay layer, every level | Yes | 1-2 min. Warm, steady, forward-moving. |
| `level_debt.ogg` | Layer played **in sync** with `level_calm`; volume rises with debt (silent at 0 debt, full at the cap) | Yes | **Exactly the same length and tempo as `level_calm.ogg`** so they stay aligned. Tense, dissonant, low strings/percussion that sit on top of the calm layer. |
| `collector_near.ogg` | Sting when the Collector gets within 5 tiles | No | 1-3 s. Sharp, eerie swell. |
| `level_complete.ogg` | Sting on reaching a level's exit | No | 2-4 s. Bright, relieved. |
| `game_over.ogg` | Sting on death | No | 2-4 s. Falling, hollow. |
| `win.ogg` | "Free." screen after the final level (level 5) | Yes | 1-2 min. Resolved, peaceful. |
