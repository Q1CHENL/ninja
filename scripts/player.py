import random
import math
from scripts.entity import PhysicsEntity
from scripts.particle import Particle

character_str = 'ninja'

class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, character_str, pos, size)
        self.air_time = 0 # tracks how long player's been in the air
        self.jumps = 1 # player can jump once when on the ground/wall
        self.wall_slide = False
        if character_str == 'ninja':
            self.anim_offset = (-3, -3)
        elif character_str == 'knight':
            self.anim_offset = (-3, -3)
        else:
            self.anim_offset = (0, 0)

    # update in every frame
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)

        # prevent falling forever
        self.air_time += 1
        if self.air_time > 120:
            if not self.game.dead:
                self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

        # in case of collision, reset air time and jumps
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1  # reset jump to 1

        self.wall_slide = False
        # player slides when in the air and touches the wall
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            # set to greater than 4, otherwise player is not sliding anymore in next call
            self.air_time = 5
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5) # set max. downward speed to 0.5
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
            self.set_action('wall_slide')

        if not self.wall_slide:
            if self.air_time > 4:
                # show jump image if player's been in the air for 4 time units
                self.set_action('jump')
            elif movement[0] != 0:  
                # player is moving horizontally
                self.set_action('run')
            else:
                self.set_action('idle')

        # burst of particles when dashing at start: 60 or end: 50 of the dash 
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        
        if self.dashing > 0: 
            self.dashing = max(0, self.dashing-1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing+1)
        # black particles along dashing
        if abs(self.dashing) > 50: # in the first 10 frames of dashing
            # seems like 50 mean we dash for 60 - 50 = 10 frames
            # the actual dash: 8 times speed, detemines the distance of dash as well
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            # at the end of the first 10 frames of dashing, we severely reduce the speed
            if abs(self.dashing) == 51:
                # achieve sudden stop of dash
                # also serves as cool down
                self.velocity[0] *= 0.1
                # make stream move along
            # particles velocity    
            pvelocity = [abs(self.dashing) /
                         self.dashing * random.random() * 3, 0]
            self.game.particles.append(
                Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

        # make wall push back naturally
        # works as air resistance
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def jump(self):
        # jump when slide on wall
        if self.wall_slide:
            # face left and moving left
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5  # pushed away from wall
                self.velocity[1] = -2.5 # force up
                self.air_time = 5 # a number bigger than 4 so the jump image will show
                self.jumps = max(0, self.jumps - 1) # player can jump while sliding even when jumps is 0
                return True
            # face right and moving right
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5  # pushed away from wall
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
        elif self.jumps:
            self.velocity[1] = -3 # increase vertical down speed
            self.jumps -= 1
            self.air_time = 5  # a number bigger than 4 so the jump image will show
            return True

    def render(self, surf, camera_offset=(0, 0)):
        # make player invisible if we are not in the first 10 frames of dashing
        if abs(self.dashing) <= 50:
            super().render(surf, camera_offset=camera_offset)

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
