import os
import sys
import random
import math
import pygame

from scripts.player import Player
from scripts.enemy import Enemy
from scripts.utils import load_image, load_images, Animation
from scripts.tilemap import Tilemap
from scripts.cloud import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

variant_player = 0
variant_enemy = 1

class Game:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('Ninja')
        # resolution of the window
        self.window_width = 1200
        self.window_height = 900
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))

        # we render on these smaller displays, and scale up to the the bigger window to avoid too small images
        # the resolution here should math the resolution of the background image, otherwise there will be black space
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)  # default black
        self.display_2 = pygame.Surface((320, 240))  # default black

        # May want to restrict frame for games since every frame is rendered
        # individually and we don't want out CPU to be overloaded
        # 1 frame = 1 iteration of the game loop while true
        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.paused = False
        
        character_str = 'ninja'
        character_size = (0, 0)
        if character_str == 'ninja':
            character_size = (8, 15)
        elif character_str == 'pekka':
            character_size = (60, 47)
        elif character_str == 'knight':
            character_size = (21, 22)


        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'stone': load_images('tiles/stone'),
            'pickups': load_images('tiles/pickups'),
            'large_decor': load_images('tiles/large_decor'),
            character_str : load_image('entities/'+ character_str + '.png'),
            'background': load_image('background_night.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            character_str + '/idle': Animation(load_images('entities/' + character_str + '/idle'), img_dur=6),
            character_str + '/run': Animation(load_images('entities/' + character_str + '/run'), img_dur=15),
            character_str + '/jump': Animation(load_images('entities/'+ character_str + '/jump')),
            character_str + '/slide': Animation(load_images('entities/' + character_str + '/slide')),
            character_str + '/wall_slide': Animation(load_images('entities/' + character_str + '/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png')
        }

        self.sfx = {
            'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
            'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        }
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.3)
        self.sfx['jump'].set_volume(0.7)

        self.clouds = Clouds(self.assets['clouds'], count=16)

        self.player = Player(self, (50, 50), character_size)

        self.tilemap = Tilemap(self, tile_size=16)

        # Game starts from level 0
        self.level = 0
        self.load_level(self.level)

        self.screenshake = 0

        self.current_level_passed = False

    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        # self.tilemap.load('data/maps/map.json')
        self.leaf_spawners = []

        self.enemies = []

        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(
                4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

        for character in self.tilemap.extract([('character', variant_player), ('character', variant_enemy)]):
        # for spawner in self.tilemap.extract([('character', 0)]):
            if character['variant'] == variant_player:
                self.player.pos = character['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, character['pos'], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        # can be seen as camera's location, used to focus the main view on the player
        self.camera_offset = [0, 0] 
        self.dead = 0
        
        # for the black circle transition effect between levels
        # self.transition = -30
        self.transition = 0

    def run(self):
        pygame.mixer.music.load('data/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)  # negative: loop forever
        self.sfx['ambience'].play(-1)

        while True:
            if not self.paused:
                self.display.fill((0, 0, 0, 0))
                # Fill the screen: everything from last fram will be replace with this color
                # Create a rectangle with: top left pos, width and height
                # self.display.fill((14, 219, 248))
                self.display_2.blit(self.assets['background'], (0, 0))

                self.screenshake = max(0, self.screenshake - 1)

                if self.current_level_passed:
                    self.transition += 1
                    if self.transition > 30:
                        # ensure don't go above max level
                        self.level = min(
                            self.level + 1, len(os.listdir('data/maps')) - 1)
                        # load level when complete black
                        self.load_level(self.level)
                        self.current_level_passed = False
                if self.transition < 0:
                    self.transition += 1

                if self.dead:
                    self.dead += 1
                    if self.dead >= 10:
                        self.transition = min(30, self.transition + 1)
                    if self.dead > 40:  # timer
                        self.load_level(self.level)

                self.camera_offset[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.camera_offset[0]) / 30

                self.camera_offset[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.camera_offset[1]) / 30

                render_camera_offset = (int(self.camera_offset[0]), int(self.camera_offset[1]))
                # render_camera_offset = (0, 0)

                for rect in self.leaf_spawners:
                    # spawn rate: bigger tree spawn more
                    # multiply by big number make it not spawning every frame
                    if random.random() * 49999 < rect.width * rect.height:
                        pos = (rect.x + random.random() * rect.width,
                               rect.y + random.random() * rect.height)
                        self.particles.append(
                            Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))

                self.clouds.update()
                # cloud no outline: display_2
                self.clouds.render(self.display_2, offset=render_camera_offset)
                # avoid subpixel movement for the camera
                self.tilemap.render(self.display, offset=render_camera_offset)

                for enemy in self.enemies.copy():
                    kill = enemy.update(self.tilemap, (0, 0))
                    enemy.render(self.display, offset=render_camera_offset)
                    if kill:
                        self.enemies.remove(enemy)
                        if not len(self.enemies):
                            self.current_level_passed = True

                if not self.dead:
                    # movement[1] == 0 since we move horizontally
                    self.player.update(
                        self.tilemap, (self.movement[1] - self.movement[0], 0))
                    self.player.render(self.display, camera_offset=render_camera_offset)

                for projectile in self.projectiles.copy():
                    projectile[0][0] += projectile[1]
                    projectile[2] += 1  # timer
                    img = self.assets['projectile']
                    self.display.blit(img, (projectile[0][0] - img.get_width(
                    ) / 2 - render_camera_offset[0], projectile[0][1] - img.get_height() / 2 - render_camera_offset[1]))
                    if self.tilemap.solid_check(projectile[0]):
                        self.projectiles.remove(projectile)
                        for i in range(4):
                            self.sparks.append(Spark(
                                projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))

                    elif projectile[2] > 360:  # 6 seconds
                        self.projectiles.remove(projectile)
                    elif abs(self.player.dashing) < 50:  # invincible during dash
                        if self.player.rect().collidepoint(projectile[0]):
                            self.projectiles.remove(projectile)
                            self.dead += 1
                            self.sfx['hit'].play()
                            self.screenshake = max(16, self.screenshake)
                            # when hit player: death
                            for i in range(30):
                                angle = random.random() * math.pi * 2
                                speed = random.random() * 5
                                self.sparks.append(
                                    Spark(self.player.rect().center, angle, 2 + random.random()))
                                # angle of particle is opposite
                                self.particles.append(Particle(self, 'particle', self.player.rect().center, velocity=[
                                                      math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5], frame=random.randint(0, 7)))

                for spark in self.sparks.copy():
                    kill = spark.update()
                    spark.render(self.display, offset=render_camera_offset)
                    if kill:
                        self.sparks.remove(spark)

                display_mask = pygame.mask.from_surface(self.display)
                display_sillhouette = display_mask.to_surface(
                    setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))

                # draw outline
                for offset in [(-1, 0), (1, 0), (0, 1), (0, 1)]:
                    self.display_2.blit(display_sillhouette, offset)

                for particle in self.particles.copy():
                    kill = particle.update()
                    particle.render(self.display, offset=render_camera_offset)
                    if particle.type == 'leaf':
                        # move particle back and forth naturally
                        particle.pos[0] += math.sin(
                            particle.animation.frame * 0.035) * 0.3
                    if kill:
                        self.particles.remove(particle)

            # blit essentially copy the memory to the position
            # we can blit any surface to to others
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # click X on the window
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_UP or event.key == pygame.K_k:  # magic: negative velocity == jump
                        if self.player.jump():
                            self.sfx['jump'].play()
                    if event.key == pygame.K_j:
                        self.player.dash()
                    if event.key == pygame.K_ESCAPE:
                        self.paused = not self.paused
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.movement[1] = False
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))

            self.display_2.blit(self.display, (0, 0))

            screenshake_offset = (random.random() * self.screenshake - self.screenshake/2,
                                  random.random() * self.screenshake - self.screenshake/2)
            self.screen.blit(pygame.transform.scale(
                self.display_2, self.screen.get_size()), screenshake_offset)
            # self.screen.blit(pygame.transform.scale(
            #     self.display, self.screen.get_size()), screenshake_offset)
            
            if self.paused:
                # Draw a semi-transparent overlay
                overlay = pygame.Surface(
                    (self.window_width, self.window_height))
                overlay.fill((100, 100, 100))
                # Set alpha value for transparency (0-255)
                overlay.set_alpha(128)
                # Blit overlay on top of the game
                self.screen.blit(overlay, (0, 0))

                font = pygame.font.Font(None, 120)
                paused_text = font.render('Paused', True, (255, 255, 255))
                text_rect = paused_text.get_rect(center=(self.screen.get_width() / 2,
                                                         self.screen.get_height() / 2 - paused_text.get_height() / 2))
                self.screen.blit(paused_text, text_rect)
            # update everything on the screen
            pygame.display.update()
            self.clock.tick(60)  # 60 fps of the while true loop using sleep mechanism


Game().run()
