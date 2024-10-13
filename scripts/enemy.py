import random
import math

import pygame
from scripts.entity import PhysicsEntity
from scripts.spark import Spark
from scripts.particle import Particle


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0  # remaining time units to walk

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if (self.collisions['right'] or self.collisions['left']):
                    self.flip = not self.flip
                else:
                    movement = (
                        movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                # flip if not physical tiles around
                self.flip = not self.flip
            # reduce to 0 over time if already walking
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                # distance to player
                dtp = (self.game.player.pos[0] - self.pos[0],
                       self.game.player.pos[1] - self.pos[1])
                if (abs(dtp[1]) < 16):
                    if (self.flip and dtp[0] < 0):
                        self.game.sfx['shoot'].play()
                        # shoot projectile
                        self.game.projectiles.append(
                            [[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                        # spawen firing sparks (left)
                        for i in range(4):
                            self.game.sparks.append(Spark(
                                self.game.projectiles[-1][0], random.random() - 0.5 + math.pi, 2 + random.random()))
                    if (not self.flip and dtp[0] > 0):
                        self.game.sfx['shoot'].play()
                        self.game.projectiles.append(
                            [[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
                        # spawen firing sparks (right)
                        for i in range(4):
                            self.game.sparks.append(Spark(
                                self.game.projectiles[-1][0], random.random() - 0.5, 2+random.random()))
        # walk randomly for a while if not already walking
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)  # half a sec to 2 sec
        super().update(tilemap, movement=movement)
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                for i in range(30):
                    angle = random.random() * math.pi * 2
                    speed = random.random() * 5
                    self.game.sparks.append(
                        Spark(self.rect().center, angle, 2 + random.random()))
                    # angle of particle is opposite
                    self.game.particles.append(Particle(self.game, 'particle', self.game.player.rect().center, velocity=[
                        math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))
                    # big sparks
                self.game.sparks.append(
                    Spark(self.rect().center, 0, 5 + random.random()))
                self.game.sparks.append(
                    Spark(self.rect().center, math.pi, 5 + random.random()))
                return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset)
        if self.flip:
            # flip gun as well
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect(
            ).centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect(
            ).centerx + 4 - offset[0], self.rect().centery - offset[1]))
