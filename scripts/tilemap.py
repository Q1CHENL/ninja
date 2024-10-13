import json
import pygame
import math

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8
}

PHYSICS_TILES = {'grass', 'stone'}  # faster than list
AUTOTILE_TYPES = {'grass', 'stone'}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size # every tile is square with side length of 16 pixels
        self.tilemap = {}  # every tile on grid, only handle physics on these tiles
        self.offgrid_tiles = [] # tiles that might be placed off grid

    # get info about some tiles and keep/delete them
    # type_varient_pairs: (type: string, variant: int)
    def extract(self, type_varient_pair_list, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in type_varient_pair_list:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        # In the video, the tilemap is not wrapped by a list(), which
        # may cause RuntimeError: dictionary changed size during iteration                    
        for loc in list(self.tilemap):
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in type_varient_pair_list:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        
        return matches
    
    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]
    
    def physics_rects_around(self, pos, entity_width, entity_height):
        rects = []
        for tile in self.tiles_around(pos, entity_width, entity_height):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size, 
                                         tile['pos'][1] * self.tile_size, 
                                         self.tile_size,
                                         self.tile_size))
        return rects

    def tiles_around(self, enitity_pos, entity_img_width, entity_img_height):
        outline_locs = []
        tiles_num_x = math.ceil(entity_img_width / self.tile_size)
        tiles_num_y = math.ceil(entity_img_height / self.tile_size)
        entity_tile_loc = (int(enitity_pos[0] // self.tile_size), int(enitity_pos[1] // self.tile_size))
        # tiles on the left and right
        for i in {-1, tiles_num_x}:
            for j in range(0, tiles_num_y + 1):
                outline_loc = str(max(0, entity_tile_loc[0] + i)) + ';' + str(entity_tile_loc[1] + j)
                if outline_loc in self.tilemap:
                    outline_locs.append(self.tilemap[outline_loc])
        # tiles on the top and bottom
        for i in {-1, tiles_num_y}:
            for j in range(0, tiles_num_x + 1):
                outline_loc = str(entity_tile_loc[0] + j ) + ';' + str(entity_tile_loc[1] + i)
                if outline_loc in self.tilemap:
                    outline_locs.append(self.tilemap[outline_loc])
        topleft_loc = str(max(0, entity_tile_loc[0] - 1)) + ';' + str(max(0, entity_tile_loc[1] - 1))
        if topleft_loc in self.tilemap:
            outline_locs.append(self.tilemap[topleft_loc])
        for i in range(0, tiles_num_x):
            for j in range(0, tiles_num_y):
                selfloc = str(entity_tile_loc[0] + i) + ';' + str(entity_tile_loc[1] + j)
                if selfloc in self.tilemap:
                    outline_locs.append(self.tilemap[selfloc])
        return outline_locs
                
        
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size,
                  'offgrid': self.offgrid_tiles}, f)
        f.close()

    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + \
                    ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']],
                      (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))

        # optimization of tilemap: only render the tiles need to be shown in display
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    surf.blit(self.game.assets[tile['type']][tile['variant']], (
                        tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
