#!/usr/bin/env bash
# Make every sound and music track for Terminus from the command line, using only ffmpeg.
#
#   tools/make_audio.sh            # writes assets/sfx/*.ogg and assets/music/*.ogg
#   tools/make_audio.sh some/dir   # writes some/dir/sfx and some/dir/music instead
#
# Needs ffmpeg (macOS: `brew install ffmpeg`; Debian/Ubuntu: `sudo apt install ffmpeg`).
# Everything is synthesised from maths (sine waves, noise, envelopes), so it is all original
# work you can credit to yourself. Tweak the numbers and re-run as often as you like.
set -euo pipefail

OUT=${1:-assets}
SR=44100
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
FF=(ffmpeg -hide_banner -loglevel error -y)
mkdir -p "$OUT/sfx" "$OUT/music"

# --- helpers -----------------------------------------------------------------------------

# gen OUT.wav SECONDS 'EXPRESSION' [extra ffmpeg filters]
# EXPRESSION is an ffmpeg aevalsrc formula in t (seconds): sin(), exp(), random(0), if()...
gen() {
  "${FF[@]}" -f lavfi -i "aevalsrc=exprs='$3':d=$2:s=$SR:c=mono${4:+,$4}" "$1"
}

# Pick the best Ogg Vorbis encoder this ffmpeg has.
# (ffmpeg's built-in fallback encoder only does stereo.)
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q libvorbis; then
  VORBIS=(-c:a libvorbis -q:a 5)
  STEREO_ONLY=0
else
  VORBIS=(-c:a vorbis -strict experimental)
  STEREO_ONLY=1
fi

# ogg IN.wav OUT.ogg CHANNELS : peak-limit, then encode.
ogg() {
  local ch=$3
  [ "$STEREO_ONLY" = 1 ] && ch=2
  "${FF[@]}" -i "$1" -af "alimiter=limit=0.9:level=disabled" -ac "$ch" -ar $SR "${VORBIS[@]}" "$2"
  echo "  made $2"
}

# Note name -> frequency in Hz (bash 3 has no dictionaries, so a case statement).
freq() {
  case $1 in
    A1) echo 55.00 ;; Bb1) echo 58.27 ;; C2) echo 65.41 ;; D2) echo 73.42 ;; E2) echo 82.41 ;;
    F2) echo 87.31 ;; G2) echo 98.00 ;; A2) echo 110.00 ;; Bb2) echo 116.54 ;; B2) echo 123.47 ;;
    C3) echo 130.81 ;; D3) echo 146.83 ;; E3) echo 164.81 ;; F3) echo 174.61 ;; Fs3) echo 185.00 ;;
    G3) echo 196.00 ;; A3) echo 220.00 ;; Bb3) echo 233.08 ;; B3) echo 246.94 ;; C4) echo 261.63 ;;
    Cs4) echo 277.18 ;; D4) echo 293.66 ;; Eb4) echo 311.13 ;; E4) echo 329.63 ;; F4) echo 349.23 ;;
    Fs4) echo 369.99 ;; G4) echo 392.00 ;; A4) echo 440.00 ;; Bb4) echo 466.16 ;; B4) echo 493.88 ;;
    C5) echo 523.25 ;; Cs5) echo 554.37 ;; D5) echo 587.33 ;; Eb5) echo 622.25 ;; E5) echo 659.25 ;;
    Fs5) echo 739.99 ;; G5) echo 783.99 ;; A5) echo 880.00 ;; *) echo "unknown note $1" >&2; exit 1 ;;
  esac
}

# Instrument voices. @F = frequency (Hz), @D = note length (s), @V = volume.
# Every voice fades out over its last 5 ms, so notes never click when they are cut.
END='min(1,(@D-t)*200)'
PLUCK="@V*(sin(2*PI*@F*t)+0.4*sin(4*PI*@F*t)+0.15*sin(6*PI*@F*t))*min(1,t*300)*exp(-4*t)*$END"
BELL="@V*(sin(2*PI*@F*t)+0.5*sin(2*PI*@F*2.76*t)*exp(-6*t))*min(1,t*400)*exp(-3*t)*$END"
BASS="@V*(sin(2*PI*@F*t)+0.35*sin(4*PI*@F*t))*min(1,t*100)*exp(-1.2*t)*$END"
PAD="@V*(sin(2*PI*@F*t)+0.5*sin(2*PI*@F*1.5*t)+0.3*sin(2*PI*@F*2.005*t))*min(1,t*3)*min(1,(@D-t)*3)"
KICK="@V*sin(2*PI*(45*t+(110/25)*(1-exp(-25*t))))*exp(-9*t)*$END"
HAT="@V*(2*random(0)-1)*exp(-70*t)*$END"

# seq OUT.wav BEAT_SECONDS VOICE VOLUME "NOTE:BEATS NOTE:BEATS ..."
# Plays the notes one after another. "-" is a rest; "x" is an unpitched hit (drums).
seq_notes() {
  local out=$1 beat=$2 voice=$3 vol=$4 notes=$5 list="$TMP/list_$RANDOM.txt" i=0
  : > "$list"
  for item in $notes; do
    local name=${item%%:*} beats=${item##*:}
    local dur
    dur=$(awk "BEGIN{printf \"%.4f\", $beat*$beats}")
    local seg="$TMP/seg_$RANDOM$RANDOM$i.wav"
    if [ "$name" = "-" ]; then
      gen "$seg" "$dur" "0"
    else
      local f=1
      [ "$name" = "x" ] || f=$(freq "$name")
      local e=${voice//@F/$f}
      e=${e//@D/$dur}
      e=${e//@V/$vol}
      gen "$seg" "$dur" "$e"
    fi
    echo "file '$seg'" >> "$list"
    i=$((i + 1))
  done
  "${FF[@]}" -f concat -safe 0 -i "$list" -c copy "$out"
}

# repeat_str N "STRING" : the string N times (for drum patterns).
repeat_str() {
  local s="" k
  for ((k = 0; k < $1; k++)); do s="$s $2"; done
  echo "$s"
}

# mix OUT.wav IN1.wav IN2.wav ... : sum the layers (all the same length).
mix() {
  local out=$1
  shift
  local args=() k=0
  for f in "$@"; do
    args+=(-i "$f")
    k=$((k + 1))
  done
  "${FF[@]}" "${args[@]}" -filter_complex "amix=inputs=$k:normalize=0:duration=longest" "$out"
}

# =========================================================================================
echo "Sound effects -> $OUT/sfx"
S=$TMP/sfx
mkdir -p "$S"

# jump: quick rising chirp 300 -> 750 Hz
gen "$S/jump.wav" 0.15 "0.5*sin(2*PI*(300*t+(450/0.3)*t*t))*min(1,t*400)*exp(-12*t)"
# land: soft low thud
gen "$S/land.wav" 0.09 "0.7*sin(2*PI*(60*t+(60/40)*(1-exp(-40*t))))*exp(-35*t)+0.15*(2*random(0)-1)*exp(-60*t)"
# pickup: two bright notes (B5 then E6)
gen "$S/pickup.wav" 0.3 "0.4*if(lt(t,0.07),sin(2*PI*988*t),sin(2*PI*1319*t)*exp(-9*(t-0.07)))*min(1,t*500)"
# borrow_loop: 1 s seamless uneasy hum with a hiss (whole-number Hz, so it loops cleanly)
gen "$S/borrow_loop.wav" 1.0 "0.22*(sin(2*PI*110*t)+0.7*sin(2*PI*113*t)+0.4*sin(2*PI*330*t))*(0.65+0.35*sin(2*PI*4*t))+0.07*(2*random(0)-1)"
# interest_tick: a slightly sour coin clink
gen "$S/interest_tick.wav" 0.35 "0.3*(sin(2*PI*1318*t)+sin(2*PI*1397*t)+0.5*sin(2*PI*659*t))*min(1,t*800)*exp(-10*t)"
# flip_glass: woody knock plus a quick glassy chirp
gen "$S/flip_glass.wav" 0.2 "0.4*sin(2*PI*(700*t+(500/0.4)*t*t))*exp(-14*t)+0.4*sin(2*PI*180*t)*exp(-40*t)"
# gate_open: stone grinding (low rumble)
gen "$S/gate_open.wav" 0.6 "(0.6*(2*random(0)-1)+0.5*sin(2*PI*48*t))*min(1,t*20)*min(1,(0.6-t)*8)" "lowpass=f=350"
# gate_close: heavy slam
gen "$S/gate_close.wav" 0.45 "0.9*sin(2*PI*(40*t+(90/18)*(1-exp(-18*t))))*exp(-8*t)+0.5*(2*random(0)-1)*exp(-25*t)" "lowpass=f=900"
# lock_start: click
gen "$S/lock_start.wav" 0.06 "0.5*(sin(2*PI*2000*t)+sin(2*PI*1100*t))*exp(-90*t)"
# lock_success: rising chime G5 B5 D6 G6
gen "$S/lock_success.wav" 0.9 "0.3*if(lt(t,0.1),sin(2*PI*784*t),if(lt(t,0.2),sin(2*PI*988*t),if(lt(t,0.3),sin(2*PI*1175*t),sin(2*PI*1568*t)*exp(-4*(t-0.3)))))*min(1,t*500)"
# lock_fail: low sour buzz
gen "$S/lock_fail.wav" 0.45 "0.25*(sgn(sin(2*PI*110*t))+sgn(sin(2*PI*116*t)))*exp(-4*t)*min(1,(0.45-t)*50)" "lowpass=f=1500"
# shrine_pour_loop: 1 s seamless pouring sand (hiss with a soft shimmer)
gen "$S/shrine_pour_loop.wav" 1.0 "0.26*(2*random(0)-1)*(0.75+0.25*sin(2*PI*6*t))+0.06*sin(2*PI*880*t)*(0.5+0.5*sin(2*PI*2*t))"
# collector_hit: cold heavy impact with an echo
gen "$S/collector_hit.wav" 0.7 "0.8*sin(2*PI*(35*t+(80/10)*(1-exp(-10*t))))*exp(-5*t)+0.3*(sin(2*PI*233*t)+sin(2*PI*247*t))*exp(-6*t)" "aecho=0.8:0.6:120:0.4"
# death: long falling chirp scattering into spray
gen "$S/death.wav" 0.9 "0.4*sin(2*PI*(600*t-(520/1.8)*t*t))*exp(-3*t)+0.2*(2*random(0)-1)*exp(-5*t)"
# menu_move: tiny tick
gen "$S/menu_move.wav" 0.05 "0.35*sin(2*PI*1200*t)*exp(-60*t)"
# menu_select: two-tone confirm
gen "$S/menu_select.wav" 0.16 "0.35*if(lt(t,0.06),sin(2*PI*880*t),sin(2*PI*1320*t))*min(1,t*500)*exp(-12*t)"

for f in "$S"/*.wav; do
  ogg "$f" "$OUT/sfx/$(basename "${f%.wav}").ogg" 1
done

# =========================================================================================
echo "Music -> $OUT/music"
M=$TMP/music
mkdir -p "$M"

# --- level_calm + level_debt: D minor, 100 BPM (beat = 0.6 s), 16 bars = 38.4 s ----------
# Both are exactly 64 beats long, so the debt layer stays in sync on top of the calm one.
BEAT=0.6
seq_notes "$M/calm_bass.wav" $BEAT "$BASS" 0.45 "\
D2:2 D2:2 D2:2 A1:2 Bb1:2 Bb1:2 Bb1:2 F2:2 F2:2 F2:2 F2:2 C2:2 C2:2 C2:2 C2:2 G2:2 \
D2:2 D2:2 D2:2 A1:2 Bb1:2 Bb1:2 Bb1:2 F2:2 G2:2 G2:2 G2:2 D2:2 A1:2 A1:2 A1:2 E2:2"
seq_notes "$M/calm_melody.wav" $BEAT "$PLUCK" 0.22 "\
A4:1 F4:1 D4:1 F4:1  E4:1 F4:1 A4:2  Bb4:1 A4:1 F4:1 D4:1  F4:4 \
C5:1 A4:1 F4:1 A4:1  G4:1 A4:1 C5:2  E4:1 G4:1 C5:1 G4:1  E4:4 \
A4:1 F4:1 D4:1 F4:1  E4:1 F4:1 A4:1 D5:1  D5:1 Bb4:1 F4:1 Bb4:1  A4:4 \
G4:1 Bb4:1 D5:1 Bb4:1  A4:1 G4:1 F4:2  E4:1 A4:1 Cs5:1 A4:1  E4:4"
seq_notes "$M/calm_kick.wav" $BEAT "$KICK" 0.5 "$(repeat_str 32 'x:2')"
seq_notes "$M/calm_tick.wav" $BEAT "$HAT" 0.12 "$(repeat_str 64 'x:1')"
mix "$M/level_calm.wav" "$M/calm_bass.wav" "$M/calm_melody.wav" "$M/calm_kick.wav" "$M/calm_tick.wav"

# The debt layer: a low drone, clashing notes, fast ticking and a heartbeat.
# Drone frequencies are whole cycles per 38.4 s (e.g. 2819/38.4 Hz) so the loop is seamless.
gen "$M/debt_drone.wav" 38.4 "0.16*(sin(2*PI*(2819/38.4)*t)+0.6*sin(2*PI*(2838/38.4)*t)+0.3*sin(2*PI*(5638/38.4)*t))*(0.7+0.3*sin(2*PI*(10/38.4)*t))*min(1,t*50)*min(1,(38.4-t)*50)"
seq_notes "$M/debt_clash.wav" $BEAT "$BELL" 0.12 "$(repeat_str 8 '-:3 Eb5:1 -:2 E4:1 -:1')"
seq_notes "$M/debt_ticks.wav" $BEAT "$HAT" 0.22 "$(repeat_str 128 'x:0.5')"
seq_notes "$M/debt_heart.wav" $BEAT "$KICK" 0.55 "$(repeat_str 16 'x:0.5 x:0.5 -:3')"
mix "$M/level_debt.wav" "$M/debt_drone.wav" "$M/debt_clash.wav" "$M/debt_ticks.wav" "$M/debt_heart.wav"

# --- title: slow and mysterious, D minor, 75 BPM (beat = 0.8 s), 16 bars = 51.2 s --------
BEAT=0.8
seq_notes "$M/title_pad.wav" $BEAT "$PAD" 0.12 "\
D3:8 Bb2:8 F3:8 A2:8 D3:8 G2:8 Bb2:8 A2:8"
seq_notes "$M/title_melody.wav" $BEAT "$BELL" 0.3 "\
A4:2 -:2 F4:2 -:2  D5:3 -:1 A4:4  F4:2 -:2 A4:2 C5:2  E4:4 -:4 \
A4:2 -:2 F4:2 D4:2  Bb4:3 -:1 A4:4  G4:2 F4:2 E4:2 -:2  A3:4 -:4"
seq_notes "$M/title_tick.wav" $BEAT "$HAT" 0.07 "$(repeat_str 64 'x:1')"
mix "$M/title.wav" "$M/title_pad.wav" "$M/title_melody.wav" "$M/title_tick.wav"

# --- win: free at last, D MAJOR, 100 BPM (beat = 0.6 s), 16 bars = 38.4 s ----------------
BEAT=0.6
seq_notes "$M/win_bass.wav" $BEAT "$BASS" 0.4 "\
D2:4 D2:4 G2:4 G2:4 B2:4 B2:4 A2:4 A2:4 D2:4 D2:4 G2:4 G2:4 E2:4 A2:4 D2:4 D2:4"
seq_notes "$M/win_pad.wav" $BEAT "$PAD" 0.05 "\
D3:8 G3:8 B2:8 A2:8 D3:8 G3:8 E3:4 A2:4 D3:8"
seq_notes "$M/win_melody.wav" $BEAT "$PLUCK" 0.22 "\
Fs4:1 A4:1 D5:2  E5:1 D5:1 A4:2  G4:1 B4:1 D5:1 B4:1  A4:4 \
B4:1 D5:1 Fs5:2  E5:1 D5:1 B4:2  Cs5:1 E5:1 A4:1 Cs5:1  D5:4 \
Fs4:1 A4:1 D5:2  E5:1 Fs5:1 E5:2  D5:1 B4:1 G4:1 B4:1  A4:4 \
G4:1 B4:1 E5:2  Cs5:1 E5:1 A5:2  Fs5:1 E5:1 D5:1 A4:1  D5:4"
seq_notes "$M/win_kick.wav" $BEAT "$KICK" 0.35 "$(repeat_str 16 'x:2 -:2')"
seq_notes "$M/win_tick.wav" $BEAT "$HAT" 0.08 "$(repeat_str 32 '-:1 x:1')"
mix "$M/win.wav" "$M/win_bass.wav" "$M/win_pad.wav" "$M/win_melody.wav" "$M/win_kick.wav" "$M/win_tick.wav"

# --- stings (play once) ------------------------------------------------------------------
# level_complete: bright rising D major arpeggio
seq_notes "$M/lc_notes.wav" 0.12 "$BELL" 0.3 "D4:1 Fs4:1 A4:1 D5:10"
seq_notes "$M/lc_pad.wav" 0.12 "$PAD" 0.06 "D3:13"
mix "$M/level_complete.wav" "$M/lc_notes.wav" "$M/lc_pad.wav"
# game_over: slow falling notes
seq_notes "$M/game_over.wav" 0.35 "$BELL" 0.3 "A4:1 F4:1 D4:1 A3:5"
# collector_near: one sharp clashing chord and a low boom, with an echo
gen "$M/collector_near.wav" 2.0 "0.14*(sin(2*PI*293.66*t)+sin(2*PI*311.13*t)+sin(2*PI*329.63*t))*min(1,t*200)*exp(-1.8*t)+0.7*sin(2*PI*(40*t+(70/12)*(1-exp(-12*t))))*exp(-4*t)" "aecho=0.8:0.7:180:0.35"

for name in level_calm level_debt title win level_complete game_over collector_near; do
  ogg "$M/$name.wav" "$OUT/music/$name.ogg" 2
done

echo "Done. Start the game with: uv run run_game.py"
