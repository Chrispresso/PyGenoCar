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

        # Camera stuff
        self._camera = b2Vec2()
        self._camera_speed = 0.05
        self._camera.x = 100

        self.init_window()

        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(1000//60)

    def _update(self):
        self.world.Step(1./60, 10, 6)
        self.world.ClearForces()
        self.update()

    def init_window(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.top, self.left, self.width, self.height)
        self.show()

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
        # painter.translate(200 - (self._camera.x * scale) , 200 + (self._camera.y * scale))
        painter.translate(200,300)
        painter.scale(scale, -scale)
        arr = [Qt.black, Qt.green, Qt.blue]
        painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
        painter.setBrush(QBrush(Qt.black, Qt.SolidPattern))
        
        for i, tile in enumerate(self.floor.floor_tiles[:]):
            # print(tile.position)
            # print('-- ',end='')
            # print(tile.fixtures[0].shape.vertices)
            self.draw_polygon(painter, tile)

        self.draw_polygon(painter, self.chassis)
        # for fixture in self.chassis.fixtures:
        #     print([self.chassis.GetWorldPoint(vert) for vert in fixture.shape.vertices])



if __name__ == "__main__":
    world = b2World()
    App = QApplication(sys.argv)
    window = Window(world)
    sys.exit(App.exec_())