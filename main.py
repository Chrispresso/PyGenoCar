from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF
from PyQt5.QtCore import Qt, QPointF, QTimer
from boxcar.floor import *
from boxcar.car import *
import sys
import time

## Constants ##
scale = 70
FPS = 60

class Window(QMainWindow):
    def __init__(self, world):
        super().__init__()
        self.world = world
        self.title = 'Test'
        self.top = 150
        self.left = 150
        self.width = 500
        self.height = 500
        self.floor = Floor(self.world)
        self.chassis = create_random_chassis(self.world)
        self.car = create_random_car(self.world)

        # Camera stuff
        self._camera = b2Vec2()
        self._camera_speed = 0.05
        self._camera.x

        self.init_window()

        # Create a timer to run given the desired FPS
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(1000//FPS)

    def _draw_car(self, painter: QPainter, car: Car):
        """
        Draws a car to the window
        """
        for wheel in car.wheels:
            self.draw_circle(painter, wheel.body)

        self.draw_polygon(painter, car.chassis)

    def _update(self):
        """
        Main update method used. Called once every (1/FPS) second.
        """
        self.world.Step(1./FPS, 10, 6)
        diff_x = self._camera.x - self.car.chassis.position.x
        diff_y = self._camera.y - self.car.chassis.position.y
        self._camera.x -= self._camera_speed * diff_x #diff_x # self._camera_speed * diff_x
        self._camera.y -= self._camera_speed * diff_y #diff_y # self._camera_speed * diff_y
        self.world.ClearForces()
        self.update()

    def _set_painter_solid(self, painter: QPainter, color: Qt.GlobalColor, with_antialiasing: bool = True):
        painter.setPen(QPen(color, 1./scale, Qt.SolidLine))
        painter.setBrush(QBrush(color, Qt.SolidPattern))
        if with_antialiasing:
            painter.setRenderHint(QPainter.Antialiasing)

    def init_window(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)
        self.show()

    def _draw_floor(self, painter: QPainter):
        for tile in self.floor.floor_tiles:
            self.draw_polygon(painter, tile)

    def draw_circle(self, painter: QPainter, body: b2Body) -> None:
        for fixture in body.fixtures:
            if isinstance(fixture.shape, b2CircleShape):
                self._set_painter_solid(painter, Qt.black)
                radius = fixture.shape.radius
                center = body.GetWorldPoint(fixture.shape.pos)

                # Fill circle
                painter.drawEllipse(QPointF(center.x, center.y), radius, radius)

                # Draw line (helps for visualization of how fast and direction wheel is moving)
                self._set_painter_solid(painter, Qt.green)
                p0 = QPointF(center.x, center.y)
                p1 = QPointF(center.x + radius*math.cos(body.angle), center.y + radius*math.sin(body.angle))
                painter.drawLine(p0, p1)


    def draw_polygon(self, painter: QPainter, body: b2Body) -> None:
        painter.setPen(QPen(Qt.black, 1./scale, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        painter.setRenderHint(QPainter.Antialiasing)

        for fixture in body.fixtures:
            if isinstance(fixture.shape, b2PolygonShape):
                polygon: b2PolygonShape = fixture.shape
                local_points: List[b2Vec2] = polygon.vertices
                world_coords = [body.GetWorldPoint(point) for point in local_points]
                for i in range(len(world_coords)):
                    p0 = world_coords[i]
                    if i == len(world_coords)-1:
                        p1 = world_coords[0]
                    else:
                        p1 = world_coords[i+1]

                    qp0 = QPointF(*p0)
                    qp1 = QPointF(*p1)
                    painter.drawLine(qp0, qp1)

    def paintEvent(self, event):
        # tile = create_floor_tile(self.world, b2Vec2(50,50), 0)
        # vertices = tile.fixtures[0].shape.vertices
        # qpoints = [QPointF(vert[0], vert[1]) for vert in vertices]

        painter = QPainter(self)
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
        self._draw_car(painter, self.car)
        # for fixture in self.chassis.fixtures:
        #     print([self.chassis.GetWorldPoint(vert) for vert in fixture.shape.vertices])



if __name__ == "__main__":
    world = b2World()
    App = QApplication(sys.argv)
    window = Window(world)
    sys.exit(App.exec_())