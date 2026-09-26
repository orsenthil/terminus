"""The player must stay visible whichever way it faces."""

from panda3d.core import GeomVertexReader, NodePath

from game.player import PlayerController, PlayerView


def front_facing_triangles(np):
    """Count vertices whose world-space normal points at the camera (camera looks along +Y)."""
    count = 0
    mat = np.getMat(np.getTop())
    for geom in np.node().getGeoms():
        reader = GeomVertexReader(geom.getVertexData(), "normal")
        while not reader.isAtEnd():
            if mat.xformVec(reader.getData3()).y < -0.5:
                count += 1
    return count


def visible_meshes(view):
    return [m for m in (view.mesh_right, view.mesh_left) if not m.isHidden()]


def test_player_visible_facing_both_ways():
    root = NodePath("root")
    view = PlayerView(root)
    pc = PlayerController(5.5, 3.0)
    for facing in (1, -1, 1, -1):
        pc.facing = facing
        view.update(1 / 60, pc)
        meshes = visible_meshes(view)
        assert len(meshes) == 1
        assert not view.root.isHidden()
        # Front faces of every box (cloak, boots, head, hood, belt) must face the camera.
        assert front_facing_triangles(meshes[0]) >= 5 * 6


def test_player_is_in_front_of_level_objects():
    root = NodePath("root")
    view = PlayerView(root)
    view.update(1 / 60, PlayerController(5.5, 3.0))
    # Level tiles, pedestals, locks, gates and bridges all sit at y >= -0.5.
    assert view.root.getY() + 0.3 < -0.5
