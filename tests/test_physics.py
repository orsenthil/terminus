import pytest

from game.physics import Body, TileGrid, move_and_collide


def floor_grid(width=20, height=20):
    return TileGrid(width, height, {(x, 0) for x in range(width)})


def simulate(body, grid, seconds, gravity=40.0, step=1 / 120):
    for _ in range(int(seconds / step)):
        body.vz -= gravity * step
        move_and_collide(body, grid, step)
    return body


def test_lands_on_tile():
    grid = floor_grid()
    body = Body(5.5, 5.0, 0.7, 0.9)
    simulate(body, grid, 2.0)
    assert body.z == pytest.approx(1.0)
    assert body.on_ground
    assert body.vz == 0


def test_hits_wall():
    grid = floor_grid()
    grid.set_solid(10, 1, True)
    body = Body(8.0, 1.0, 0.7, 0.9)
    body.vx = 8.0
    for _ in range(120):
        body.vz = -0.1
        move_and_collide(body, grid, 1 / 120)
    assert body.right == pytest.approx(10.0)
    assert body.hit_wall or body.vx == 0


def test_hits_wall_moving_left():
    grid = floor_grid()
    grid.set_solid(3, 1, True)
    body = Body(6.0, 1.0, 0.7, 0.9)
    body.vx = -8.0
    for _ in range(120):
        move_and_collide(body, grid, 1 / 120)
    assert body.left == pytest.approx(4.0)


def test_hits_ceiling():
    grid = floor_grid()
    grid.set_solid(5, 4, True)
    body = Body(5.5, 1.0, 0.7, 0.9)
    body.vz = 20.0
    move_and_collide(body, grid, 0.2)
    assert body.top == pytest.approx(4.0)
    assert body.hit_ceiling
    assert body.vz == 0


def test_no_tunneling_at_high_speed():
    grid = TileGrid(40, 200, {(x, 0) for x in range(40)})
    body = Body(10.5, 150.0, 0.7, 0.9)
    body.vz = -1000.0  # 1000 tiles/s straight down through a 1-tile floor
    move_and_collide(body, grid, 1.0)
    assert body.z == pytest.approx(1.0)
    assert body.on_ground

    wall = TileGrid(200, 10, {(100, 1)})
    body = Body(10.5, 1.0, 0.7, 0.9)
    body.vx = 5000.0
    move_and_collide(body, wall, 1.0)
    assert body.right == pytest.approx(100.0)


def test_level_edges_are_walls():
    grid = floor_grid(10)
    body = Body(1.0, 1.0, 0.7, 0.9)
    body.vx = -20
    move_and_collide(body, grid, 1.0)
    assert body.left == pytest.approx(0.0)


def test_fits_through_one_tile_gap():
    grid = floor_grid()
    grid.set_solid(6, 2, True)  # ceiling at z=2 above a 1-tile tall tunnel
    body = Body(3.0, 1.0, 0.7, 0.9)
    body.vx = 8
    for _ in range(60):
        move_and_collide(body, grid, 1 / 120)
    assert body.x > 6.5
