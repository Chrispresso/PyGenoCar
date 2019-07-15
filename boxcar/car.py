from Box2D import *
from typing import List
from numpy import random
import random as rand
from .utils import get_boxcar_constant
from .wheel import *
from typing import List
import math


class Car(object):
    def __init__(self, world: b2World, wheels: List[Wheel], wheel_vertices: List[int], 
                 chassis_vertices: List[b2Vec2], chassis_densities: List[float],
                 winning_tile: b2Vec2, lowest_y_pos: float) -> None:
        self.world = world
        self.wheels = wheels
        self.wheel_vertices = wheel_vertices
        self.chassis_vertices = chassis_vertices
        self.chassis_densities = chassis_densities
        self.winning_tile = winning_tile
        self.lowest_y_pos = lowest_y_pos
        self.is_winner = False

        self.chassis = create_chassis(self.world, self.chassis_vertices, self.chassis_densities)

        self.is_alive = True
        self.frames = 0
        self.max_tries = get_boxcar_constant('car_max_tries')
        self.num_failures = 0
        self.max_position = -100
        self._destroyed = False

        # Calculate mass of car
        self.mass = self.chassis.mass
        for wheel in self.wheels:
            self.mass += wheel.mass

        #@TODO: This isn't right
        for wheel in self.wheels:
            torque = self.mass * abs(world.gravity.y) / wheel.radius
            wheel.torque = torque

        joint_def = b2RevoluteJointDef()
        for i in range(len(self.wheels)):
            chassis_vertex = self.chassis_vertices[self.wheel_vertices[i]]
            joint_def.localAnchorA = chassis_vertex
            joint_def.localAnchorB =  self.wheels[i].body.fixtures[0].shape.pos
            joint_def.maxMotorTorque = self.wheels[i].torque
            joint_def.motorSpeed = -15  # @TODO: Make this random
            joint_def.enableMotor = True
            joint_def.bodyA = self.chassis
            joint_def.bodyB = self.wheels[i].body
            world.CreateJoint(joint_def)

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
        if current_position.x > self.max_position and current_position.y > self.lowest_y_pos:
            self.num_failures = 0
            self.max_position = current_position.x
            return True

        # If we have not improved or are going very slow, update failures and destroy if needed
        if current_position.x <= self.max_position or self.linear_velocity.x < .001:
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
    restitution = .2
    wheels = []
    for _ in range(num_wheels):
        radius = random.uniform(get_boxcar_constant('min_wheel_radius'), get_boxcar_constant('max_wheel_radius'))
        density = random.uniform(get_boxcar_constant('min_wheel_density'), get_boxcar_constant('max_wheel_density'))
        wheels.append(Wheel(world, radius, density, restitution))
    
    min_chassis_axis = get_boxcar_constant('min_chassis_axis')
    max_chassis_axis = get_boxcar_constant('max_chassis_axis')

    chassis_vertices = []
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), 0))
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(0, random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), 0))
    chassis_vertices.append(b2Vec2(-random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(0, -random.uniform(min_chassis_axis, max_chassis_axis)))
    chassis_vertices.append(b2Vec2(random.uniform(min_chassis_axis, max_chassis_axis), -random.uniform(min_chassis_axis, max_chassis_axis)))

    densities = [30.] * 8

    wheel_verts = list(range(num_wheels))
    rand.shuffle(wheel_verts)
    return Car(world, wheels, wheel_verts, chassis_vertices, densities, winning_tile, lowest_y_pos)


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

    densities = [30.] * 8

    return create_chassis(world, vertices, densities)



def create_chassis(world: b2World, vertices: List[b2Vec2], densities: List[float]) -> b2Body:
    if len(vertices) != len(densities):
        raise Exception('vertices and densities must be same length')

    # Create body definition
    body_def = b2BodyDef()
    body_def.type = b2_dynamicBody
    body_def.position = b2Vec2(0, 1)

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

    body.CreateFixture(fixture_def)
