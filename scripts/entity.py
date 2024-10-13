import pygame
import random
from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]  # velocity in x and y derection
        self.collisions = {'up': False, 'down': False,
                           'right': False, 'left': False}
        self.action = ''
        # for padding e.g player and enemy's run and idle image have different size
        self.anim_offset = (-3, -3)  


        self.flip = False  # right and left
        self.set_action('idle') # to set which animation we are currently using

        self.last_movement = [0, 0]

        self.dashing = 0  # how long player will dash for in frames

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        # only change if different action
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy() # create a instance of the Animation

    def update(self, tilemap, movement=(0, 0)):
        # collisons are reset every time
        self.collisions = {'up': False, 'down': False,
                           'right': False, 'left': False}
        # force(movement) + veclocity = final movement
        frame_movement = (movement[0] + self.velocity[0],
                          movement[1] + self.velocity[1])

        # update pos based on the movement
        # handle collisions x and y seperately is recommended
        # handle collision in x direction
        self.pos[0] += frame_movement[0]  # update player position
        entity_rect = self.rect()
        pra = tilemap.physics_rects_around(self.pos, entity_rect.width, entity_rect.height)
        for rect in pra:
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:  # moving right
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:  # moving left
                    entity_rect.left = rect.right
                    self.collisions['left'] = True

                self.pos[0] = entity_rect.x  # attach player to the tile
                # why don't use rect to represent the entity's position in the first place?
                # reason: rect in pygame only works with int

        # handle collision in y direction
        self.pos[1] += frame_movement[1]  # update player position
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos, entity_rect.width, entity_rect.height):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:  # moving down
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.bottom - entity_rect.height  # attach player to the tile

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        # max velocity is set to 5: avoid consistent acceleration
        # works as gravity
        # example: prevent forever up when jump
        # up phase  : velocity is from negative number to 0
        # down phase: valocity is from 0 to 5 or the value when hit the ground
        # y direction veclocity
        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        # down/up collision stops the entity, sets the vertical velocity to 0
        # in order to to accerlerate gradually
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, camera_offset=(0, 0)):
        # offset: camera offset
        # anim_offset: animation offset
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - camera_offset[0] + self.anim_offset[0], self.pos[1] - camera_offset[1] + self.anim_offset[1]))
