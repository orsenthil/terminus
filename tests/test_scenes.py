"""Scene lifecycle: every transition cleans up its handlers, nodes and GUI."""

import pytest

from game import scenes
from game import settings as S
from game.main import Game


@pytest.fixture(scope="module")
def game(headless_base):
    g = Game(headless_base)
    held = set()
    g.held = lambda action: action in held
    g.test_held = held
    return g


def run(game, frames=5):
    for _ in range(frames):
        game.base.taskMgr.step()


def settle(game):
    """Advance until any pending fade/transition completes."""
    for _ in range(200):
        run(game, 1)
        if game.pending is None and game.fade_dir == 0:
            return


def snapshot(base):
    return {
        "render nodes": base.render.findAllMatches("**").getNumPaths(),
        "render2d nodes": base.render2d.findAllMatches("**").getNumPaths(),
        "events": sorted(base.messenger.getEvents()),
        "tasks": sorted(t.name for t in base.taskMgr.getAllTasks()),
    }


def test_transitions_do_not_leak(game):
    base = game.base
    game.start(scenes.TitleScene(game))
    settle(game)
    baseline = snapshot(base)

    for index in range(len(S.LEVEL_ORDER)):
        game.change_scene(lambda i=index: scenes.PlayScene(game, i))
        settle(game)
        scene = game.scene
        assert isinstance(scene, scenes.PlayScene)
        # play a little, pause, unpause, die, respawn, restart
        game.test_held.add("right")
        run(game, 30)
        game.test_held.clear()
        base.messenger.send("escape")
        run(game, 2)
        assert scene.state == "paused"
        base.messenger.send("escape")
        run(game, 2)
        assert scene.state == "play"
        scene.life.top = 0.0
        run(game, 2)
        assert scene.state == "dead"
        base.messenger.send("space")
        run(game, 2)
        assert scene.state == "play"
        base.messenger.send("r")
        settle(game)
        assert game.scene is not scene
        game.change_scene(lambda: scenes.TitleScene(game))
        settle(game)
        assert snapshot(base) == baseline, f"leak after level {index}"


def test_measure_level_guide_leads_to_solution(game):
    """Level 5's locks open with the intended method (sloppy human timing), and the
    step-by-step hint only appears when H is pressed."""
    base = game.base
    game.change_scene(lambda: scenes.PlayScene(game, 4))
    settle(game)
    sc = game.scene

    def at(x):
        sc.player.teleport(x, 3)
        run(game, 1)

    def wait(seconds):
        run(game, int(round(seconds * 60)))

    def press_e():
        base.messenger.send("e")
        run(game, 1)

    # Lock 0: 7 seconds with the 7s glass.
    at(13.5)
    press_e()
    wait(0.4)
    at(15.5)
    press_e()
    assert sc.guide_progress[0][0] == 2
    wait(7.0)
    press_e()
    assert sc.locks[0].logic.solved

    # Lock 1: 15 seconds with the 7s and 11s glasses. Only the problem shows until H.
    at(32.5)
    run(game, 1)
    assert sc.hud.guide_key[0].startswith("Lock: measure 15 seconds")
    assert sc.hud.guide_key[1] == ()  # no steps visible
    base.messenger.send("h")
    run(game, 1)
    assert len(sc.hud.guide_key[1]) == 4  # the hint's steps are visible
    base.messenger.send("h")
    run(game, 1)
    assert sc.hud.guide_key[1] == ()
    at(34.5)
    press_e()  # flip the 11s
    wait(0.4)
    at(30.5)
    press_e()  # flip the 7s
    assert sc.guide_progress[1][0] == 1
    at(32.5)
    while sc.glasses[1].running:
        run(game, 1)
    wait(0.3)
    press_e()  # start when the 7s empties
    assert sc.guide_progress[1][0] == 2
    while sc.glasses[2].running:
        run(game, 1)
    wait(0.3)
    at(34.5)
    press_e()  # re-flip the 11s when it empties (4 s later)
    assert sc.guide_progress[1][0] == 3
    at(32.5)
    while sc.glasses[2].running:
        run(game, 1)
    wait(0.3)
    press_e()  # stop when it empties again: 4 + 11 = 15
    assert sc.locks[1].logic.solved
    run(game, 2)
    assert all(g.open for g in sc.gates)
    game.change_scene(lambda: scenes.TitleScene(game))
    settle(game)


def test_intro_pages_lead_to_the_first_level(game):
    base = game.base
    game.change_scene(lambda: scenes.TitleScene(game))
    settle(game)
    baseline = snapshot(base)
    base.messenger.send("space")
    settle(game)
    intro = game.scene
    assert isinstance(intro, scenes.IntroScene)
    for page in range(len(scenes.INTRO_PAGES)):
        assert intro.page == page
        base.messenger.send("space")
        run(game, 2)
    settle(game)
    assert isinstance(game.scene, scenes.LevelIntroScene)
    assert game.scene.index == 0
    # Esc skips the intro straight to level 1.
    game.change_scene(lambda: scenes.IntroScene(game))
    settle(game)
    base.messenger.send("escape")
    settle(game)
    assert isinstance(game.scene, scenes.LevelIntroScene)
    game.change_scene(lambda: scenes.TitleScene(game))
    settle(game)
    assert snapshot(base) == baseline


def test_credits_roll_to_the_end_and_return_to_title(game):
    base = game.base
    game.change_scene(lambda: scenes.TitleScene(game))
    settle(game)
    baseline = snapshot(base)
    base.messenger.send("c")
    settle(game)
    credits = game.scene
    assert isinstance(credits, scenes.CreditsScene)
    # Let the whole roll play out: it returns to the title on its own.
    seconds = (2.3 + credits.length) / scenes.S.CREDITS_SCROLL_SPEED + 2
    run(game, int(seconds * 60))
    settle(game)
    assert isinstance(game.scene, scenes.TitleScene)
    # From the win screen, Space rolls the credits; Space again skips them.
    game.change_scene(lambda: scenes.WinScene(game))
    settle(game)
    base.messenger.send("space")
    settle(game)
    assert isinstance(game.scene, scenes.CreditsScene)
    base.messenger.send("space")
    settle(game)
    assert isinstance(game.scene, scenes.TitleScene)
    assert snapshot(base) == baseline
