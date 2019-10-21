from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QScrollArea, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QFormLayout
from PyQt5.QtGui import QPainter, QBrush, QPen, QPolygonF, QLinearGradient, QColor
from PyQt5.QtCore import Qt, QPointF, QTimer, QRect
from boxcar.floor import *
from boxcar.car import *
from settings import settings, get_boxcar_constant, get_ga_constant
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

        self.boxcar_form = QFormLayout()

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
        gradient_vbox.addWidget(self._gradient_widget, 15)
        column_layout.addLayout(gradient_vbox, 3)

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

        # Add the boxcar settings
        self._add_boxcar_settings()

        # Set overall layout
        self.setLayout(self.layout)

    def resizeEvent(self, event):
        self._create_linear_gradient()
        return super().resizeEvent(event)

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


    def _add_boxcar_settings(self) -> None:
        label_boxcar_settings = QLabel()
        label_boxcar_settings.setFont(font_bold)
        label_boxcar_settings.setText('Boxcar Settings')
        label_boxcar_settings.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.layout.addWidget(label_boxcar_settings)

        # Make small note
        small_note = QLabel()
        small_note.setFont(QtGui.QFont('Times', 8, QtGui.QFont.Normal))
        small_note.setText('*indicates it is part of the Genetic Algorithm')
        small_note.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.layout.addWidget(small_note)

        self._add_bc_row_entry('floor_tile_height', 'Tile Height:', font_bold, normal_font)
        self._add_bc_row_entry('floor_tile_width', 'Tile Width:', font_bold, normal_font)
        self._add_bc_row_entry('max_floor_tiles', 'Num Floor Tiles:', font_bold, normal_font)
        self._add_bc_row_entry('floor_creation_type', 'Floor Type:', font_bold, normal_font)
        # Ramp specific stuff
        if get_boxcar_constant('floor_creation_type') == 'ramp':
            # Is the ramp constant?
            if get_boxcar_constant('ramp_constant_angle'):
                self._add_bc_row_entry('ramp_constant_angle', 'Ramp Constant Angle:', font_bold, normal_font)
                self._add_bc_row_entry('ramp_constant_distance', 'Ramp Distance:', font_bold, normal_font)
            # Otherwise it's increasing angle
            else:
                self._add_bc_row_entry('ramp_increasing_angle', 'Ramp Increasing Angle:', font_bold, normal_font)
                self._add_bc_row_entry('ramp_start_angle', 'Start Angle:', font_bold, normal_font)
                self._add_bc_row_entry('ramp_increasing_type', 'Increase By:', font_bold, normal_font)
                self._add_bc_row_entry('ramp_max_angle', 'Max Ramp Angle:', font_bold, normal_font)
                self._add_bc_row_entry('ramp_approach_distance', 'Approach Distance:', font_bold, normal_font)
            self._add_bc_row_entry('ramp_distance_needed_to_jump', 'Jump Distance:', font_bold, normal_font)
        # Gaussian specific stuff
        elif get_boxcar_constant('floor_creation_type') == 'gaussian':
            self._add_bc_row_entry('gaussian_floor_seed', 'Seed:', font_bold, normal_font)
            self._add_bc_row_entry('tile_angle_mu', 'Tile Angle (mu):', font_bold, normal_font)
            self._add_bc_row_entry('tile_angle_std', 'Tile Andle (std):', font_bold, normal_font)
            self._add_bc_row_entry('tile_gaussian_denominator', 'Angle Normalizer:', font_bold, normal_font)
            self._add_bc_row_entry('tile_gaussian_threshold', 'Max Numerator:', font_bold, normal_font)
        # Jagged specific stuff
        elif get_boxcar_constant('floor_creation_type') == 'jagged':
            angle_range = '-{:.2f}, {:.2f}'.format(
                get_boxcar_constant('jagged_increasing_angle'),
                get_boxcar_constant('jagged_decreasing_angle')
            )
            self._add_bc_row_entry(None, 'Jagged Angle:', font_bold, normal_font, force_value=angle_range)
        else:
            raise Exception('Unable to determine floor_creation_type "{}"'.format(get_boxcar_constant('floor_creation_type')))
        self._add_bc_row_entry('car_max_tries', 'Car Max Tries:', font_bold, normal_font)
        # Chassis Axis
        chassis_axis_range = '[{:.2f}, {:.2f})'.format(
            get_boxcar_constant('min_chassis_axis'),
            get_boxcar_constant('max_chassis_axis')
        )
        self._add_bc_row_entry(None, '*Chassis Axis:', font_bold, normal_font, force_value=chassis_axis_range)
        # Chassis Density
        chassis_density_range = '[{:.2f}, {:.2f})'.format(
            get_boxcar_constant('min_chassis_density'),
            get_boxcar_constant('max_chassis_density')
        )
        self._add_bc_row_entry(None, '*Chassis Density:', font_bold, normal_font, force_value=chassis_density_range)
        # Wheel Density
        wheel_density_range = '[{:.2f}, {:.2f})'.format(
            get_boxcar_constant('min_wheel_density'),
            get_boxcar_constant('max_wheel_density')
        )
        self._add_bc_row_entry(None, '*Wheel Density:', font_bold, normal_font, force_value=wheel_density_range)
        # Num Wheels
        num_wheels_range = '[{:.2f}, {:.2f}]'.format(
            get_boxcar_constant('min_num_wheels'),
            get_boxcar_constant('max_num_wheels')
        )
        self._add_bc_row_entry(None, '*Num. Wheels:', font_bold, normal_font, force_value=num_wheels_range)
        # Wheel Radius
        wheel_radius_range = '[{:.2f}, {:.2f})'.format(
            get_boxcar_constant('min_wheel_radius'),
            get_boxcar_constant('max_wheel_radius')
        )
        self._add_bc_row_entry(None, '*Wheel Radius:', font_bold, normal_font, force_value=wheel_radius_range)
        # Wheel motor wpeed
        # wheel_motor_speed_range = '[{:.2f}, {:.2f})'.format(
        #     get_boxcar_constant('min_wheel_motor_speed'),
        #     get_boxcar_constant('max_wheel_motor_speed')
        # )
        # self._add_bc_row_entry(None, '*Wheel Speed:', font_bold, normal_font, force_value=wheel_motor_speed_range)
        
        self._add_bc_row_entry('gravity', 'Gravity (x, y):', font_bold, normal_font)
        self._add_bc_row_entry('fps', 'FPS:', font_bold, normal_font)

        widget = QWidget()
        widget.setLayout(self.boxcar_form)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidget(widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setMaximumHeight(250)
        self.scroll_area.setWidgetResizable(False)

        vbox = QVBoxLayout()
        vbox.addWidget(self.scroll_area, 0)
        self.layout.addLayout(vbox, 0) # @TODO: Adjust this
    
    def _add_bc_row_entry(self, constant: str, label_text: str,
                       label_font, value_font,
                       alignment: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
                       force_value = None):
        _add_row_entry(self.boxcar_form, 'boxcar', constant, label_text, label_font, value_font, alignment, force_value)

class SettingsWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.resize(size[0], size[1])

        top_down = QVBoxLayout()
        self.density_window = DensityWindow(self, (size[0], int(size[1]*.8)))
        
        top_down.addWidget(self.density_window)
        self.setLayout(top_down)

    
class StatsWindow(QWidget):
    def __init__(self, parent, size):
        super().__init__(parent)
        self.size = size

        # Create a grid layout to keep track of certain stats

        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0, 0, 0, 0)
        self._init_window()
        self.setLayout(self.grid)


    def paintEvent(self, event):
        painter = QPainter(self)
        draw_border(painter, self.size)

    def _init_window(self) -> None:
        ROW = 0
        COL = 0
        stats_vbox = QVBoxLayout()
        stats_vbox.setContentsMargins(0,0,0,0)

        # Create the current generation
        generation_label = QLabel()
        generation_label.setFont(font_bold)
        generation_label.setText('Generation:')
        generation_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.generation = QLabel()
        self.generation.setFont(normal_font)
        self.generation.setText("<font color='red'>" + '1' + '</font>')
        self.generation.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_generation = QHBoxLayout()
        hbox_generation.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_generation.addWidget(generation_label, 1)
        hbox_generation.addWidget(self.generation, 1)
        stats_vbox.addLayout(hbox_generation)

        # Current number alive
        current_num_alive_label = QLabel()
        current_num_alive_label.setFont(font_bold)
        current_num_alive_label.setText('Current Alive:')
        current_num_alive_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.current_num_alive = QLabel()
        self.current_num_alive.setFont(normal_font)
        self.current_num_alive.setText(str(get_ga_constant('num_parents')))
        self.current_num_alive.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_num_alive = QHBoxLayout()
        hbox_num_alive.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_num_alive.addWidget(current_num_alive_label, 1)
        hbox_num_alive.addWidget(self.current_num_alive, 1)
        stats_vbox.addLayout(hbox_num_alive)

        # population size
        pop_size_label = QLabel()
        pop_size_label.setFont(font_bold)
        pop_size_label.setText('Population Size:')
        pop_size_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.pop_size = QLabel()
        self.pop_size.setFont(normal_font)
        self.pop_size.setText(str(get_ga_constant('num_parents')))
        self.pop_size.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_pop_size = QHBoxLayout()
        hbox_pop_size.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_pop_size.addWidget(pop_size_label, 1)
        hbox_pop_size.addWidget(self.pop_size, 1)
        stats_vbox.addLayout(hbox_pop_size)

        # Create best fitness
        best_fitness_label = QLabel()
        best_fitness_label.setFont(font_bold)
        best_fitness_label.setText('Best Fitness Ever:')
        generation_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.best_fitness = QLabel()
        self.best_fitness.setFont(normal_font)
        self.best_fitness.setText('0.0')
        self.best_fitness.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_fitness = QHBoxLayout()
        hbox_fitness.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_fitness.addWidget(best_fitness_label, 1)
        hbox_fitness.addWidget(self.best_fitness, 1)
        stats_vbox.addLayout(hbox_fitness)

        # Average fitness last gen
        average_fitness_label = QLabel()
        average_fitness_label.setFont(font_bold)
        average_fitness_label.setText('Mean Fitness Last Gen:')
        average_fitness_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.average_fitness_last_gen = QLabel()
        self.average_fitness_last_gen.setFont(normal_font)
        self.average_fitness_last_gen.setText('0.0')
        self.average_fitness_last_gen.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_avg_fitness = QHBoxLayout()
        hbox_avg_fitness.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_avg_fitness.addWidget(average_fitness_label, 1)
        hbox_avg_fitness.addWidget(self.average_fitness_last_gen, 1)
        stats_vbox.addLayout(hbox_avg_fitness)

        # num solved last gen
        num_solved_last_gen_label = QLabel()
        num_solved_last_gen_label.setFont(font_bold)
        num_solved_last_gen_label.setText('# Solved Last Gen:')
        num_solved_last_gen_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.num_solved_last_gen = QLabel()
        self.num_solved_last_gen.setFont(normal_font)
        self.num_solved_last_gen.setText('0')
        self.num_solved_last_gen.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_num_solved = QHBoxLayout()
        hbox_num_solved.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_num_solved.addWidget(num_solved_last_gen_label, 1)
        hbox_num_solved.addWidget(self.num_solved_last_gen, 1)
        stats_vbox.addLayout(hbox_num_solved)

        # generations without improvement
        gens_without_improvement_label = QLabel()
        gens_without_improvement_label.setFont(font_bold)
        gens_without_improvement_label.setText('Stale Generations:')
        gens_without_improvement_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.gens_without_improvement = QLabel()
        self.gens_without_improvement.setFont(normal_font)
        self.gens_without_improvement.setText('0')
        self.gens_without_improvement.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hbox_gens_without_improvement = QHBoxLayout()
        hbox_gens_without_improvement.setContentsMargins(5, 0, 0, 0)
        # Give equal weight
        hbox_gens_without_improvement.addWidget(gens_without_improvement_label, 1)
        hbox_gens_without_improvement.addWidget(self.gens_without_improvement, 1)
        stats_vbox.addLayout(hbox_gens_without_improvement)

        self.grid.addLayout(stats_vbox, 0, 0)
        # self.grid.addWidget(QLabel(),0,1)
        # self.grid.setColumnStretch(1,10)
        self._add_ga_settings_window()  # Finally add the GA Settings Window
    
    def _add_ga_settings_window(self) -> None:
        self.ga_settings_window = QVBoxLayout()
        # GA settings title
        label_ga_settings = QLabel()
        label_ga_settings.setFont(font_bold)
        label_ga_settings.setText('Genetic Algorithm Settings')
        label_ga_settings.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        self.ga_settings_window.addWidget(label_ga_settings)

        self._add_ga_entry('selection_type', 'Selection Type:', font_bold, normal_font)
        # Prob mutation
        mutation_prob = '{:.1f}% Gaussian\n{:.1f}% Uniform'.format(
            get_ga_constant('probability_gaussian') * 100.0,
            get_ga_constant('probability_random_uniform') * 100.0
        )
        self._add_ga_entry(None, 'Prob. Mutation:', font_bold, normal_font, force_value=mutation_prob)
        # Prob crossover
        crossover_prob = '{:.1f}% SBX'.format(
            get_ga_constant('probability_SBX') * 100.0
        )
        self._add_ga_entry(None, 'Prob. Crossover:', font_bold, normal_font, force_value=crossover_prob)
        # Crossover selection
        # Tournament crossover selection
        if get_ga_constant('crossover_selection').lower() == 'tournament':
            if not get_ga_constant('tournament_size'):
                raise Exception('You must provide a tournament size if you choose "tournament" for crossover_selection.\n'+\
                    '"tournament_size" can be anywhere from [1, len(population))')
            parent_crossover = 'tournament of {}'.format(get_ga_constant('tournament_size'))
        # roulette
        elif get_ga_constant('crossover_selection').lower() == 'roulette':
            parent_crossover = 'roulette'
        else:
            raise Exception('Unable to determine crossover_selection "{}"'.format(get_ga_constant('crossover_selection')))
        self._add_ga_entry(None, 'Crossover Selection:', font_bold, normal_font, force_value=parent_crossover)
        # Mutation rate
        mutation_rate = '{:.1f}%'.format(get_ga_constant('mutation_rate')*100)
        # static
        if get_ga_constant('mutation_rate_type').lower() == 'static':
            mutation_rate += ' Static'
        # decaying
        elif get_ga_constant('mutation_rate_type').lower() == 'decaying':
            mutation_rate += ' Decaying'
        else:
            raise Exception('Unable to determine mutation_rate_type "{}"'.format(get_ga_constant('mutation_rate_type')))
        self._add_ga_entry(None, 'Mutation Rate:', font_bold, normal_font, force_value=mutation_rate)
        # Lifespan
        lifespan = get_ga_constant('lifespan')
        lifespan = str(int(lifespan)) if lifespan != np.inf else 'infinite'
        self._add_ga_entry(None, 'Lifespan:', font_bold, normal_font, force_value=lifespan)

        self.grid.addLayout(self.ga_settings_window, 0, 3)

    def _add_ga_entry(self, constant: str, label_text: str,
                      label_font, value_font,
                      alignment: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
                      force_value = None):
        _add_top_down_entry(self.ga_settings_window, 'ga', constant, label_text, label_font, value_font, alignment, force_value)

    


def draw_border(painter: QPainter, size: Tuple[float, float]) -> None:
    painter.setPen(QPen(Qt.black, 1, Qt.SolidLine))
    painter.setBrush(QBrush(Qt.green, Qt.NoBrush))
    painter.setRenderHint(QPainter.Antialiasing)
    points = [(0, 0), (size[0], 0), (size[0], size[1]), (0, size[1])]
    qpoints = [QPointF(point[0], point[1]) for point in points]
    polygon = QPolygonF(qpoints)
    painter.drawPolygon(polygon)

def _add_row_entry(form: QFormLayout, controller: str, constant: str, label_text: str,
                   label_font, value_font,
                   alignment: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
                   force_value=None) -> None:
    # Create label
    label = QLabel()
    label.setFont(label_font)
    label.setText(label_text)
    label.setAlignment(alignment)
    # Create value
    value_label = QLabel()
    value_label.setFont(value_font)
    value = None
    if controller == 'boxcar' and constant:
        value = get_boxcar_constant(constant)
    elif controller == 'ga' and constant:
        value = get_ga_constant(constant)
    elif force_value:
        value = force_value

    value_label.setText(str(value))


    form.addRow(label, value_label)

def _add_top_down_entry(layout: QVBoxLayout, controller: str, constant: str, label_text: str,
                        label_font, value_font,
                        alignment: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
                        force_value=None) -> None:
    hbox = QHBoxLayout()
    hbox.setContentsMargins(0, 0, 0, 0)
    # Create label
    label = QLabel()
    label.setFont(label_font)
    label.setText(label_text)
    label.setAlignment(alignment)
    # Create value
    value_label = QLabel()
    value_label.setFont(value_font)
    value = None
    if controller == 'boxcar' and constant:
        value = get_boxcar_constant(constant)
    elif controller == 'ga' and constant:
        value = get_ga_constant(constant)
    elif force_value:
        value = force_value

    value_label.setText(str(value))

    # Add the labels to the hbox
    hbox.addWidget(label, 1)
    hbox.addWidget(value_label, 1)

    # Finally add hbox to the top-down layout
    layout.addLayout(hbox)