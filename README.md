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

## Credits and licenses

- Developer: Senthil Kumaran
- Testers: Siddhartha S Obla and Saharsha S Obla
- Inspired by Isaac Asimov's *Foundation* stories and the world of Terminus. This is a fan
  tribute made for PyWeek, not affiliated with the Asimov estate or publishers.
