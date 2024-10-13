import sys
import pygame

from scripts.utils import load_images
from scripts.tilemap import Tilemap

# how much we're multiplying the size of each pixel
RENDER_SCALE = 2.0


class Editor:
    def __init__(self):
        pygame.init()

        pygame.display.set_caption('editor')
        self.screen = pygame.display.set_mode((640, 480))

        # we render on this smaller displayer, and scale up to the bigger screen
        self.display = pygame.Surface((320, 240))  # default black

        # May want to restrict frame for games since every frame is rendered
        # individually and we don't want out CPU to be overloaded
        self.clock = pygame.time.Clock()

        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'stone': load_images('tiles/stone'),
            'large_decor': load_images('tiles/large_decor'),
            'character': load_images('tiles/spawners')
        }
        self.movement = [False, False, False, False]

        self.tilemap = Tilemap(self, tile_size=16)
        
        try:
            self.tilemap.load('map.json')
        except FileNotFoundError:
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False

        self.shift = False

        self.ongrid = True

    def run(self):
        while True:
            # Fill the screen: everything from last fram will be replace with this color
            # Create a rectangle with: top left pos, width and height
            # self.display.fill((14, 219, 248))
            self.display.fill((0, 0, 0))

            # move camera using keyboard (wasd)
            self.scroll[0] += (self.movement[1] - self.movement[0])*2
            self.scroll[1] += (self.movement[3] - self.movement[2])*2

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            self.tilemap.render(self.display, offset=render_scroll)

            # copy since we want to set alpha (opacity)
            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy(
            )
            current_tile_img.set_alpha(100)  # 0 is fully transparent

            # mouse position
            mpos = pygame.mouse.get_pos()
            # because our game is scaled up by 2
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)

            tile_pos = (int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                        int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size))

            if self.ongrid:
                # to see where the next tile will be placed
                # convert tile_pos back to pixel pos, remove scroll
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size -
                                                     self.scroll[0], tile_pos[1] * self.tilemap.tile_size-self.scroll[1]))
            else:
                self.display.blit(current_tile_img, mpos)

            # left click to create tile
            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ';'+str(tile_pos[1])] = {
                    'type': self.tile_list[self.tile_group],
                    'variant': self.tile_variant,
                    'pos': tile_pos
                }

            # right click to delete tiles
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ';' + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile['type']][tile['variant']]
                    # hitbox
                    tile_r = pygame.Rect(tile['pos'][0] - self.scroll[0], tile['pos'][1] - self.scroll[1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
            self.display.blit(current_tile_img, (5, 5))

            # blit essentially copy the memory to the position
            # we can blit any surface to to others
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # click X on the window
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # left click
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {'type': self.tile_list[self.tile_group], 'variant': self.tile_variant, 'pos': (mpos[0] + render_scroll[0], mpos[1] + self.scroll[1])})
                    if event.button == 3:  # right click
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:  # scroll up
                            self.tile_variant = (
                                self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:  # scroll down
                            self.tile_variant = (
                                self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:  # scroll up
                            self.tile_group = (
                                self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0  # reset: prevent index error
                        if event.button == 5:  # scroll down
                            self.tile_group = (
                                self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0  # reset: prevent index error
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_o:
                        self.tilemap.save('map.json')
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False
            self.screen.blit(pygame.transform.scale(
                self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)  # 60 fps


Editor().run()
