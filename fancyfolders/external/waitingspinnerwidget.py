"""
The MIT License (MIT)

Copyright (c) 2012-2014 Alexander Turkin
Copyright (c) 2014 William Hallatt
Copyright (c) 2015 Jacob Dawid
Copyright (c) 2016 Luca Weiss
Copyright (c) 2023 Kieran Freitag

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import math

from PySide6.QtCore import Property, QPropertyAnimation, Qt, QRect
from PySide6.QtGui import QColor, QPaintEvent, QPainter
from PySide6.QtWidgets import QWidget


class QWaitingSpinner(QWidget):
    """Represents a spinner that is shown when something is loading. Hidden by default
    """

    @Property(int)
    def counter(self):
        return self._counter

    @counter.setter
    def counter(self, value: int):
        self._counter = value
        self.update()

    def __init__(self, parent, colour: QColor = Qt.black, roundness=100.0,
                 minimum_trail_opacity=3.14, trail_fade_percentage=80.0, revolutions_per_second=1.57,
                 num_lines=20, line_length=10.0, line_width=2.0, inner_radius=10.0,
                 center_on_parent=True, disable_parent_when_spinning=False,
                 modality=Qt.WindowModality.NonModal):
        super().__init__(parent)

        self._centerOnParent = center_on_parent
        self._disableParentWhenSpinning = disable_parent_when_spinning

        # Set display properties
        self._color = colour
        self._roundness = roundness
        self._minimum_trail_opacity = minimum_trail_opacity
        self._trail_fade_percentage = trail_fade_percentage
        self._revolutions_per_second = revolutions_per_second
        self._num_lines = num_lines
        self._line_length = line_length
        self._line_width = line_width
        self._inner_radius = inner_radius
        self._is_spinning = False

        self.counter = 0

        # Configure looping animation
        self._animation = QPropertyAnimation(self, b"counter", self)
        self._animation.setDuration(math.floor(1000 / revolutions_per_second))
        self._animation.setLoopCount(-1)
        self._animation.setStartValue(0)
        self._animation.setEndValue(self._num_lines)
        self._animation.start()

        self.hide()

        self.setWindowModality(modality)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._set_size()

    #########################
    # PUBLIC METHODS
    #########################

    def start(self):
        if self._is_spinning:
            return

        self._is_spinning = True
        self._animation.start()
        self.show()

    def stop(self):
        if not self._is_spinning:
            return

        self._is_spinning = False
        self._animation.stop()
        self.hide()

    def is_spinning(self) -> bool:
        return self._is_spinning

    #########################
    # PRIVATE METHODS
    #########################

    def paintEvent(self, _: QPaintEvent):
        with QPainter(self) as painter:
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            if self.counter >= self._num_lines:
                self.counter = 0

            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(0, self._num_lines):
                painter.save()
                painter.translate(self._inner_radius + self._line_length,
                                  self._inner_radius + self._line_length)
                rotate_angle = float(360 * i) / float(self._num_lines)
                painter.rotate(rotate_angle)
                painter.translate(self._inner_radius, 0)
                distance = self._line_count_distance_from_primary(i, self.counter)
                color = self._current_line_color(distance)
                painter.setBrush(color)
                rect = QRect(0, int(-self._line_width / 2),
                             int(self._line_length), int(self._line_width))
                painter.drawRoundedRect(
                    rect, self._roundness, self._roundness, Qt.SizeMode.RelativeSize)
                painter.restore()

    def _set_size(self):
        size = int((self._inner_radius + self._line_length) * 2)
        self.setFixedSize(size, size)

    def _line_count_distance_from_primary(self, current, primary):
        distance = primary - current
        if distance < 0:
            distance += self._num_lines
        return distance

    def _current_line_color(self, count_distance) -> QColor:
        color = QColor(self._color)
        if count_distance == 0:
            return color
        min_alpha_f = self._minimum_trail_opacity / 100.0
        distance_threshold = int(
            math.ceil((self._num_lines - 1) * self._trail_fade_percentage / 100.0))
        if count_distance > distance_threshold:
            color.setAlphaF(min_alpha_f)
        else:
            alpha_diff = color.alphaF() - min_alpha_f
            gradient = alpha_diff / float(distance_threshold + 1)
            result_alpha = color.alphaF() - gradient * count_distance
            # If alpha is out of bounds, clip it.
            result_alpha = min(1.0, max(0.0, result_alpha))
            color.setAlphaF(result_alpha)
        return color
