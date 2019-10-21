from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from typing import Optional, Tuple, List, Dict, Any
import argparse
import dill as pickle
from enum import Enum, unique
from Box2D import *
import random
from boxcar.floor import Floor
from boxcar.car import Car, create_random_car, save_car, load_car, smart_clip
from genetic_algorithm.population import Population
from genetic_algorithm.individual import Individual
from genetic_algorithm.crossover import simulated_binary_crossover as SBX
from genetic_algorithm.crossover import single_point_binary_crossover as SPBX
from genetic_algorithm.mutation import gaussian_mutation
from genetic_algorithm.selection import elitism_selection, roulette_wheel_selection, tournament_selection
from settings import get_boxcar_constant, get_ga_constant
import settings
from windows import SettingsWindow, StatsWindow, draw_border
import os
import sys
import time
import numpy as np
import math


## Constants ##
scale = 70
default_scale = 70
FPS = 60


@unique
class States(Enum):
    FIRST_GEN = 0
    FIRST_GEN_IN_PROGRESS = 1
    NEXT_GEN = 2
    NEXT_GEN_COPY_PARENTS_OVER = 4
    NEXT_GEN_CREATE_OFFSPRING = 5
    REPLAY = 6


def draw_circle(painter: QPainter, body: b2Body, local=False) -> None:
    """
    Draws a circle with the given painter.
    """
    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2CircleShape):
            # Set the color of the circle to be based off wheel density
            adjust = get_boxcar_constant('max_wheel_density') - get_boxcar_constant('min_wheel_density')
            # If the min/max are the same you will get 0 adjust. This is to prevent divide by zero.
            if adjust == 0.0:
                hue_ratio = 0.0
            else:
                hue_ratio = (fixture.density - get_boxcar_constant('min_wheel_density')) / adjust
            hue_ratio = min(max(hue_ratio, 0.0), 1.0)  # Just in case you leave the GA unbounded...
            color = QColor.fromHsvF(hue_ratio, 1., .8)
            painter.setBrush(QBrush(color, Qt.SolidPattern))

            radius = fixture.shape.radius
            if local:
                center = fixture.shape.pos
            else:
                center = body.GetWorldPoint(fixture.shape.pos)

            # Fill circle
            painter.drawEllipse(QPointF(center.x, center.y), radius, radius)

            # Draw line (helps for visualization of how fast and direction wheel is moving)
            _set_painter_solid(painter, Qt.black)
            p0 = QPointF(center.x, center.y)
            p1 = QPointF(center.x + radius*math.cos(body.angle), center.y + radius*math.sin(body.angle))
            painter.drawLine(p0, p1)


def draw_polygon(painter: QPainter, body: b2Body, poly_type: str = '', adjust_painter: bool = True, local=False) -> None:
    """
    Draws a polygon with the given painter. Uses poly_type for determining the fill of the polygon.
    """
    if adjust_painter:
        _set_painter_clear(painter, Qt.black)

    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2PolygonShape):
            poly = []
            # If we are drawing a chassis, determine fill color
            if poly_type == 'chassis':
                adjust = get_boxcar_constant('max_chassis_density') - get_boxcar_constant('min_chassis_density')
                # If the min/max are the same you will get 0 adjust. This is to prevent divide by zero.
                if adjust == 0.0:
                    hue_ratio = 0.0
                else:
                    hue_ratio = (fixture.density - get_boxcar_constant('min_chassis_density')) / adjust
                hue_ratio = min(max(hue_ratio, 0.0), 1.0)  # Just in case you leave the GA unbounded...
                color = QColor.fromHsvF(hue_ratio, 1., .8)
                painter.setBrush(QBrush(color, Qt.SolidPattern))
            
            polygon: b2PolygonShape = fixture.shape
            local_points: List[b2Vec2] = polygon.vertices

            if local:
                world_coords = local_points
            else:
                world_coords = [body.GetWorldPoint(point) for point in local_points]
            for i in range(len(world_coords)):
                p0 = world_coords[i]
                if i == len(world_coords)-1:
                    p1 = world_coords[0]
                else:
                    p1 = world_coords[i+1]

                qp0 = QPointF(*p0)
                qp1 = QPointF(*p1)

                poly.append(qp0)
                poly.append(qp1)
            if poly:
                painter.drawPolygon(QPolygonF(poly))
    

def _set_painter_solid(painter: QPainter, color: Qt.GlobalColor, with_antialiasing: bool = True):
    _set_painter(painter, color, True, with_antialiasing)

def _set_painter_clear(painter: QPainter, color: Qt.GlobalColor, with_antialiasing: bool = True):
    _set_painter(painter, color, False, with_antialiasing)

def _set_painter(painter: QPainter, color: Qt.GlobalColor, fill: bool, with_antialiasing: bool = True):
    painter.setPen(QPen(color, 1./scale, Qt.SolidLine))
    pattern = Qt.SolidPattern if fill else Qt.NoBrush
    painter.setBrush(QBrush(color, pattern))
    if with_antialiasing:
        painter.setRenderHint(QPainter.Antialiasing)


class GameWindow(QWidget):
    def __init__(self, parent, size, world, floor, cars, leader):
        super().__init__(parent)
        self.size = size
        self.world = world
        self.title = 'Test'
        self.top = 150
        self.left = 150
        self.width = 1100
        self.height = 700
        self.floor = floor
        self.leader: Car = leader  # Track the leader
        self.best_car_ever = None
        self.cars = cars
        self.manual_control = False  # W,A,S,D, Z,C, E,R

        # Camera stuff
        self._camera = b2Vec2()
        self._camera_speed = 0.05
        self._camera.x

    def pan_camera_to_leader(self) -> None:
        diff_x = self._camera.x - self.leader.chassis.position.x
        diff_y = self._camera.y - self.leader.chassis.position.y
        self._camera.x -= self._camera_speed * diff_x 
        self._camera.y -= self._camera_speed * diff_y

    def pan_camera_in_direction(self, direction: str, amount: int) -> None:
        diff_x, diff_y = 0, 0
        if direction.lower()[0] == 'u':
            diff_y = -amount
        elif direction.lower()[0] == 'd':
            diff_y = amount
        elif direction.lower()[0] == 'l':
            diff_x = amount
        elif direction.lower()[0] == 'r':
            diff_x = -amount

        self._camera.x -= self._camera_speed * diff_x 
        self._camera.y -= self._camera_speed * diff_y
    def _update(self):
        """
        Main update method used. Called once every (1/FPS) second.
        """
        self.update()


    def _draw_car(self, painter: QPainter, car: Car):
        """
        Draws a car to the window
        """
        for wheel in car.wheels:
            draw_circle(painter, wheel.body)

        draw_polygon(painter, car.chassis, poly_type='chassis')

    def _draw_floor(self, painter: QPainter):
        #@TODO: Make this more efficient. Only need to draw things that are currently on the screen or about to be on screen
        for tile in self.floor.floor_tiles:
            if tile is self.floor.winning_tile:
                painter.setPen(QPen(Qt.black, 1./scale, Qt.SolidLine))
                painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
                painter.setRenderHint(QPainter.Antialiasing)
                local_points: List[b2Vec2] = tile.fixtures[0].shape.vertices
                world_coords = [tile.GetWorldPoint(point) for point in local_points]
                qpoints = [QPointF(coord[0], coord[1]) for coord in world_coords]
                polyf = QPolygonF(qpoints)
                painter.drawPolygon(polyf)
            else:
                draw_polygon(painter, tile)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_border(painter, self.size)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.translate(200 - (self._camera.x * scale) , 250 + (self._camera.y * scale))
        # painter.translate(200,300)
        painter.scale(scale, -scale)
        arr = [Qt.black, Qt.green, Qt.blue]
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        
        self._draw_floor(painter)

        # self.draw_polygon(painter, self.chassis)
        for car in self.cars:
            self._draw_car(painter, car)
        # for fixture in self.chassis.fixtures:
        #     print([self.chassis.GetWorldPoint(vert) for vert in fixture.shape.vertices])

class MainWindow(QMainWindow):
    def __init__(self, world, replay=False):
        super().__init__()
        self.world = world
        self.title = 'Genetic Algorithm - Cars'
        self.top = 150
        self.left = 150
        self.width = 1100
        self.height = 700
        self.max_fitness = 0.0
        self.cars = []
        self.population = Population([])
        self.state = States.FIRST_GEN
        self._next_pop = []  # Used when you are in state 1, i.e. creating new cars from the old population
        self.current_batch = 1
        self.batch_size = get_boxcar_constant('run_at_a_time')
        self.gen_without_improvement = 0
        self.replay = replay

        self.manual_control = False

        
        self.current_generation = 0
        self.leader = None  # What car is leading
        self.num_cars_alive = get_boxcar_constant('run_at_a_time')
        self.batch_size = self.num_cars_alive
        self._total_individuals_ran = 0
        self._offset_into_population = 0  # Used if we display only a certain number at a 
        # Determine whether or not we are in the process of creating random cars.
        # This is used for when we only run so many at a time. For instance if `run_at_a_time` is 20 and
        # `num_parents` is 1500, then we can't just create 1500 cars. Instead we create batches of 20 to 
        # run at a time. This flag is for deciding when we are done with that so we can move on to crossover
        # and mutation.
        self._creating_random_cars = True
        
        # Determine how large the next generation is
        if get_ga_constant('selection_type').lower() == 'plus':
            self._next_gen_size = get_ga_constant('num_parents') + get_ga_constant('num_offspring')
        elif get_ga_constant('selection_type').lower() == 'comma':
            self._next_gen_size = get_ga_constant('num_parents')
        else:
            raise Exception('Selection type "{}" is invalid'.format(get_ga_constant('selection_type')))

        if self.replay:
            global args
            self.floor = Floor(self.world)
            self.state = States.REPLAY
            self.num_replay_inds = len([x for x in os.listdir(args.replay_from_folder) if x.startswith('car_')])
        else:
            self._set_first_gen()
        # self.population = Population(self.cars)
        # For now this is all I'm supporting, may change in the future. There really isn't a reason to use
        # uniform or single point here because all the values have different ranges, and if you clip them, it
        # can make those crossovers useless. Instead just use simulated binary crossover to ensure better crossover.
        self._crossover_bins = np.cumsum([get_ga_constant('probability_SBX')])

        self._mutation_bins = np.cumsum([get_ga_constant('probability_gaussian'),
                                         get_ga_constant('probability_random_uniform')])



        self.init_window()
        self.stats_window.pop_size.setText(str(get_ga_constant('num_parents')))
        self._set_number_of_cars_alive()
        self.game_window.cars = self.cars
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(1000//get_boxcar_constant('fps'))

    def next_generation(self) -> None:
        if self.state == States.NEXT_GEN:
            self.stats_window.pop_size.setText(str(self._next_gen_size))
            self.current_batch = 0
            # Set next state to copy parents if its plus, otherwise comma is just going to create offspring
            if get_ga_constant('selection_type').lower() == 'plus':
                self.state = States.NEXT_GEN_COPY_PARENTS_OVER
            elif get_ga_constant('selection_type').lower() == 'comma':
                self.state = States.NEXT_GEN_CREATE_OFFSPRING
            else:
                raise Exception('Invalid selection_type: "{}"'.format(get_ga_constant('selection_type')))

            self._offset_into_population = 0
            self._total_individuals_ran = 0  # Reset back to the first individual

            self.population.individuals = self._next_pop
            self._next_pop = []  # Reset the next pop

            # Calculate fit
            for individual in self.population.individuals:
                individual.calculate_fitness()

            # Should we save the pop
            if args.save_pop:
                path = os.path.join(args.save_pop, 'pop_gen{}'.format(self.current_generation))
                if os.path.exists(path):
                    raise Exception('{} already exists. This would overwrite everything, choose a different folder or delete it and try again'.format(path))
                os.makedirs(path)
                save_population(path, self.population, settings.settings)
            # Save best? 
            if args.save_best:
                save_car(args.save_best, 'car_{}'.format(self.current_generation), self.population.fittest_individual, settings.settings)

            self._set_previous_gen_avg_fitness()
            self._set_previous_gen_num_winners()
            self._increment_generation()


            # Grab the best individual and compare to best fitness
            best_ind = self.population.fittest_individual
            if best_ind.fitness > self.max_fitness:
                self.max_fitness = best_ind.fitness
                self._set_max_fitness()
                self.gen_without_improvement = 0
            else:
                self.gen_without_improvement += 1
            # Set text for gen improvement
            self.stats_window.gens_without_improvement.setText(str(self.gen_without_improvement))

            # Set the population to be just the parents allowed for reproduction. Only really matters if `plus` method is used.
            # If `plus` method is used, there can be more individuals in the next generation, so this limits the number of parents.
            self.population.individuals = elitism_selection(self.population, get_ga_constant('num_parents'))

            random.shuffle(self.population.individuals)
            
            # Parents + offspring selection type ('plus')
            if get_ga_constant('selection_type').lower() == 'plus':
                # Decrement lifespan
                for individual in self.population.individuals:
                    individual.lifespan -= 1

        num_offspring = min(self._next_gen_size - len(self._next_pop), get_boxcar_constant('run_at_a_time'))
        self.cars = self._create_num_offspring(num_offspring)
        # Set number of cars alive
        self.num_cars_alive = len(self.cars)
        self.batch_size = self.num_cars_alive
        self.current_batch += 1
        self._set_number_of_cars_alive()
        self._next_pop.extend(self.cars)  # Add to next_pop
        self.game_window.cars = self.cars
        leader = self.find_new_leader()
        self.leader = leader
        self.game_window.leader = leader
        if get_ga_constant('selection_type').lower() == 'comma':
            self.state = States.NEXT_GEN_CREATE_OFFSPRING
        elif get_ga_constant('selection_type').lower() == 'plus' and self._offset_into_population >= len(self.population.individuals):
            self.state = States.NEXT_GEN_CREATE_OFFSPRING
        

        # Set the next pop
        # random.shuffle(next_pop)
        # self.population.individuals = next_pop




    def init_window(self):
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)

        # Create stats_window
        self.stats_window = StatsWindow(self.centralWidget, (800, 200))
        self.stats_window.setGeometry(QRect(0, 500, 800, 200))
        self.stats_window.setObjectName('stats_window')

        # Create game_window - where the game is played
        self.game_window = GameWindow(self.centralWidget, (800, 500), self.world, self.floor, self.cars, self.leader)
        self.game_window.setGeometry(QRect(0, 0, 800, 500))
        self.game_window.setObjectName('game_window')

        # Create settings_window - just a bunch of settings of the game and how they were defined, etc.
        self.settings_window = SettingsWindow(self.centralWidget, (300, 700))
        self.settings_window.setGeometry(QRect(800, 0, 300, 700))
        self.settings_window.setObjectName('settings_window')
        

        # Add main window
        self.main_window = QWidget(self)
        self.main_window.setGeometry(QRect(0, 0, 800, 500))
        self.main_window.setObjectName('main_window')

        if get_boxcar_constant('show'):
            self.show()

    def find_new_leader(self) -> Optional[Car]:
        max_x = -1
        leader = None
        for car in self.cars:
            # Can't be a leader if you're dead
            if not car.is_alive:
                continue

            car_pos = car.position.x
            if car_pos > max_x:
                leader = car
                max_x = car_pos

        return leader

    def _set_previous_gen_avg_fitness(self) -> None:
        avg_fitness = sum(ind.fitness for ind in self.population.individuals) / len(self.population.individuals)
        self.stats_window.average_fitness_last_gen.setText('{:.2f}'.format(avg_fitness))

    def _set_previous_gen_num_winners(self) -> None:
        winners = sum(ind.is_winner for ind in self.population.individuals)
        self.stats_window.num_solved_last_gen.setText(str(winners))

    def _create_num_offspring(self, number_of_offspring) -> List[Individual]:
        """
        This is a helper function to decide whether to grab from current pop or create new offspring.

        Creates a number of offspring from the current population. This assumes that the current population are all able to reproduce.
        This is broken up from the main next_generation function so that we can create N individuals at a time if needed without going
        to the next generation. Mainly used if `run_at_a_time` is < the number of individuals that are in the next generation.
        """
        next_pop: List[Individual] = []
        #@TODO: comment this to new state
        # If the selection type is plus, then it means certain individuals survive to the next generation, so we need
        # to grab those first before we create new ones
        # if get_ga_constant('selection_type').lower() == 'plus' and len(self._next_pop) < get_ga_constant('num_parents'):
        if self.state == States.NEXT_GEN_COPY_PARENTS_OVER:
            # Select the subset of the individuals to bring to the next gen
            increment = 0  # How much did the offset increment by
            for idx in range(self._offset_into_population, len(self.population.individuals)):
            # for individual in self.population.individuals[self._offset_into_population: self._offset_into_population + number_of_offspring]:
                    individual = self.population.individuals[idx]
                    increment += 1  # For offset
                    world = self.world
                    wheel_radii = individual.wheel_radii
                    wheel_densities = individual.wheel_densities
                    #wheel_motor_speeds = individual.wheel_motor_speeds
                    chassis_vertices = individual.chassis_vertices
                    chassis_densities = individual.chassis_densities
                    winning_tile = individual.winning_tile
                    lowest_y_pos = individual.lowest_y_pos
                    lifespan = individual.lifespan

                    # If the individual is still alive, they survive
                    if lifespan > 0:
                        car = Car(world, 
                                wheel_radii, wheel_densities,# wheel_motor_speeds,       # Wheel
                                chassis_vertices, chassis_densities,                    # Chassis
                                winning_tile, lowest_y_pos,
                                lifespan)
                        next_pop.append(car)
                        # Check to see if we've added enough parents. The reason we check here is if you requet 5 parents but
                        # 2/5 are dead, then you need to keep going until you get 3 good ones.
                        if len(next_pop) == number_of_offspring:
                            break
                    else:
                        print("Oh dear, you're dead")
            # Increment offset for the next time
            self._offset_into_population += increment
            # If there weren't enough parents that made it to the new generation, we just accept it and move on.
            # Since the lifespan could have reached 0, you are not guaranteed to always have the same number of parents copied over.
            if self._offset_into_population >= len(self.population.individuals):
                self.state = States.NEXT_GEN_CREATE_OFFSPRING
        # Otherwise just perform crossover with the current population and produce num_of_offspring
        # @NOTE: The state, even if we got here through State.NEXT_GEN or State.NEXT_GEN_COPY_PARENTS_OVER is now
        # going to switch to State.NEXT_GEN_CREATE_OFFSPRING based off this else condition. It's not set here, but
        # rather at the end of new_generation
        else:
            # Keep adding children until we reach the size we need
            while len(next_pop) < number_of_offspring:
                # Tournament crossover
                if get_ga_constant('crossover_selection').lower() == 'tournament':
                    p1, p2 = tournament_selection(self.population, 2, get_ga_constant('tournament_size'))
                # Roulette
                elif get_ga_constant('crossover_selection').lower() == 'roulette':
                    p1, p2 = roulette_wheel_selection(self.population, 2)
                else:
                    raise Exception('crossover_selection "{}" is not supported'.format(get_ga_constant('crossover_selection').lower()))

                # Crossover
                c1_chromosome, c2_chromosome = self._crossover(p1.chromosome, p2.chromosome)

                # Mutation
                self._mutation(c1_chromosome)
                self._mutation(c2_chromosome)

                # Don't let the chassis density become <=0. It is bad
                smart_clip(c1_chromosome)
                smart_clip(c2_chromosome)

                # Create children from the new chromosomes
                c1 = Car.create_car_from_chromosome(p1.world, p1.winning_tile, p1.lowest_y_pos, get_ga_constant('lifespan'), c1_chromosome)
                c2 = Car.create_car_from_chromosome(p2.world, p2.winning_tile, p2.lowest_y_pos, get_ga_constant('lifespan'), c2_chromosome)

                # Add children to the next generation
                next_pop.extend([c1, c2])

        # Return the next population that will play. Remember, this can be a subset of the overall population since
        # those parents still exist.
        return next_pop
    
    def _increment_generation(self) -> None:
        """
        Increments the generation and sets the label
        """
        self.current_generation += 1
        self.stats_window.generation.setText("<font color='red'>" + str(self.current_generation + 1) + '</font>')

    def _set_first_gen(self) -> None:
        """
        Sets the first generation, i.e. random cars
        """
        # Create the floor if FIRST_GEN, but not if it's in progress
        if self.state == States.FIRST_GEN:
            self.floor = Floor(self.world)

        # We are now in progress of creating the first gen
        self.state = States.FIRST_GEN_IN_PROGRESS

        # Initialize cars randomly
        self.cars = []
        # Determine how many cars to make
        num_to_create = None
        if get_ga_constant('num_parents') - self._total_individuals_ran >= get_boxcar_constant('run_at_a_time'):
            num_to_create = get_boxcar_constant('run_at_a_time')
        else:
            num_to_create = get_ga_constant('num_parents') - self._total_individuals_ran

        # @NOTE that I create the subset of cars
        for i in range(num_to_create):
            car = create_random_car(self.world, self.floor.winning_tile, self.floor.lowest_y)
            self.cars.append(car)
        
        self._next_pop.extend(self.cars)  # Add the cars to the next_pop which is used by population

        leader = self.find_new_leader()
        self.leader = leader

        # Time to go to new state?
        if self._total_individuals_ran == get_ga_constant('num_parents'):
            self._creating_random_cars = False
            self.state = States.NEXT_GEN

    def _set_number_of_cars_alive(self) -> None:
        """
        Set the number of cars alive on the screen label
        """
        total_for_gen = get_ga_constant('num_parents')
        if self.current_generation > 0:
            total_for_gen = self._next_gen_size
        num_batches = math.ceil(total_for_gen / get_boxcar_constant('run_at_a_time'))
        text = '{}/{} (batch {}/{})'.format(self.num_cars_alive, self.batch_size, self.current_batch, num_batches)
        self.stats_window.current_num_alive.setText(text)

    def _set_max_fitness(self) -> None:
        """
        Sets the max fitness label
        """
        self.stats_window.best_fitness.setText(str(int(self.max_fitness)))


    def _update(self) -> None:
        """
        Called once every 1/FPS to update everything
        """
        for car in self.cars:
            if not car.is_alive:
                continue
            # Did the car die/win?
            if not car.update():
                # Another individual has finished
                self._total_individuals_ran += 1
                # Decrement the number of cars alive
                self.num_cars_alive -= 1
                self._set_number_of_cars_alive()

                # If the car that just died/won was the leader, we need to find a new one
                if car == self.leader:
                    leader = self.find_new_leader()
                    self.leader = leader
                    self.game_window.leader = leader
            else:
                if not self.leader:
                    self.leader = leader
                    self.game_window.leader = leader
                else:
                    car_pos = car.position.x
                    if car_pos > self.leader.position.x:
                        self.leader = car
                        self.game_window.leader = car
        # If the leader is valid, then just pan to the leader
        if not self.manual_control and self.leader:
            self.game_window.pan_camera_to_leader()
        # If there is not a leader then the generation is over OR the next group of N need to run
        if not self.leader:
            # Replay state
            if self.state == States.REPLAY:
                name = 'car_{}.npy'.format(self.current_generation)
                car = load_car(self.world, self.floor.winning_tile, self.floor.lowest_y, np.inf, args.replay_from_folder, name)
                self.cars = [car]
                self.game_window.cars = self.cars
                self.leader = self.find_new_leader()
                self.game_window.leader = self.leader
                self.current_generation += 1
                txt = 'Replay {}/{}'.format(self.current_generation, self.num_replay_inds)
                self.stats_window.generation.setText("<font color='red'>Replay</font>")
                self.stats_window.pop_size.setText("<font color='red'>Replay</font>")
                self.stats_window.current_num_alive.setText("<font color='red'>" + txt + '</font>')
                return
            # Are we still in the process of just random creation?
            if self.state in (States.FIRST_GEN, States.FIRST_GEN_IN_PROGRESS):
                self._set_first_gen()
                self.game_window.leader = self.leader
                self.game_window.cars = self.cars
                self.num_cars_alive = len(self.cars)
                self.batch_size = self.num_cars_alive
                self.current_batch += 1
                self._set_number_of_cars_alive()
                return
            # Next N individuals need to run
            # We already have a population defined and we need to create N cars to run
            elif self.state == States.NEXT_GEN_CREATE_OFFSPRING:
                num_create = min(self._next_gen_size - self._total_individuals_ran, get_boxcar_constant('run_at_a_time'))

                self.cars = self._create_num_offspring(num_create)
                self.batch_size = len(self.cars)
                self.num_cars_alive = len(self.cars)
                
                self._next_pop.extend(self.cars)  # These cars will now be part of the next pop
                self.game_window.cars = self.cars
                leader = self.find_new_leader()
                self.leader = leader
                self.game_window.leader = leader
                # should we go to the next state? 
                if (self.current_generation == 0 and (self._total_individuals_ran >= get_ga_constant('num_parents'))) or\
                    (self.current_generation > 0 and (self._total_individuals_ran >= self._next_gen_size)):
                    self.state = States.NEXT_GEN
                else:
                    self.current_batch += 1
                    self._set_number_of_cars_alive()
                return
            elif self.state in (States.NEXT_GEN, States.NEXT_GEN_COPY_PARENTS_OVER, States.NEXT_GEN_CREATE_OFFSPRING):
                self.next_generation()
                return
            else:
                raise Exception('You should not be able to get here, but if you did, awesome! Report this to me if you actually get here.')

        self.world.ClearForces()

        # Update windows
        self.game_window._update()

        # Step
        self.world.Step(1./FPS, 10, 6)

    def _crossover(self, p1_chromosome: np.ndarray, p2_chromosome: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Perform crossover between two parent chromosomes and return TWO child chromosomes
        """
        rand_crossover = random.random()
        crossover_bucket = np.digitize(rand_crossover, self._crossover_bins)

        # SBX
        if crossover_bucket == 0:
            c1_chromosome, c2_chromosome = SBX(p1_chromosome, p2_chromosome, get_ga_constant('SBX_eta'))
        else:
            raise Exception('Unable to determine valid crossover based off probabilities')

        return c1_chromosome, c2_chromosome

    def _mutation(self, chromosome: np.ndarray) -> None:
        """
        Randomly decide if we should perform mutation on a gene within the chromosome. This is done in place
        """
        rand_mutation = random.random()
        mutation_bucket = np.digitize(rand_mutation, self._mutation_bins)

        # Gaussian
        if mutation_bucket == 0:
            mutation_rate = get_ga_constant('mutation_rate')
            if get_ga_constant('mutation_rate_type').lower() == 'dynamic':
                mutation_rate = mutation_rate / math.sqrt(self.current_generation + 1)
            gaussian_mutation(chromosome, mutation_rate, scale=get_ga_constant('gaussian_mutation_scale'))


        # Random uniform
        elif mutation_bucket == 1:
            #@TODO: add to this
            pass
        else:
            raise Exception('Unable to determine valid mutation based off probabilities')
    
    def keyPressEvent(self, event):
        global scale, default_scale
        key = event.key()
        # Zoom in
        if key == Qt.Key_C:
            scale += 1
        # Zoom out
        elif key == Qt.Key_Z:
            scale -= 1
            scale = max(scale, 1)
        elif key in (Qt.Key_W, Qt.Key_A, Qt.Key_S, Qt.Key_D):
            self.manual_control = True
            if key == Qt.Key_W:
                direction = 'u'
            elif key == Qt.Key_A:
                direction = 'l'
            elif key == Qt.Key_S:
                direction = 'd'
            elif key == Qt.Key_D:
                direction = 'r'
            self.game_window.pan_camera_in_direction(direction, 5)
        # Reset to normal control
        elif key == Qt.Key_R:
            self.manual_control = False
        elif key == Qt.Key_E:
            scale = default_scale

    def closeEvent(self, event):
        global args
        if args.save_pop_on_close:
            save_population(args.save_pop_on_close, self.population, settings.settings)


def save_population(population_folder: str, population: Population, settings: Dict[str, Any]) -> None:
    """
    Saves all cars in the population
    """
    # @NOTE: self.population.individuals is not the same as self.cars
    # self.cars are the cars that run at a given time for the BATCH
    # self.population.individuals is the ENTIRE population of chromosomes.
    # This will not save anything the first generation since those are just random cars and nothing has
    # been added to the population yet.
    for i, car in enumerate(population.individuals):
        name = 'car_{}'.format(i)
        print('saving {} to {}'.format(name, population_folder))
        save_car(population_folder, name, car, settings)

def parse_args():
    parser = argparse.ArgumentParser(description='PyGenoCar V1.0')
    # Save
    parser.add_argument('--save-best', dest='save_best', type=str, help='destination folder to save best individiuals after each gen')
    parser.add_argument('--save-pop', dest='save_pop', type=str, help='destination folder to save population after each gen')
    parser.add_argument('--save-pop-on-close', dest='save_pop_on_close', type=str, help='destination to save the population when program exits')

    # Replay @NOTE: Only supports replaying the best individual. Not a list of populations.
    parser.add_argument('--replay-from-folder', dest='replay_from_folder', type=str, help='destination to replay individuals from')

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    global args
    args = parse_args()
    replay = False
    if args.replay_from_folder:
        if 'settings.pkl' not in os.listdir(args.replay_from_folder):
            raise Exception('settings.pkl not found within {}'.format(args.replay_from_folder))
        settings_path = os.path.join(args.replay_from_folder, 'settings.pkl')
        with open(settings_path, 'rb') as f:
            settings.settings = pickle.load(f)
        replay = True


    world = b2World(get_boxcar_constant('gravity'))
    App = QApplication(sys.argv)
    window = MainWindow(world, replay)
    sys.exit(App.exec_())