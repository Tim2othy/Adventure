"""Projectiles, shooting through space."""

from pygame import Color
from pygame.math import Vector2 as Vec2
from camera import Camera
from physics import PhysicalObject


class Bullet(PhysicalObject):
    """A triangular bullet."""

    def __init__(self, pos: Vec2, vel: Vec2, color: Color) -> None:
        """Create a new basic Bullet.

        Args:
        ----
            pos (Vec2): Start position
            vel (Vec2): Velocity
            color (Color): Border- and fill-color

        """
        super().__init__(pos, vel, 1.0)
        self.color = Color("black")

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera`.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        camera.draw_circle(self.color, self.pos, 4)
