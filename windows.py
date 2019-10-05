from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from boxcar.floor import *
from boxcar.car import *
from boxcar.utils import *
from settings import settings
import sys
import time
from typing import Tuple

normal_font = QtGui.QFont('Times', 11, QtGui.QFont.Normal)
font_bold = QtGui.QFont('Times', 11, QtGui.QFont.Bold)

class DensityWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size
        self.resize(size[0], size[1])
        self._gradient_widget = QWidget()
        self._gradient_widget.resize(size[0]/2, size[1])
        self._create_linear_gradient()

        self.layout = QVBoxLayout()
        column_layout = QHBoxLayout()  # For the densities and gradient
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Add the headers for the two columns we will have
        headers = QHBoxLayout()
        headers.setContentsMargins(0,0,0,0)
        # Add header for chassis density
        label_chassis_densities = QLabel()
        label_chassis_densities.setText('Chassis Density')
        label_chassis_densities.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        headers.addWidget(label_chassis_densities)
        # Add spacer
        headers.addStretch(1)
        # Add header for wheel density
        label_wheel_density = QLabel()
        label_wheel_density.setText('Wheel Density')
        label_wheel_density.setAlignment(Qt.AlignHCenter | Qt.AlignBottom)
        headers.addWidget(label_wheel_density)

        # Add headers
        self.layout.addLayout(headers)
        
        
        # Add Chassis Density stuff
        chassis_density_vbox = QVBoxLayout()
        chassis_density_vbox.setContentsMargins(0, 0, 0, 0)
        min_chassis_density = get_boxcar_constant('min_chassis_density')
        max_chassis_density = get_boxcar_constant('max_chassis_density')
        chassis_range = max_chassis_density - min_chassis_density
        num_slices = 10  # Number of sections to add
        chassis_slices = [(chassis_range)/(num_slices-1)*i + min_chassis_density for i in range(num_slices)]

        for chassis_slice in chassis_slices:
            label = QLabel()
            text = '{:.2f} -'.format(chassis_slice)
            label.setAlignment(Qt.AlignRight | Qt.AlignTop)
            label.setText(text)
            chassis_density_vbox.addWidget(label)

        # Add the VBox to the layout
        column_layout.addLayout(chassis_density_vbox)

        # Add the actual gradient but add it to a VBox to be cheeky and set stretch at the bottom
        gradient_vbox = QVBoxLayout()
        gradient_vbox.addWidget(self._gradient_widget, 17)
        gradient_vbox.addStretch(1)
        column_layout.addLayout(gradient_vbox, 1)

        # Add Wheel Density stufff
        wheel_density_vbox = QVBoxLayout()
        wheel_density_vbox.setContentsMargins(0,0,0,0)
        min_wheel_density = get_boxcar_constant('min_wheel_density')
        max_wheel_density = get_boxcar_constant('max_wheel_density')
        wheel_range = max_wheel_density - min_wheel_density
        num_slices = 10  # Number of sections to add (I'm keeping it the same as the chassis density for now)
        wheel_slices = [(wheel_range)/(num_slices-1)*i + min_wheel_density for i in range(num_slices)]

        for i, wheel_slice in enumerate(wheel_slices):
            label = QLabel()
            text = '- {:.2f}'.format(wheel_slice)
            label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            label.setText(text)
            wheel_density_vbox.addWidget(label)

        # Add the VBox to the layout
        column_layout.addLayout(wheel_density_vbox)

        # Add column_layout to the layout
        self.layout.addLayout(column_layout, 5)
        self.layout.addStretch(1)

        # Set overall layout
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


class SettingsWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.resize(size[0], size[1])

        top_down = QVBoxLayout()
        self.density_window = DensityWindow(self, (size[0], int(size[1]*.8)))
        
        top_down.addWidget(self.density_window)
        self.setLayout(top_down)