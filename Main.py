import sys
import numpy as np

from PyQt5.QtCore import pyqtSignal, QSize, Qt, QTimer
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QApplication, QGridLayout, QOpenGLWidget, QSlider,
                             QWidget, QPushButton, QLabel)

from OpenGL.GL import *


class Window(QWidget):

    def __init__(self):
        super(Window, self).__init__()

        self.running = True

        self.glWidget = GLWidget()

        self.play_button = QPushButton("Play")

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 60)
        self.speed_slider.setSingleStep(1)
        self.speed_slider.setValue(30)

        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(20, 80)
        self.zoom_slider.setValue(50)

        self.cell_count_label = QLabel("Active Cells: ")
        self.frequency_label = QLabel("Update Speed: %dhz" % self.zoom_slider.value())
        self.zoom_label = QLabel("Square Density: 20")

        self.play_button.pressed.connect(self.glWidget.toggle_state)
        self.speed_slider.valueChanged.connect(self.change_step_speed)
        self.zoom_slider.valueChanged.connect(self.change_density)

        self.glWidget.cell_count_changed.connect(self.update_cell_count)
        self.glWidget.game_state_changed.connect(self.game_state_changed)

        self.change_step_speed(30)

        main_layout = QGridLayout()
        control_layout = QGridLayout()

        main_layout.addWidget(self.glWidget, 0, 0)
        main_layout.addLayout(control_layout, 1, 0)
        control_layout.addWidget(self.play_button, 0, 0)
        control_layout.addWidget(self.speed_slider, 1, 0)
        control_layout.addWidget(self.frequency_label, 1, 1)
        control_layout.addWidget(self.cell_count_label, 0, 1)
        control_layout.addWidget(self.zoom_slider, 2, 0)
        control_layout.addWidget(self.zoom_label, 2, 1)

        self.setLayout(main_layout)

        self.setWindowTitle("Conway's Game of Life")

        self.cell_count = 0

    def update_cell_count(self, val):
        self.cell_count = val
        self.cell_count_label.setText("Cells: %d" % val)

    def game_state_changed(self, state):
        self.running = state
        states = ["Play", "Pause"]
        self.play_button.setText(states[self.running])

    def change_step_speed(self, value):
        self.frequency_label.setText("Update Speed: %dhz" % value)
        self.glWidget.set_step_frequency(value)

    def change_density(self, value):
        self.zoom_label.setText("Square Density: %d" % value)
        self.glWidget.set_grid_buffer(value)


class GLWidget(QOpenGLWidget):
    cell_count_changed = pyqtSignal(int)
    game_state_changed = pyqtSignal(bool)

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)

        self.squares = []
        self.width = 1000
        self.height = 1000
        self.running = False
        self.square_size = 80
        self.density = 50
        self.grid_vao = -1
        self.cell_vao = -1

        self.cell_vbo = -1
        self.grid_vbo = -1

        self.timer = QTimer()
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self.step)
        self.timer.start(500)

        self.timer2 = QTimer()
        self.timer2.setSingleShot(False)
        self.timer2.timeout.connect(self.update_loop)
        self.timer2.start(10)

        self.white = QColor.fromCmykF(0, 0, 0, 0.0)
        self.black = QColor.fromCmykF(1, 1, 1, 0.0)
        self.gray = QColor.fromCmykF(0.5, 0.5, 0.5, 0.0)

    def step(self):
        if self.running:
            self.update_cells()

    def update_loop(self):
        self.update_buffer_data()

    def minimumSizeHint(self):
        return QSize(50, 50)

    def sizeHint(self):
        return QSize(self.width, self.height)

    def initializeGL(self):
        glClearColor(1, 1, 1, 1)

        self.grid_vao = glGenVertexArrays(1)
        self.cell_vao = glGenVertexArrays(1)

        self.grid_vbo = glGenBuffers(1)
        self.cell_vbo = glGenBuffers(1)

        objects = [(self.grid_vao, self.grid_vbo), (self.cell_vao, self.cell_vbo)]

        for (vao, vbo) in objects:
            glBindVertexArray(vao)
            glBindBuffer(GL_ARRAY_BUFFER, vbo)
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(GLfloat), None)

        self.set_grid_buffer(self.density)

    def paintGL(self):
        glClear(
            GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.set_color(self.gray)
        glBindVertexArray(self.cell_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.cell_vbo)
        glDrawArrays(GL_TRIANGLES, 0, glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE))

        self.set_color(self.black)
        self.set_grid_buffer(self.density)
        glBindVertexArray(self.grid_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
        glDrawArrays(GL_LINES, 0, glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE))

    def resizeGL(self, width, height):
        self.width = width
        self.height = height

        glViewport(0, width, 0, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, 0, height, -1, 1)
        glMatrixMode(GL_MODELVIEW)

    def mouseMoveEvent(self, event):
        x, y = int(event.pos().x() // self.square_size), int((self.height - event.pos().y()) // self.square_size)
        if event.buttons() == Qt.LeftButton:
            if not (x, y) in self.squares:
                self.squares.append((x, y))
        elif event.buttons() == Qt.RightButton and (x, y) in self.squares:
            self.squares.remove((x, y))

    def set_grid_buffer(self, density):
        array = []
        self.density = density
        self.square_size = self.width / density
        for i in range(0, density):
            array += [0, i*self.square_size, self.width, i*self.square_size]
            array += [i*self.square_size, 0, i*self.square_size, self.height]
        glBindVertexArray(self.grid_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.grid_vbo)
        glBufferData(GL_ARRAY_BUFFER, np.array(array, dtype=np.float32), GL_DYNAMIC_DRAW)
        self.update()

    def get_population(self, pos):
        return len([1 for n in self.get_neighbors(pos) if n in self.squares])

    def toggle_state(self):
        if self.running:
            self.running = False
            self.game_state_changed.emit(False)
        else:
            self.running = True
            self.game_state_changed.emit(True)

    def update_cells(self):
        to_kill = set()
        to_raise = set()
        cells = 0
        visited = set()
        for cell in self.squares:
            if not 1 < self.get_population(cell) < 4:
                to_kill.add(cell)
            else:
                cells += 1
            for n_p in self.get_neighbors(cell):
                if (not (n_p in self.squares or n_p in visited)) and self.get_population(n_p) == 3\
                        and 0 <= n_p[0] <= 80 and 0 <= n_p[1] <= 80:
                    to_raise.add(n_p)
                    visited.add(n_p)
                    cells += 1

        for p in to_kill:
            self.squares.remove(p)

        for p in to_raise:
            self.squares.append(p)
        self.cell_count_changed.emit(cells)
        self.update_buffer_data()

    def update_buffer_data(self):
        array = []
        for cell in self.squares:
            row = cell[1]
            column = cell[0]
            if cell:
                x = column * self.square_size
                y = row * self.square_size
                array += [x, y, x+self.square_size, y] + [x+self.square_size, y+self.square_size]*2 +\
                         [x, y+self.square_size, x, y]
        if len(array) == 0:
            array = [0, 0]
        array = np.array(array, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, self.cell_vbo)
        glBufferData(GL_ARRAY_BUFFER, array, GL_DYNAMIC_DRAW)
        self.update()

    def set_step_frequency(self, value):
        self.timer.start(1000/value)

    @staticmethod
    def get_neighbors(pos):
        neighbors = []
        for angle in [np.pi / 4 * j for j in range(8)]:
            neighbors.append((round(pos[0] + np.cos(angle)), round(pos[1] + np.sin(angle))))
        return neighbors

    @staticmethod
    def get_buffer_data():
        size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, size, None)
        data = np.array(data)
        print(data.view(np.float32))
        print("Data contains %d bytes, or %d floats, or %d squares" % (size, size/4, size/(12*4)))

    @staticmethod
    def set_color(c):
        glColor4f(c.redF(), c.greenF(), c.blueF(), c.alphaF())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
