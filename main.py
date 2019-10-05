from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from boxcar.floor import *
from boxcar.car import *
from boxcar.utils import *
from windows import SettingsWindow

import sys
import time
from typing import Tuple
from copy import deepcopy

g_best_car = None

## Constants ##
scale = 70
FPS = 60

def draw_border(painter: QPainter, size: Tuple[float, float]) -> None:
    painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    painter.setBrush(QBrush(Qt.green, Qt.NoBrush))
    painter.setRenderHint(QPainter.Antialiasing)
    points = [(0, 0), (size[0], 0), (size[0], size[1]), (0, size[1])]
    qpoints = [QPointF(point[0], point[1]) for point in points]
    polygon = QPolygonF(qpoints)
    painter.drawPolygon(polygon)

def draw_circle(painter: QPainter, body: b2Body, local=False) -> None:
    for fixture in body.fixtures:
        if isinstance(fixture.shape, b2CircleShape):
            _set_painter_solid(painter, Qt.black)
            radius = fixture.shape.radius
            if local:
                center = fixture.shape.pos
            else:
                center = body.GetWorldPoint(fixture.shape.pos)

            # Fill circle
            painter.drawEllipse(QPointF(center.x, center.y), radius, radius)

            # Draw line (helps for visualization of how fast and direction wheel is moving)
            _set_painter_solid(painter, Qt.green)
            p0 = QPointF(center.x, center.y)
            p1 = QPointF(center.x + radius*math.cos(body.angle), center.y + radius*math.sin(body.angle))
            painter.drawLine(p0, p1)


def draw_polygon(painter: QPainter, body: b2Body, poly_type: str = '', adjust_painter: bool = True, local=False) -> None:
    if adjust_painter:
        _set_painter_solid(painter, Qt.black)
    for fixture in body.fixtures:
        poly = []
        # If we are drawing a chassis, determine fill color
        if poly_type == 'chassis':
            adjust = get_boxcar_constant('max_chassis_density') - get_boxcar_constant('min_chassis_density')
            hue_ration = (fixture.density - get_boxcar_constant('min_chassis_density')) / adjust
            color = QColor.fromHsvF(hue_ration, 1., .8)
            painter.setBrush(QBrush(color, Qt.SolidPattern))
        if isinstance(fixture.shape, b2PolygonShape):
            polygon: b2PolygonShape = fixture.shape
            local_points: List[b2Vec2] = polygon.vertices
            # poly = []
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
    painter.setPen(QPen(color, 1./scale, Qt.SolidLine))
    painter.setBrush(QBrush(color, Qt.SolidPattern))
    if with_antialiasing:
        painter.setRenderHint(QPainter.Antialiasing)


class ColorGradient(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self. size = size

    


class StatsWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size

        font = QtGui.QFont('Times', 11, QtGui.QFont.Normal)
        font_bold = QtGui.QFont('Times', 11, QtGui.QFont.Bold)

        # Create a grid layout to keep track of certain stats
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)

    def paintEvent(self, event):
        painter = QPainter(self)
        draw_border(painter, self.size)


class BestCarWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size
        global g_best_car
        # self.best_car = None
        # Create a timer to run given the desired FPS
        self._timer = QTimer()
        self._timer.timeout.connect(self.update)
        self._timer.start(1000//FPS)
        

    def paintEvent(self, event):
        global g_best_car
        painter = QPainter(self)
        draw_border(painter, self.size)
        painter.translate(150, 110)
        painter.scale(50, -50)
        if g_best_car:
            for wheel in g_best_car.wheels:
                draw_circle(painter, wheel.body, local=False)

            draw_polygon(painter, g_best_car.chassis, local=False)
        else:
            pass



class GeneticAlgorithmWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size
        self.ga_settings = None
        self._ga_stats_edits = {}

        self.init_window()

    def _create_ga_row_edit(self, entry: str, text: str, is_range: bool = False) -> None:
        label = QLabel()
        label.setText(text)
        edit = QLineEdit()
        if entry not in boxcar_constant and not is_range:
            raise Exception('If entry is not a range, it must be named the same as defined in boxcar_constant')
        elif entry in self._ga_stats_edits:
            raise Exception('Entry already exists')
        else:
            value = None
            if is_range:
                # Find '_range' and set idx
                name = entry[:entry.index('_range')]
                # Find the 'min_name' and 'max_name' from the constants
                min_name = 'min_' + name
                max_name = 'max_' + name
                if min_name not in boxcar_constant:
                    raise Exception('{} must be defined in boxcar_constant'.format(min_name))
                if max_name not in boxcar_constant:
                    raise Exception('{} must be defined in boxcar_constant'.format(max_name))
                # Format value
                value = '{}, {}'.format(get_boxcar_constant(min_name),
                                        get_boxcar_constant(max_name))
            else:
                value = str(get_boxcar_constant(entry))

            edit.setText(value)
            self._ga_stats_edits[entry] = edit
            self.ga_settings.addRow(label, self._ga_stats_edits[entry])

    def init_window(self):
        # self.scroll_area = QScrollArea(self)
        self.ga_settings = QFormLayout()
        blank_label = QLabel().setText('')
        ### Car Specific Edits ###
        car_specific_label = QLabel()
        car_specific_label.setText('Car Specific Edits:')
        self.ga_settings.addRow(car_specific_label, blank_label)
        # Number of wheels range
        self._create_ga_row_edit('num_wheels_range', 'Num Wheels (Range):', is_range=True)    
        # Wheel radius range
        self._create_ga_row_edit('wheel_radius_range', 'Wheel Radius (Range):', is_range=True)
        # Wheel density range
        self._create_ga_row_edit('wheel_density_range', 'Wheel Density (Range):', is_range=True)
        # Chassis axis range
        self._create_ga_row_edit('chassis_axis_range', 'Chassis Axis (Range):', is_range=True)
        # Max tries
        self._create_ga_row_edit('car_max_tries', 'Max Tries (int):')
        ### Floor Specific Edits ###
        floor_specific_label = QLabel()
        floor_specific_label.setText('Floor Specific Edits:')
        self.ga_settings.addRow(floor_specific_label, blank_label)
        # Floor tile height
        self._create_ga_row_edit('floor_tile_height', 'Tile Height (float):')
        # Floor tile width
        self._create_ga_row_edit('floor_tile_width', 'Tile Width (float):')
        # Floor type
        self._create_ga_row_edit('floor_creation_type', 'Floor type (str):')
        # Max floor tiles
        self._create_ga_row_edit('max_floor_tiles', 'Max Tiles (int):')
        ### Floor - Gaussian ###
        floor_gaussian_specific_label = QLabel()
        floor_gaussian_specific_label.setText("Gaussian Specific\n( Floor type = 'gaussian' )")
        self.ga_settings.addRow(floor_gaussian_specific_label, blank_label)
        # mu tile angle
        self._create_ga_row_edit('tile_angle_mu', 'Mean Tile Angle:')
        # std tile angle
        self._create_ga_row_edit('tile_angle_std', 'Std Tile Angle:')
        ### Floor - Ramp ###
        floor_ramp_specific_label = QLabel()
        floor_ramp_specific_label.setText("Ramp Specific\n( Floor type = 'ramp' )")
        self.ga_settings.addRow(floor_ramp_specific_label, blank_label)
        # Ramp constant angle
        self._create_ga_row_edit('ramp_constant_angle', 'Ramp Constant Angle:')
        # Ramp constant distance
        self._create_ga_row_edit('ramp_constant_distance', 'Ramp Constant Distance:')
        # Ramp increasing angle
        self._create_ga_row_edit('ramp_increasing_angle', 'Ramp Increasing Angle:')
        # Ramp start angle
        self._create_ga_row_edit('ramp_start_angle', 'Ramp Start Angle:')
        # Ramp increasing type
        self._create_ga_row_edit('ramp_increasing_type', 'Ramp Increasing Type:')
        # Ramp max angle
        self._create_ga_row_edit('ramp_max_angle', 'Ramp Max Angle:')
        # Ramp approach distance
        self._create_ga_row_edit('ramp_approach_distance', 'Ramp Approach Distance:')
        # Ramp distance to jump
        self._create_ga_row_edit('ramp_distance_needed_to_jump', 'Distance to Jump:')
        # Jagged increasing angle
        self._create_ga_row_edit('jagged_increasing_angle', 'Jagged Increasing Angle:')
        # Jagged decreasing angle
        self._create_ga_row_edit('jagged_decreasing_angle', 'Jagged Decreasing Angle:')
        

        ga_widget = QWidget()
        ga_widget.setLayout(self.ga_settings)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(ga_widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)
        
        button_widget = QWidget()
        hlayout = QHBoxLayout()
        hlayout.addWidget(QPushButton('Apply'))
        hlayout.addWidget(QPushButton('Reset'))
        button_widget.setLayout(hlayout)

        self.vbox = QVBoxLayout()
        self.vbox.addWidget(self.scroll_area)
        self.vbox.addWidget(button_widget)

        self.setLayout(self.vbox)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        draw_border(painter, self.size)


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
        # tile = create_floor_tile(self.world, b2Vec2(50,50), 0)
        # vertices = tile.fixtures[0].shape.vertices
        # qpoints = [QPointF(vert[0], vert[1]) for vert in vertices]

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
        self.title = 'Test'
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
        self.best_car_window = BestCarWindow(self.centralWidget, (300, 200))
        self.best_car_window.setGeometry(QRect(800, 500, 300, 200))
        self.best_car_window.setObjectName('best_car_window')

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

        self.settings_window = SettingsWindow(self.centralWidget, (300, 500))
        self.settings_window.setGeometry(QRect(800, 0, 300, 500))
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