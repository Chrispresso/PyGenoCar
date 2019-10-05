from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from boxcar.floor import *
from boxcar.car import *
from boxcar.utils import *
import sys
import time
from typing import Tuple


class DensityWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size
        self.resize(size[0], size[1])
        print(self.width(), self.height())
        self._gradient_widget = QWidget()
        self._gradient_widget.resize(size[0]/2, size[1])
        self._create_linear_gradient()

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Add the stuff to the left
        vbox_layout = QVBoxLayout()
        vbox_layout.setContentsMargins(0, 0, 0, 0)
        for i in range(10):
            label = QLabel()
            label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            label.setText('Test {} -'.format(i))
            vbox_layout.addWidget(label)

        self.layout.addLayout(vbox_layout)

        self.layout.addWidget(self._gradient_widget, 1)

        # New vbox
        v = QVBoxLayout()
        v.setContentsMargins(0,0,0,0)

        for i in range(6):
            label = QLabel()
            label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            label.setText('- test {}'.format(i))
            v.addWidget(label)
        self.layout.addLayout(v)
        self.setLayout(self.layout)

    def _create_linear_gradient(self) -> None:
        self._gradient_widget.setAutoFillBackground(True)
        gradient = QLinearGradient()
        gradient.setStart(self._gradient_widget.width(), 0.0)
        gradient.setFinalStop(self._gradient_widget.width(), self._gradient_widget.height())

        # Create gradient stops
        stops = []
        i = 0.0
        for i in range(360):
            stop_location = i/360.0
            color = QColor.fromHsvF(i/360.0, 1.0, 0.8)
            stop = (stop_location, color)
            stops.append(stop)
        
        gradient.setStops(stops)
        
        # Add Gradient to the rectangle
        brush = QtGui.QBrush(gradient)
        palette = self._gradient_widget.palette()
        palette.setBrush(self._gradient_widget.backgroundRole(), brush)
        self._gradient_widget.setPalette(palette)