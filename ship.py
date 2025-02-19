"""Spaceships, shooting through space."""

from __future__ import annotations

import math
import random
from enum import Enum
from typing import TYPE_CHECKING

import pygame
from pygame import Color
from pygame.math import Vector2 as Vec2

from physics import Disk
from projectiles import Bullet

if TYPE_CHECKING:
    from camera import Camera


BULLET_SPEED = 300
HEAD_LENGTH = 3  # relative to radius
HEAD_WIDTH = 3  # relative to radius
ENEMY_SHOOT_RANGE = 400

# How long a ship should glow after taking damage
DAMAGE_INDICATOR_TIME = 0.75
SPEED = 0.5


class Ship(Disk):
    """A basic spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        size: float,
        color: Color,
    ) -> None:
        """Create a new spaceship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density (of disk-body)
            size (float): Radius of disk-body
            color (Color): Material color

        """
        super().__init__(pos, vel, density, size, color)
        self.size: float = size
        self.angle: float = 270
        self.health: float = 10000
        self.projectiles: list[Bullet] = []
        self.gun_cooldown: float = 0
        self.has_trophy: bool = False

        self.ammo: int = 1000
        self.thrust: float = 40 * self.mass
        self.rotation_thrust: float = 100
        self.move_right: bool = False
        self.move_left: bool = False
        self.move_down: bool = False
        self.move_up: bool = False

        self.fuel_consumption_rate: float = 0
        self.fuel_rot_consumption_rate: float = 0

        self.damage_indicator_timer: float = 0

    def get_faced_direction(self) -> Vec2:
        """Get `self`'s faced direction from its `angle`.

        Returns
        -------
            Vec2: Faced direction, normalized

        """
        # For unknown reasons, `Vec2.from_polar((self.angle, 1))` won't work.
        direction = Vec2()
        direction.from_polar((1, self.angle))
        return direction

    def shoot(self) -> None:
        """Try to shoot a bullet."""
        if self.gun_cooldown <= 0 and self.ammo > 0:
            forward = self.get_faced_direction()
            bullet_pos = self.pos + forward * self.radius * HEAD_LENGTH
            bullet_vel = self.vel + forward * BULLET_SPEED
            self.projectiles.append(Bullet(bullet_pos, bullet_vel, self.color))
            self.gun_cooldown = 0.5
            self.ammo -= 1

    def suffer_damage(self, damage: float) -> None:
        """Deal damage to the ship and activate its damage-indicator.

        Does nothing if damage is <= 0.

        Args:
        ----
            damage (float): Amount of damage to deal.

        """
        if damage > 0:
            self.health -= damage
            self.damage_indicator_timer = DAMAGE_INDICATOR_TIME

    def step(self, dt: float) -> None:
        """Physics, control, and bullet-stepping for `self`.

        Args:
        ----
            dt (float): Passed time

        """
        if self.move_right:
            self.pos += (SPEED,0)

        if self.move_left:
            self.pos += (-SPEED,0)

        forward = self.get_faced_direction()
        if self.move_up:
            self.pos += (0,-SPEED)

        if self.move_down:
            self.pos += (0,SPEED)


        self.damage_indicator_timer = max(0, self.damage_indicator_timer - dt)

        super().step(dt)

        for projectile in self.projectiles:
            projectile.step(dt)

        self.gun_cooldown = max(0, self.gun_cooldown - dt)

    def draw(self, camera: Camera) -> None:
        """Draw `self` on `camera.

        Args:
        ----
            camera (Camera): Camera to draw on

        """
        forward = self.get_faced_direction()
        right = Vec2(-forward.y, forward.x)
        left = -right
        backward = -forward

        base_color: Color = self.color.lerp(Color("red"), self.damage_indicator_timer)
        darker_color: Color = base_color.lerp(Color("black"), 0.5)

        # Helper function for drawing polygons relative to the ship-position
        def drawy(color: Color, points: list[Vec2]) -> None:
            camera.draw_polygon(color, [self.pos + self.radius * p for p in points])

        # move_down (active)
        if self.move_down:
            drawy(Color("white"), [forward * 2, left * 1.25, right * 1.25])

        # "For his neutral special, he wields a cannon"
        camera.draw_line(
            darker_color,
            self.pos,
            self.pos + forward * self.radius * HEAD_LENGTH,
            HEAD_WIDTH * self.radius,
        )

        # move_right (material)
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * forward,
                0.5 * left + 0.5 * backward,
                2.0 * left + 4.0 * backward,
            ],
        )
        # move_right (active)
        if self.move_right:
            drawy(
                Color("white"),
                [
                    1.5 * left + 1.25 * backward,
                    0.5 * left + 0.5 * backward,
                    2.0 * left + 1.0 * backward,
                ],
            )

        # move_left (material)
        drawy(
            darker_color,
            [
                0.7 * right + 0.7 * forward,
                0.5 * right + 0.5 * backward,
                2.0 * right + 4.0 * backward,
            ],
        )
        # move_left (active)
        if self.move_left:
            drawy(
                Color("white"),
                [
                    1.5 * right + 1.25 * backward,
                    0.5 * right + 0.5 * backward,
                    2.0 * right + 1.0 * backward,
                ],
            )

        # move_up (flame)
        if self.move_up:
            drawy(
                Color("white"),
                [
                    0.7 * left + 0.7 * backward,
                    0.5 * left + 1.5 * backward,
                    1.25 * backward,
                    0.5 * right + 1.5 * backward,
                    0.7 * right + 0.7 * backward,
                ],
            )
        # move_up (material)
        drawy(
            darker_color,
            [
                0.7 * left + 0.7 * backward,
                0.5 * left + 1.25 * backward,
                1.0 * backward,
                0.5 * right + 1.25 * backward,
                0.7 * right + 0.7 * backward,
            ],
        )

        # Ugly hack
        backup_self_color = Color(self.color)
        self.color = base_color
        super().draw(camera)  # Draw circular body ("hitbox")
        self.color = backup_self_color

        for projectile in self.projectiles:
            projectile.draw(camera)


class ShipInput:
    """Specification for which keys trigger what spaceship-action."""

    type PygameKey = int

    def __init__(
        self,
        move_right: PygameKey,
        move_left: PygameKey,
        move_up: PygameKey,
        move_down: PygameKey,
        shoot: PygameKey,
    ) -> None:
        """Create a new map from keys to spaceship-actions.

        Args:
        ----
            move_right (pygame_key): Left rotation thruster's key
            move_left (pygame_key): Right rotation thruster's key
            move_up (pygame_key): Forward thruster's key
            move_down (pygame_key): Backward thruster's key
            shoot (pygame_key): Pew pew key

        """
        self.move_right = move_right
        self.move_left = move_left
        self.move_up = move_up
        self.move_down = move_down
        self.shoot = shoot


class PlayerShip(Ship):
    """A player-controlled spaceship."""

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        density: float,
        size: float,
        color: Color,
        spaceship_input: ShipInput,
    ) -> None:
        """Create a new player-spaceship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            density (float): Density (of disk-body)
            size (float): Radius of disk-body
            color (Color): Material color
            spaceship_input (SpaceshipInput): Map from keys to actions

        """
        super().__init__(pos, vel, density, size, color)
        self.spaceship_input = spaceship_input

    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """Handle input for `self` using ScancodeWrapper `keys`.

        `keys` is typically retreived using `pygame.key.get_pressed()`

        Args:
        ----
            keys (pygame.key.ScancodeWrapper): Pressed keys

        """
        self.move_right = keys[self.spaceship_input.move_right]
        self.move_left = keys[self.spaceship_input.move_left]
        self.move_up = keys[self.spaceship_input.move_up]
        self.move_down = keys[self.spaceship_input.move_down]
        if keys[self.spaceship_input.shoot]:
            self.shoot()


class BulletEnemy(Ship):
    """An enemy ship, targeting a specific other ship."""

    Action = Enum(
        "Action",
        [
            "accelerate_to_player",
            "accelerate_randomly",
            "decelerate",
        ],
    )

    def __init__(
        self,
        pos: Vec2,
        vel: Vec2,
        target_ship: Ship,
        shoot_cooldown: float = 0.0125,
        color: Color = Color("lime"),
    ) -> None:
        """Create a new enemy ship.

        Args:
        ----
            pos (Vec2): Initial position
            vel (Vec2): Initial velocity
            target_ship (Ship): Ship to target
            shoot_cooldown (float, optional): Minimum time between shots.
                Defaults to 0.125.
            color (Color, optional): Material color. Defaults to Color("purple").

        """
        super().__init__(pos, vel, 1, 8, color)
        self.thrust *= 1
        self.time_until_next_shot = 20
        self.action_timer = 6
        self.health = 10000
        self.current_action: BulletEnemy.Action = (
            BulletEnemy.Action.accelerate_to_player
        )
        self.target_ship = target_ship
        self.shoot_cooldown = shoot_cooldown
        self.projectiles: list[Bullet] = []

    def step(self, dt: float) -> None:
        """Apply physics and "AI" to `self`.

        Args:
        ----
            dt (float): Passed time

        """
        self.action_timer -= dt
        if self.action_timer <= 0:
            [self.current_action] = random.choices(
                population=list(BulletEnemy.Action), weights=[0.9, 0.05, 0.05]
            )
            self.action_timer = 6

        delta_target_ship = self.target_ship.pos - self.pos

        force_direction: Vec2
        match self.current_action:
            case BulletEnemy.Action.accelerate_to_player:
                force_direction = delta_target_ship
            case BulletEnemy.Action.accelerate_randomly:
                force_direction = Vec2(random.uniform(-1, 1), random.uniform(-1, 1))
            case BulletEnemy.Action.decelerate:
                force_direction = -self.vel
        force = force_direction * self.thrust / force_direction.magnitude()
        self.apply_force(force, dt)

        super().step(dt)
        self.angle = math.degrees(math.atan2(self.vel.y, self.vel.x))

        # Shooting logic
        self.time_until_next_shot -= 1
        if (
            delta_target_ship.magnitude_squared() < ENEMY_SHOOT_RANGE**2
            and self.time_until_next_shot <= 0
        ):
            self.shoot()
            self.time_until_next_shot = self.shoot_cooldown
