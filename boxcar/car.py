from Box2D import *
from typing import List
from numpy import random
from .utils import boxcar_constant as bcc
from .wheel import *
from typing import List
import math


class Car(object):
    def __init__(self, world: b2World, wheels: List[Wheel], wheel_vertices: List[int], 
                 chassis_vertices: List[b2Vec2]=None, chassis_densities: List[float]=None) -> None:
        self.world = world
        self.wheels = wheels
        self.wheel_vertices = wheel_vertices
        self.chassis_vertices = chassis_vertices
        self.chassis_densities = chassis_densities

        if self.chassis_vertices:
            self.chassis = create_chassis(world, self.chassis_vertices, self.chassis_densities)
        else:
            self.chassis = create_random_chassis(world)

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
            chassis_vertex = self.chassis_vertices[self.wheel_vertices[i]] # self.chassis.fixtures[0].shape.vertices[0]
            joint_def.localAnchorA = chassis_vertex
            joint_def.localAnchorB =  self.wheels[i].body.fixtures[0].shape.pos
            joint_def.maxMotorTorque = self.wheels[i].torque
            joint_def.motorSpeed = -15
            joint_def.enableMotor = True
            joint_def.bodyA = self.chassis
            joint_def.bodyB = self.wheels[i].body
            world.CreateJoint(joint_def)

def create_random_car(world: b2World):
    num_wheels = 2 # random.randint(0, 9)
    restitution = .2
    wheels = []
    for i in range(num_wheels):
        radius = .2
        density = 10
        wheels.append(Wheel(world, radius, density, restitution))
    
    min_chassis_axis = bcc['min_chassis_axis']
    max_chassis_axis = bcc['max_chassis_axis']

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

    wheel_verts = [1, 4]
    return Car(world, wheels, wheel_verts, chassis_vertices, densities)


def create_random_chassis(world: b2World) -> b2Body:
    min_chassis_axis = bcc['min_chassis_axis']
    max_chassis_axis = bcc['max_chassis_axis']

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
    body_def.position = b2Vec2(0, 4)

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
