# Making the music for Terminus

A step-by-step guide to making all seven music tracks with free tools. You don't need to read
music or own an instrument. The whole job takes about 2–4 hours.

> **Theme to keep in mind:** Terminus is the place where you can borrow time to accomplish a
> particular task. In the end you repay the time debt and set yourself free.
> The music should move from *calm and mysterious* → *uneasy when in debt* → *free and warm*
> at the end.

---

## What you are making

Seven files, all in `assets/music/`:

| # | File | When it plays | Loops? | Length | Mood |
|---|------|---------------|--------|--------|------|
| 1 | `level_calm.ogg` | During every level | Yes | 1–2 min | Steady, curious, moving forward |
| 2 | `level_debt.ogg` | On top of `level_calm`, louder the more you owe | Yes | **Exactly the same as #1** | Tense, uneasy, ticking |
| 3 | `title.ogg` | Title screen | Yes | 1–2 min | Calm, mysterious, a slow tick |
| 4 | `win.ogg` | "Free." screen after level 5 | Yes | 1–2 min | Warm, relieved, resolved |
| 5 | `level_complete.ogg` | Reaching a level's exit | No | 2–4 s | Bright, rising |
| 6 | `game_over.ogg` | Dying | No | 2–4 s | Falling, hollow |
| 7 | `collector_near.ogg` | The Collector gets close | No | 1–3 s | Sharp, eerie |

The game already knows these names. Put a correctly named file in `assets/music/` and it
plays; leave one out and that moment is silent. **You can add them one at a time.**

**Most important:** #1 and #2 must be exactly the same length and tempo. The game starts
them at the same instant and fades #2 in as your debt grows, so they have to line up bar for
bar. Step 4 shows how.

**Suggested order:** #1 and #2 first (you hear them the most), then #5, #6, #7 (quick), then
#3 and #4.

---

## Step 1: Rules check (PyWeek)

- Music you make **during the challenge week** is fine.
- If you use anything made before the week (a sample pack, someone else's song), it must be
  public domain or under a Creative Commons or open-source licence, and published **at least
  30 days before** the challenge started. Write its source and licence in `README.md`.
- BeepBox songs you write yourself are your own work.

## Step 2: Get the tools (free)

1. **BeepBox** — https://www.beepbox.co — a song maker that runs in your browser. Nothing to
   install.
2. **Audacity** — https://www.audacityteam.org — to trim, set the volume, and save as `.ogg`.
   Install it.

## Step 3: Learn BeepBox in 5 minutes

- The grid is your song. **Rows = channels** (instruments); **columns = bars**. Each cell
  holds a *pattern* number; 0 means silence.
- **Click a cell and draw notes** in the piano roll that appears below it. Click to add a
  note, click again to remove it, and drag to make it longer.
- Right-hand panel:
  - **Scale:** set to **Minor** for everything except the win track. It keeps every note in
    tune, so you can't play a "wrong" note.
  - **Key:** choose **D** for all tracks, so they sound like one game.
  - **Tempo:** beats per minute (BPM).
  - **Instrument:** per channel. Try "chip wave", "FM" or "harmonics", and a drum-set
    preset on the drum channel.
- **Loop bar:** the highlighted range at the top of the grid is what loops when exported.
  Make it cover the whole song.
- **Save your work:** BeepBox keeps the whole song in the page's web address. Bookmark it or
  copy the URL into a text file after every track. Also use **File → Export → .json** as a
  backup.

## Step 4: Make `level_calm` and `level_debt` (together)

### 4a. The calm track

1. Open a new BeepBox song. Set **Key: D**, **Scale: Minor**, **Tempo: 100**.
2. Set the **song length to 16 bars**, using the song-length setting in BeepBox's menus or by
   extending the grid until it has 16 columns. At 100 BPM that's about 38 seconds, which
   loops fine. Write down the tempo and length. **Do not change either after this point.**
3. Channel 1, **bass**: a simple repeating line, one or two notes per bar, played low.
   Example: D for 2 bars, then F, then C, then back to D.
4. Channel 2, **melody**: a short, gentle 4-bar phrase. Repeat it, with a small change the
   second time.
5. Channel 3, **pad or chords**: long, soft notes that follow the bass. Optional.
6. Drum channel: a soft, steady beat. A kick on beats 1 and 3, a light hi-hat on every beat.
   This is the "clock ticking" feel.
7. Make sure the **loop bar covers all 16 bars**.
8. Listen through the loop point: the last bar should flow back into the first without a
   jump.
9. **File → Export → .wav**. Save it as `level_calm.wav`.
10. Copy the URL into your notes as "level_calm".

### 4b. The debt layer (made from the calm track)

1. Keep the same song open (you saved its URL, so the calm version is safe). **Don't touch
   the tempo or the song length.**
2. **Remove the calm parts:** set every cell in channels 1–3 and the calm drum channel to
   **0**. Muting a channel is not enough, because it may still be included in the export.
   The export must *not* contain the calm parts, because the game plays them already.
3. Add new channels for tension:
   - a **low drone**: one very long, low note (D) that holds for the whole song, with an
     "FM" or distorted instrument
   - **uneasy notes**: occasional short notes one step above the calm melody's notes, which
     clash on purpose
   - **faster ticking**: a hi-hat or clicking sound on every half-beat, which feels like
     time running out
   - optionally, a heartbeat: two low kicks close together, once per bar
4. Keep it **thin**. It only has to sound right *on top of* the calm track, not on its own.
5. To check how both sound together, open the calm song's URL in a second browser tab and
   press play in both tabs at the same moment. It should feel like the same song turned
   anxious. (You'll hear it properly in the game in Step 8.)
6. **File → Export → .wav**. Save it as `level_debt.wav`.
7. Save the URL as "level_debt".

> Both exports must be exactly the same length. BeepBox guarantees this if you didn't change
> the tempo or song length between them.

## Step 5: Make the three short stings

These play once and don't loop. For each one, open a new song with **Key: D** and the tempo
shown, make it 1–2 bars long, and in the export dialog **turn off looping** (set the loop
count to 1) so it doesn't repeat.

| File | Tempo | What to write | Instrument idea |
|------|-------|---------------|-----------------|
| `level_complete.wav` | 120 | Four quick notes climbing up (D, F, A, high D), then hold the last one | bright chip wave or bell |
| `game_over.wav` | 80 | Four slow notes falling down (A, F, D, low A), with the last one long | soft "harmonics" or organ |
| `collector_near.wav` | 90 | One sharp chord of three close, clashing notes (D, E♭, E), held for 1 bar, plus one low drum hit | FM or distorted, with reverb up |

## Step 6: Make `title` and `win`

### `title` (calm, mysterious)
1. **Key: D**, **Scale: Minor**, **Tempo: 70**, 16–24 bars.
2. A slow bass and a sparse melody with lots of space between notes.
3. Add a quiet clock tick: a soft click on every beat.
4. Loop bar across the whole song, then **Export → .wav** as `title.wav`.
5. **Shortcut:** reuse your calm track. Open its URL, slow it to 70 BPM, and remove the
   drums except a soft tick. Save it as a new song.

### `win` (free, warm)
1. **Key: D**, **Scale: Major**. The switch to major is what makes it sound like freedom.
   **Tempo: 90**, 16 bars.
2. Reuse the calm melody's shape, but in major: open the calm song, change **Scale to
   Major**, and the same notes become hopeful.
3. Add a warm pad (long chords) and a gentle, unhurried beat.
4. Loop bar across the whole song, then **Export → .wav** as `win.wav`.

## Step 7: Finish every file in Audacity

Do this for each `.wav`:

1. **File → Open** the `.wav`.
2. **Trim silence at the start:** zoom in (Ctrl/Cmd + 1). If there's silence before the
   first sound, select it and press Delete. Stings must start instantly.
3. **For the looping tracks** (`level_calm`, `level_debt`, `title`, `win`), don't trim the
   end: BeepBox exports exact loop lengths. Turn on **Transport → Loop Play** (or
   Shift + Space) and listen to the join. You shouldn't hear a gap or click.
4. **Set the volume:** select all (Ctrl/Cmd + A), then **Effect → Volume and
   Compression → Normalize**, with "Normalize peak amplitude to **-1.0 dB**".
   - **Exception:** normalize `level_debt` to **-3.0 dB**. It plays on top of the calm
     track, so it should be a little quieter.
5. **File → Export Audio**:
   - Format: **Ogg Vorbis**
   - Quality: **5**
   - Channels: stereo is fine
   - Filename: **exactly** as in the table, for example `level_calm.ogg`
   - Folder: `assets/music/` inside the game folder
6. If Audacity asks for metadata, you can leave it empty.

Your folder should end up like this:

```
assets/music/
  collector_near.ogg
  game_over.ogg
  level_calm.ogg
  level_complete.ogg
  level_debt.ogg
  title.ogg
  win.ogg
```

(The game also accepts `.wav` with the same names if you skip conversion, but `.ogg` files
are much smaller to upload.)

## Step 8: Test in the game

```
uv run run_game.py
```

When the game starts, the terminal prints one line per missing file:

```
[audio] missing music/title.ogg, playing silence
```

When your seven tracks are in place, none of the `music/` lines appear.

Where to hear each track:

| Track | How to trigger it |
|-------|-------------------|
| `title` | Start the game |
| `level_calm` | Start level 1 |
| `level_debt` | Level 2: hold **Shift** to borrow a lot. The music should turn tense, and relax again when the debt is repaid. |
| `collector_near` | Level 2: borrow, then stand still until the Collector gets close |
| `level_complete` | Reach any level's exit |
| `game_over` | Walk into red spikes |
| `win` | Finish level 5. Quick test: solve both locks and walk out owing nothing. |

Tips:
- **M** mutes and unmutes everything while you test.
- If `level_debt` sounds out of sync, the two exports have different lengths. Re-export both
  from the same BeepBox song without changing the tempo or length.
- If a track is too loud or quiet compared with the others, re-normalize it (Step 7.4) a few
  dB lower or higher.

## Step 9: Give yourself credit

In `README.md`, under **Credits and licenses**, add a line like:

```
- Music: composed during PyWeek by <your name> using BeepBox; mixed and exported with Audacity.
```

Add a separate line for anything you didn't make yourself, with its source and licence.

---

## Out of time? The minimum

1. Make just **`level_calm`**. That covers most of the playing time.
2. Then **`level_debt`**, which is the one that makes borrowing *feel* dangerous.
3. Then **`title`**.

The other four are nice extras. The game is fine without them.
