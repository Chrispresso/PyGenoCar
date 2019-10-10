from Box2D import *
import numpy as np
from typing import List
from numpy import random
import random as rand
from settings import get_boxcar_constant, get_ga_constant
from .wheel import *
from genetic_algorithm.individual import Individual
from typing import List, Optional, Union
import math

genes = {
    # Gene name              row(s)
    'chassis_vertices_x':    0,
    'chassis_vertices_y':    1,
    'chassis_densities':     2,
    'wheel_radii':           3,
    'wheel_densities':       4,
}

class Car(Individual):
    def __init__(self, world: b2World, wheel_radii: List[float], wheel_densities: List[float], 
                 chassis_vertices: List[b2Vec2], chassis_densities: List[float],
                 winning_tile: b2Vec2, lowest_y_pos: float, 
                 lifespan: Optional[Union[int, float]] = np.inf, from_chromosome: bool = False) -> None:
        self.world = world
        self.wheel_radii = wheel_radii
        self.wheel_densities = wheel_densities
        # self.wheels = wheels
        # self.wheel_vertices = wheel_vertices
        self.chassis_vertices = chassis_vertices
        self.chassis_densities = chassis_densities
        self.winning_tile = winning_tile
        self.lowest_y_pos = lowest_y_pos
        self.lifespan = lifespan
        self.is_winner = False

        # These are set in _init_car
        self.chassis = None 

        self.is_alive = True
        self.frames = 0
        self.max_tries = get_boxcar_constant('car_max_tries')
        self.num_failures = 0
        self.max_position = -100
        self._destroyed = False

        # GA stuff
        self._chromosome = None
        self._fitness = 0.01

        # If the car is being initialized and is NOT from a chromosome, then you need to initialize the GA settins
        # and encode the chromosome. Otherwise it will be taken car of during the deconding of the chromosome
        if not from_chromosome:
            self._init_ga_settings()
            self._init_car()

    def _init_car(self):
        self.chassis = create_chassis(self.world, self.chassis_vertices, self.chassis_densities)
        
        # Calculate chassis volume
        self.chassis_volume = 0.0
        for fixture in self.chassis.fixtures:
            mass = fixture.massData.mass
            density = fixture.density
            self.chassis_volume += mass / density

        # Create wheels from radius/density
        # Since the radius/density arrays are the same length as the chassis vertices, then if there is a positive
        # value, we say the wheel is at the index for the chassis vertex
        self.wheels = []
        self._wheel_vertices = []
        for i, (wheel_radius, wheel_density) in enumerate(zip(self.wheel_radii, self.wheel_densities)):
            # Are both above 0?
            if wheel_radius > 0.0 and wheel_density > 0.0:
                self.wheels.append(Wheel(self.world, wheel_radius, wheel_density))
                self._wheel_vertices.append(i)  # The chassis vertex this is going to attach to
        self.num_wheels = len(self.wheels)

        # Calculate mass of car
        self.mass = self.chassis.mass
        for wheel in self.wheels:
            self.mass += wheel.mass

        # Calculate torque of wheel
        for wheel in self.wheels:
            torque = self.mass * abs(self.world.gravity.y) / wheel.radius
            wheel.torque = torque

        joint_def = b2RevoluteJointDef()
        for i in range(len(self.wheels)):
            # Grab the chassis that the wheel should be on and anchor it
            chassis_vertex = self.chassis_vertices[self._wheel_vertices[i]]
            joint_def.localAnchorA = chassis_vertex
            joint_def.localAnchorB =  self.wheels[i].body.fixtures[0].shape.pos
      
            # Set the motor torque of the wheel - vroom vroom
            joint_def.maxMotorTorque = self.wheels[i].torque
            joint_def.motorSpeed = -15  # @TODO: Make this random
            joint_def.enableMotor = True
            joint_def.bodyA = self.chassis
            joint_def.bodyB = self.wheels[i].body
            self.world.CreateJoint(joint_def)

        # Calculate volume of wheels
        self.wheels_volume = 0.0
        for wheel in self.wheels:
            mass = wheel.body.fixtures[0].massData.mass
            density = wheel.body.fixtures[0].density
            self.wheels_volume += mass / density
    

    def _init_ga_settings(self) -> None:
        # Initialize the chromosome
        self._init_chromosome()

    def _init_chromosome(self) -> None:
        """
        Initializes the chromosome. Only needs to be call
        """
        self._chromosome = np.empty((5,8))
        self.encode_chromosome()

    def _set_car_from_values(self) -> None:
        """
        Set the car to be defined from things like:
        self.chassis_vertices
        self.
        """
        pass

    @classmethod
    def create_car_from_chromosome(cls, world: b2World, winning_tile: b2Vec2, lowest_y_pos: float,
                                   chromosome: np.ndarray) -> 'Car':
        car = Car(world, None, None, None, None, winning_tile, lowest_y_pos, from_chromosome=True)
        car._chromosome = np.copy(chromosome)
        car.decode_chromosome()
        return car

    def calculate_fitness(self) -> None:
        func = get_ga_constant('fitness_function')
        fitness = func(max(self.max_position, 0.0),
                       self.num_wheels,
                       self.chassis_volume,
                       self.wheels_volume,
                       self.frames)
        self._fitness = max(fitness, 0.0001)
        
    @property
    def fitness(self) -> float:
        return self._fitness
    
    @fitness.setter
    def fitness(self, val):
        self._fitness = val

    def encode_chromosome(self) -> None:
        #### Chassis stuff
        self._chromosome[genes['chassis_vertices_x'], :] = np.array([vertex.x for vertex in self.chassis_vertices])
        self._chromosome[genes['chassis_vertices_y'], :] = np.array([vertex.y for vertex in self.chassis_vertices])
        self._chromosome[genes['chassis_densities'], :] = np.array([density for density in self.chassis_densities])

        #### Wheel stuff
        self._chromosome[genes['wheel_radii'], :] = np.array([radius for radius in self.wheel_radii])
        self._chromosome[genes['wheel_densities'], :] = np.array([density for density in self.wheel_densities])

    def decode_chromosome(self) -> None:
        #@TODO: I may need to ignore the 0,2,4,6 vertices since those are bounding vertices and I'm not sure if there will
        # be a complete polygon if those begin changing drastically
        # If a chassis already exists, then we are going to delete it
        if self.chassis:
            self._destroy()
            # Reset the flags
            self._destroyed = False
            self.is_winner = False
            self.is_alive = True

        #### Decode chassis
        chassis_vertices: b2Vec2 = []
        # Don't forget to.... unzip your genes...
        for xy_vertex in zip(*self._chromosome[(genes['chassis_vertices_x'], genes['chassis_vertices_y']), :]):
            chassis_vertices.append(b2Vec2(xy_vertex))
        self.chassis_vertices = chassis_vertices
        self.chassis_densities = self._chromosome[genes['chassis_densities'], :]
        
        #### Decode wheel
        self.wheel_radii = self._chromosome[genes['wheel_radii'], :]
        self.wheel_densities = self._chromosome[genes['wheel_densities'], :]

        # Re-create the car based off the new chromosome
        self._init_car()

    @property
    def chromosome(self):
        return self._chromosome


    
    def clone(self):
        world = self.world
        wheels = []
        for wheel in self.wheels:
            radius = wheel.radius
            density = wheel.density
            restitution = wheel.restitution
            wheels.append(Wheel(world, radius, density, restitution))

        wheel_vertices = self._wheel_vertices[:]
        chassis_vertices = self.chassis_vertices[:]
        chassis_densities = self.chassis_densities[:]
        winning_tile = self.winning_tile
        lowest_y_pos = self.lowest_y_pos

        return Car(world, wheels, wheel_vertices, 
                 chassis_vertices, chassis_densities,
                 winning_tile, lowest_y_pos, True)

    def update(self) -> bool:
        if not self.is_alive:
            return False

        self.frames += 1
        current_position = self.position
        # Did we win?
        if current_position.x > self.winning_tile.position.x:
            self.is_winner = True
            self.is_alive = False
            self._destroy()
            print('winnnerr')
            return False
        # If we advanced past our max position, reset failures and max position
        if (current_position.x > self.max_position) and (current_position.y > self.lowest_y_pos) and (self.linear_velocity.x >= .4):
            self.num_failures = 0
            self.max_position = current_position.x
            return True

        # If we have not improved or are going very slow, update failures and destroy if needed
        if current_position.x <= self.max_position or self.linear_velocity.x < .4:
            self.num_failures += 1

        if current_position.y < self.lowest_y_pos:
            self.num_failures += 2

        if self.num_failures > self.max_tries:
            self.is_alive = False
        
        if not self.is_alive and not self._destroyed:
            self._destroy()
            return False
        
        return True

    def _destroy(self) -> None:
        self.world.DestroyBody(self.chassis)
        for wheel in self.wheels:
            self.world.DestroyBody(wheel.body)
        self._destroyed = True


    @property
    def linear_velocity(self) -> b2Vec2:
        return self.chassis.linearVelocity

    @linear_velocity.setter
    def linear_velocity(self, value):
        # Not actually read only, but don't allow it to be set
        raise Exception('linear velocity is read only!')

    @property
    def position(self) -> b2Vec2:
        return self.chassis.position

    @position.setter
    def position(self, value):
        raise Exception('position is read only!')



def create_random_car(world: b2World, winning_tile: b2Vec2, lowest_y_pos: float):
    # Create a number of random wheels.
    # Each wheel will have a random radius and density
    num_wheels = random.randint(get_boxcar_constant('min_num_wheels'), get_boxcar_constant('max_num_wheels') + 1)
    wheel_verts = list(range(num_wheels))  # What vertices should we attach to?
    rand.shuffle(wheel_verts)
    wheel_verts = wheel_verts[:num_wheels]
    wheel_radii = [0.0 for _ in range(8)]
    wheel_densities = [0.0 for _ in range(8)]

    # Assign a random radius/density to vertices found in wheel_verts
    for vert_idx in wheel_verts:
        radius = random.uniform(get_boxcar_constant('min_wheel_radius'), get_boxcar_constant('max_wheel_radius'))
        density = random.uniform(get_boxcar_constant('min_wheel_density'), get_boxcar_constant('max_wheel_density'))

        # Override the intiial 0.0
        wheel_radii[vert_idx] = radius
        wheel_densities[vert_idx] = density
    
    min_chassis_axis = get_boxcar_constant('min_chassis_axis')
    max_chassis_axis = get_boxcar_constant('max_chassis_axis')

    ####
    # The chassis vertices are on a grid and defined by v0-v7 like so:
    # 
    #             v2
    #              |
    #          v3  |  v1
    #     v4 -------------- v0
    #          v5  |  v7
    #              |
    #             v6
    #
    # V0, V2, V4 and V6 are on an axis, while the V1 is defined somewhere between V0 and V2, V3 is defined somewhere between V2 and V4, etc.
    chassis_vertices = []
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), 0))
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(0, random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), 0))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(0, -random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))

    densities = []
    for i in range(8):
        densities.append(random.uniform(get_boxcar_constant('min_chassis_density'), get_boxcar_constant('max_chassis_density')))


    return Car(world, wheel_radii, wheel_densities, chassis_vertices, densities, winning_tile, lowest_y_pos, lifespan=get_ga_constant('lifespan'))

def smart_clip(chromosome: np.ndarray) -> None:
    np.clip(chromosome[genes['chassis_densities'], :],
            0.0001,
            np.inf,
            out=chromosome[genes['chassis_densities'], :])

def clip_chromosome(chromosome: np.ndarray) -> None:
    """
    Clips the chromosome values to be  in between min/max values defined in settings.py
    """
    #### Chassis 
    # Row 0 and 1 are chassis vertices
    np.clip(chromosome[:2, :], get_boxcar_constant('min_chassis_axis'), get_boxcar_constant('max_chassis_axis'), out=chromosome[:2, :])
    # Row 2 is chassis density
    np.clip(chromosome[2, :], get_boxcar_constant('min_chassis_density'), get_boxcar_constant('max_chassis_density'), out=chromosome[2, :])

    #### Wheel - no need to clip bottom portion
    # Row 3 is wheel radius
    np.clip(chromosome[3, :], -np.inf, get_boxcar_constant('max_wheel_radius'), out=chromosome[3, :])
    # Row 4 is wheel density
    np.clip(chromosome[4, :], -np.inf, get_boxcar_constant('max_wheel_density'), out=chromosome[4, :])

def set_chromosome_bounding_vertices_to_zero(chromosome: np.ndarray) -> None:
    """
    Forcefully sets the bounding vertices to make a grid. Since V0, V2, V3 and V6 are the bounding vertices,
    they each have a component that start at 0. Either their x or y value is at 0. This ensures that even 
    through mutation/crossover, those components remain at 0.
    #@TODO: Test if this is necessary
    """
    #### Set the x-component of V2 and V6 to 0
    # Row 0 is x-component for chassis vertices
    chromosome[0, (2, 6)] = 0.0

    #### Set the y-component of V0 and V4 to 0
    # Row 1 is y-component for chassis vertices
    chromosome[1, (0, 4)] = 0.0

    

def clip_chromosome_to_zero(chromosome: np.ndarray) -> None:
    """
    Clips the chromosome so the minimum value is 0.0 for everything except wheel radius/density.
    Wheel radius/density can be negative since they will just be ignored anyway during the creation of wheels.
    """
    # radius/density are row 3 and 4
    np.clip(chromosome[:3, :], 0.0, np.inf, out=chromosome[:3, :])

def create_random_chassis(world: b2World) -> b2Body:
    min_chassis_axis = get_boxcar_constant('min_chassis_axis')
    max_chassis_axis = get_boxcar_constant('max_chassis_axis')

    vertices = []
    vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), 0))
    vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    vertices.append(b2Vec2(0, random.uniform(min_chassis_axis, max_chassis_axis)))
    vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), 0))
    vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))
    vertices.append(b2Vec2(0, -random.uniform(min_chassis_axis, max_chassis_axis)))
    vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))

    densities = []
    for i in range(8):
        densities.append(random.uniform(get_boxcar_constant('min_chassis_density'), get_boxcar_constant('max_chassis_density')))

    return create_chassis(world, vertices, densities)


def create_chassis(world: b2World, vertices: List[b2Vec2], densities: List[float]) -> b2Body:
    if len(vertices) != len(densities):
        raise Exception('vertices and densities must be same length')

    # Create body definition
    body_def = b2BodyDef()
    body_def.type = b2_dynamicBody
    body_def.position = b2Vec2(0, 2)  # Create at (0,1 so it's slightly above the track)

    body = world.CreateBody(body_def)

    # Create chassis parts for the given vertices
    for i in range(len(vertices)):
        # If we are at the end, grab the first index
        if i == len(vertices)-1:
            end_idx = 0
        else:
            end_idx = i+1
        _create_chassis_part(body, vertices[i], vertices[end_idx], densities[i])

    return body


def _create_chassis_part(body: b2Body, point0: b2Vec2, point1: b2Vec2, density: float) -> None:
    """
    Creates a fixture with a polygon shape and adds it to the body.
    The origin point will be (0, 0) and create a polygon with point0 and point1, creating a triangle
    """
    vertices = [point0, point1, b2Vec2(0, 0)]
    
    fixture_def = b2FixtureDef()
    fixture_def.shape = b2PolygonShape()
    fixture_def.density = density
    fixture_def.friction = 10.0
    fixture_def.restitution = 0.2
    fixture_def.groupIndex = -1
    fixture_def.shape.vertices = vertices
    #@TODO: sometimes rotational_intertia be is <0... need to fix that
    body.CreateFixture(fixture_def)


