from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from boxcar.floor import *
from boxcar.car import *
from settings import *
from windows import SettingsWindow, StatsWindow, draw_border

import sys
import time
from typing import Tuple
from copy import deepcopy

g_best_car = None

## Constants ##
scale = 70
FPS = 60


def draw_circle(painter: QPainter, body: b2Body, local=False) -> None:
    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2CircleShape):
            # Set the color of the circle to be based off wheel density
            adjust = get_boxcar_constant('max_wheel_density') - get_boxcar_constant('min_wheel_density')
            hue_ratio = (fixture.density - get_boxcar_constant('min_wheel_density')) / adjust
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
    def __init__(self, parent, size, world):
        super().__init__(parent)
        self.size = size
        self.world = world
        self.title = 'Test'
        self.top = 150
        self.left = 150
        self.width = 1100
        self.height = 700
        self.floor = Floor(self.world)
        self.chassis = create_random_chassis(self.world)
        self.leader: Car = None  # Track the leader
        self.best_car_ever = None
        self.cars = None
        self.new_generation()

        # Camera stuff
        self._camera = b2Vec2()
        self._camera_speed = 0.05
        self._camera.x

        # Create a timer to run given the desired FPS

    def _update(self):
        """
        Main update method used. Called once every (1/FPS) second.
        """

        for car in self.cars:
            if not car.is_alive:
                continue

            if not car.update():
                if car == self.leader:
                    self.find_new_leader()
            else:
                car_pos = car.position.x
                if car_pos > self.leader.position.x:
                    self.leader = car


        # Did all the cars die?
        if not self.leader:
            print('new generation')
            self.new_generation()
        else:
            diff_x = self._camera.x - self.leader.chassis.position.x
            diff_y = self._camera.y - self.leader.chassis.position.y
            self._camera.x -= self._camera_speed * diff_x #diff_x # self._camera_speed * diff_x
            self._camera.y -= self._camera_speed * diff_y #diff_y # self._camera_speed * diff_y
        
        self.world.ClearForces()
        self.update()

        self.world.Step(1./FPS, 10, 6)

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
        painter.translate(200 - (self._camera.x * scale) , 200 + (self._camera.y * scale))
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

    def new_generation(self):
        global g_best_car
        if self.cars:
            best_car = None
            # If we have not found a best car yet, compare just the current generation
            if not g_best_car:
                best_pos = -1
                for car in self.cars:
                    if car.max_position > best_pos:
                        best_car = car
                        best_pos = car.max_position
            else:
                best_car = g_best_car
                for car in self.cars:
                    if car.max_position > best_car.max_position:
                        best_car = car

            if best_car != g_best_car:
                g_best_car = best_car.clone()

        print(g_best_car)

        self.cars = [create_random_car(self.world, self.floor.winning_tile, self.floor.lowest_y) for _ in range(get_boxcar_constant('num_cars_in_generation'))]
        g_best_car = self.cars[0].clone()
        self.find_new_leader()

    def find_new_leader(self):
        max_x = -1
        leader: Car = None
        for car in self.cars:
            # Can't be a leader if you're dead
            if not car.is_alive:
                continue

            car_pos = car.position.x
            if car_pos > max_x:
                leader = car
                max_x = car_pos

        self.leader = leader

class MainWindow(QMainWindow):
    def __init__(self, world):
        super().__init__()
        self.world = world
        self.title = 'Genetic Algorithm - Cars'
        self.top = 150
        self.left = 150
        self.width = 1100
        self.height = 700

        self.init_window()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(1000//FPS)

    def _update(self) -> None:
        # Update windows
        self.game_window._update()

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

        self.game_window = GameWindow(self.centralWidget, (800, 500), self.world)
        self.game_window.setGeometry(QRect(0, 0, 800, 500))
        self.game_window.setObjectName('game_window')

        # self.ga_window = GeneticAlgorithmWindow(self.centralWidget, (300, 500))
        # self.ga_window.setGeometry(QRect(800, 0, 300, 500))
        # self.ga_window.setObjectName('ga_window')

        self.settings_window = SettingsWindow(self.centralWidget, (300, 700))
        self.settings_window.setGeometry(QRect(800, 0, 300, 700))
        self.settings_window.setObjectName('settings_window')
        

        # Add stats window
        self.stats_window = QWidget(self)
        self.stats_window.setGeometry(QRect(0, 500, 1000, 200))
        self.stats_window.setObjectName('stats_window')

        # Add main window
        self.main_window = QWidget(self)
        self.main_window.setGeometry(QRect(0, 0, 800, 500))
        self.main_window.setObjectName('main_window')

        self.show()

if __name__ == "__main__":
    world = b2World(get_boxcar_constant('gravity'))
    App = QApplication(sys.argv)
    window = MainWindow(world)
    sys.exit(App.exec_())