from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from typing import Optional, Tuple, List
from Box2D import *
import random
from boxcar.floor import Floor
from boxcar.car import Car, create_random_car, clip_chromosome, clip_chromosome_to_zero, set_chromosome_bounding_vertices_to_zero, smart_clip
from genetic_algorithm.population import Population
from genetic_algorithm.crossover import simulated_binary_crossover as SBX
from genetic_algorithm.crossover import single_point_binary_crossover as SPBX
from genetic_algorithm.mutation import gaussian_mutation
from genetic_algorithm.selection import elitism_selection, roulette_wheel_selection, tournament_selection
from settings import get_boxcar_constant, get_ga_constant
from windows import SettingsWindow, StatsWindow, draw_border

import sys
import time
from copy import deepcopy
import numpy as np
import math

g_best_car = None

## Constants ##
scale = 70
default_scale = 70
FPS = 60


def draw_circle(painter: QPainter, body: b2Body, local=False) -> None:
    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2CircleShape):
            # Set the color of the circle to be based off wheel density
            adjust = get_boxcar_constant('max_wheel_density') - get_boxcar_constant('min_wheel_density')
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
    if adjust_painter:
        _set_painter_clear(painter, Qt.black)

    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2PolygonShape):
            poly = []
            # If we are drawing a chassis, determine fill color
            if poly_type == 'chassis':
                adjust = get_boxcar_constant('max_chassis_density') - get_boxcar_constant('min_chassis_density')
                hue_ratio = (fixture.density - get_boxcar_constant('min_chassis_density')) / adjust
                hue_ratio = min(max(hue_ratio, 0.0), 1.0)  # Just in case you leave the GA unbounded...
                try:
                    color = QColor.fromHsvF(hue_ratio, 1., .8)
                except:
                    print(hue_ratio)
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
                # painter.drawLine(qp0, qp1)
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
        self.manual_control = False

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
    def __init__(self, world):
        super().__init__()
        self.world = world
        self.title = 'Genetic Algorithm - Cars'
        self.top = 150
        self.left = 150
        self.width = 1100
        self.height = 700
        self.max_fitness = 0.0

        self.manual_control = False

        
        self.current_generation = 0
        self.leader = None  # What car is leading
        self.num_cars_alive = get_ga_constant('num_parents')
        self._current_individual = 0
        
        # Determine how large the next generation is
        if get_ga_constant('selection_type').lower() == 'plus':
            self._next_gen_size = get_ga_constant('num_parents') + get_ga_constant('num_offspring')
        elif get_ga_constant('selection_type').lower() == 'comma':
            self._next_gen_size = get_ga_constant('num_parents')
        else:
            raise Exception('Selection type "{}" is invalid'.format(get_ga_constant('selection_type')))

        self._set_first_gen()
        self.population = Population(self.cars)
        # For now this is all I'm supporting, may change in the future. There really isn't a reason to use
        # uniform or single point here because all the values have different ranges, and if you clip them, it
        # can make those crossovers useless. Instead just use simulated binary crossover to ensure better crossover.
        self._crossover_bins = np.cumsum([get_ga_constant('probability_SBX')])

        self._mutation_bins = np.cumsum([get_ga_constant('probability_gaussian'),
                                         get_ga_constant('probability_random_uniform')])



        self.init_window()
        self.game_window.cars = self.cars
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(1000//get_boxcar_constant('fps'))

    

    def next_generation(self) -> None:
        self._increment_generation()
        self._current_individual = 0  # Reset back to the first individual

        # Calculate fit
        for individual in self.population.individuals:
            individual.calculate_fitness()
        
        # Grab the best individual and compare to best fitness
        best_ind = self.population.fittest_individual
        if best_ind.fitness > self.max_fitness:
            self.max_fitness = best_ind.fitness
            self._set_max_fitness()


        self.population.individuals = elitism_selection(self.population, get_ga_constant('num_parents'))

        random.shuffle(self.population.individuals)
        next_pop: List[Car] = []

        # Parents + offspring selection type ('plus')
        if get_ga_constant('selection_type').lower() == 'plus':
            # Decrement lifespan
            for individual in self.population.individuals:
                individual.lifespan -= 1

            for individual in self.population.individuals:
                world = self.world
                wheel_radii = individual.wheel_radii
                wheel_densities = individual.wheel_densities
                chassis_vertices = individual.chassis_vertices
                chassis_densities = individual.chassis_densities
                winning_tile = individual.winning_tile
                lowest_y_pos = individual.lowest_y_pos
                lifespan = individual.lifespan

                # If the individual is still alive, they survive
                if lifespan > 0:
                    car = Car(world, 
                              wheel_radii, wheel_densities,         # Wheel
                              chassis_vertices, chassis_densities,  # Chassis
                              winning_tile, lowest_y_pos,
                              lifespan)
                    next_pop.append(car)

        # Keep adding children until we reach the size we need
        while len(next_pop) < self._next_gen_size:
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

            smart_clip(c1_chromosome)
            smart_clip(c2_chromosome)

            # Create children from the new chromosomes
            c1 = Car.create_car_from_chromosome(p1.world, p1.winning_tile, p1.lowest_y_pos, c1_chromosome)
            c2 = Car.create_car_from_chromosome(p2.world, p2.winning_tile, p2.lowest_y_pos, c2_chromosome)

            # Add children to the next generation
            next_pop.extend([c1, c2])

        # Set the next pop
        random.shuffle(next_pop)
        self.population.individuals = next_pop




    def init_window(self):
        self.centralWidget = QWidget(self)
        self.setCentralWidget(self.centralWidget)
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)

        # Create the best_car_window
        # self.best_car_window = BestCarWindow(self.centralWidget, (300, 200))
        # self.best_car_window.setGeometry(QRect(800, 500, 300, 200))
        # self.best_car_window.setObjectName('best_car_window')

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
    
    def _increment_generation(self) -> None:
        self.current_generation += 1
        self.stats_window.generation.setText("<font color='red'>" + str(self.current_generation + 1) + '</font>')

    def _set_first_gen(self) -> None:
        # Create the floor
        self.floor = Floor(self.world)

        # Initialize cars randomly
        self.cars = []
        for i in range(get_ga_constant('num_parents')):
            car = create_random_car(self.world, self.floor.winning_tile, self.floor.lowest_y)
            self.cars.append(car)

        leader = self.find_new_leader()
        self.leader = leader

    def _set_number_of_cars_alive(self) -> None:
        self.stats_window.current_num_alive.setText(str(self.num_cars_alive))

    def _set_max_fitness(self) -> None:
        self.stats_window.best_fitness.setText(str(int(self.max_fitness)))


    def _update(self) -> None:
        for car in self.cars:
            # if car is self.leader and self.leader:
            #     print(car.linear_velocity)
            if not car.is_alive:
                continue
            # Did the car die/win?
            if not car.update():
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
        # If the leader is None, then that means no new leader was found because everyone is dead.
        # Need a new generation then
        if not self.leader:
            self.next_generation()
            self.cars = self.population.individuals
            self.game_window.cars = self.population.individuals
            leader = self.find_new_leader()
            self.leader = leader
            self.game_window.leader = leader
            return

        self.world.ClearForces()

        # Update windows
        self.game_window._update()
        # if self._are_all_cars_dead():
        #     print('eeeeeeeeeek')

        # Step
        self.world.Step(1./FPS, 10, 6)


    def _are_all_cars_dead(self) -> bool:
        for car in self.cars:
            if car.is_alive:
                return False

        return True

    def _crossover(self, p1_chromosome: np.ndarray, p2_chromosome: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        rand_crossover = random.random()
        crossover_bucket = np.digitize(rand_crossover, self._crossover_bins)

        # SBX
        if crossover_bucket == 0:
            c1_chromosome, c2_chromosome = SBX(p1_chromosome, p2_chromosome, get_ga_constant('SBX_eta'))
        else:
            raise Exception('Unable to determine valid crossover based off probabilities')

        return c1_chromosome, c2_chromosome

    def _mutation(self, chromosome: np.ndarray) -> None:
        rand_mutation = random.random()
        mutation_bucket = np.digitize(rand_mutation, self._mutation_bins)

        # Gaussian
        if mutation_bucket == 0:
            gaussian_mutation(chromosome, get_ga_constant('mutation_rate'), scale=get_ga_constant('gaussian_mutation_scale'))


        # Random uniform
        elif mutation_bucket == 1:
            #@TODO: add to this
            pass
        else:
            raise Exception('Unable to determine valid mutation based off probabilities')
    
    def keyPressEvent(self, event):
        global scale, default_scale
        key = event.key()
        if key == Qt.Key_C:
            scale += 1
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
        elif key == Qt.Key_R:
            self.manual_control = False
        elif key == Qt.Key_E:
            scale = default_scale


if __name__ == "__main__":
    world = b2World(get_boxcar_constant('gravity'))
    App = QApplication(sys.argv)
    window = MainWindow(world)
    sys.exit(App.exec_())