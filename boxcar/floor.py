from Box2D import *
from .base import BoxCarObject
from typing import List
from .utils import boxcar_constant as bcc
import math
import random

def rotate_floor_tile(coords: List[b2Vec2], center: b2Vec2, angle: float) -> List[b2Vec2]:
    rads = angle * math.pi / 180.0  # Degree to radians
    new_coords: List[b2Vec2] = []
    for coord in coords:
        new_coord = b2Vec2()
        new_coord.x = math.cos(rads)*(coord.x - center.x) - math.sin(rads)*(coord.y - center.y) + center.x
        new_coord.y = math.sin(rads)*(coord.x - center.x) + math.cos(rads)*(coord.y - center.y) + center.y
        new_coords.append(new_coord)

    return new_coords

def create_floor_tile(world: b2World, position: b2Vec2, angle: float) -> b2Body:
    width = bcc['floor_tile_width']
    height = bcc['floor_tile_height']

    body_def = b2BodyDef()
    body_def.position = position
    body = world.CreateBody(body_def)

    # Create Fixture
    fixture_def = b2FixtureDef()
    fixture_def.shape = b2PolygonShape()
    fixture_def.friction = 0.5

    # Coordinates of tile
    # p3---------p2
    # |          |
    # p0---------p1
    coords: List[b2Vec2] = []
    coords.append(b2Vec2(0, 0))            # p0
    coords.append(b2Vec2(width, 0))        # p1
    coords.append(b2Vec2(width, -height))  # p2
    coords.append(b2Vec2(0, -height))      # p3
    # Rotate @NOTE: This rotates in reference to p0
    coords = rotate_floor_tile(coords, b2Vec2(0, 0), angle)

    # Set vertices of fixture
    fixture_def.shape.vertices = coords

    body.CreateFixture(fixture_def)
    return body


class Floor(object):
    def __init__(self, world: b2World, seed=0, num_tiles = bcc['max_floor_tiles']):
        self.world = world
        self.seed = seed
        self.num_tiles = num_tiles
        self.floor_tiles: List[b2Body] = []
        self.rand = random.Random(self.seed)
        self._generate_floor()

    def _generate_floor(self):
        tile_position = b2Vec2(-5, 0)
        for i in range(self.num_tiles):
            # floor_tile = create_floor_tile(self.world, tile_position, (self.rand.random()*1.5*2 - 1.5) * 1.5*i/self.num_tiles)
            floor_tile = create_floor_tile(self.world, tile_position, 0)  # i*3
            self.floor_tiles.append(floor_tile)
            # Get the world coordinate of the bottom-right of the box and set that as the next position to start from.
            # The position of the new box will be defined from bottom-left, so this stacks them next to each other
            world_coord = floor_tile.GetWorldPoint(floor_tile.fixtures[0].shape.vertices[1])
            tile_position = world_coord

    def destroy(self):
        for tile in self.floor_tiles:
            self.world.DestroyBody(tile)

    def _generate_gaussian_random_floor(self):
        tile_position = b2Vec2(-5, 0)
        threshold = bcc['tile_gaussian_threshold']
        denominator = 
        for i in range(self.num_tiles):
            numerator = min(i, threshold)
            scale = min(float(numerator) / threshold, 1.0)
            
