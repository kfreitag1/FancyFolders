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
    def currentCounter(self):
        return self._currentcounter

    @currentCounter.setter
    def currentCounter(self, value: int):
        self._currentcounter = value
        self.update()

    def __init__(self, parent, colour: QColor = Qt.black, roundness=100.0,
                 minimumTrailOpacity=3.14, trailFadePercentage=80.0, revolutionsPerSecond=1.57,
                 numberOfLines=20, lineLength=10.0, lineWidth=2.0, innerRadius=10.0,
                 centerOnParent=True, disableParentWhenSpinning=False,
                 modality=Qt.WindowModality.NonModal):
        super().__init__(parent)

        self._centerOnParent = centerOnParent
        self._disableParentWhenSpinning = disableParentWhenSpinning

        # Set display properties
        self._color = colour
        self._roundness = roundness
        self._minimumTrailOpacity = minimumTrailOpacity
        self._trailFadePercentage = trailFadePercentage
        self._revolutionsPerSecond = revolutionsPerSecond
        self._numberOfLines = numberOfLines
        self._lineLength = lineLength
        self._lineWidth = lineWidth
        self._innerRadius = innerRadius
        self._isSpinning = False

        self.currentCounter = 0

        # Configure looping animation
        self._animation = QPropertyAnimation(self, b"currentCounter", self)
        self._animation.setDuration(math.floor(1000 / revolutionsPerSecond))
        self._animation.setLoopCount(-1)
        self._animation.setStartValue(0)
        self._animation.setEndValue(self._numberOfLines)
        self._animation.start()

        self.hide()

        self.setWindowModality(modality)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._setSize()

    #########################
    # PUBLIC METHODS
    #########################

    def start(self):
        if self._isSpinning:
            return

        self._isSpinning = True
        self._animation.start()
        self.show()

    def stop(self):
        if not self._isSpinning:
            return

        self._isSpinning = False
        self._animation.stop()
        self.hide()

    def isSpinning(self) -> bool:
        return self._isSpinning

    #########################
    # PRIVATE METHODS
    #########################

    def paintEvent(self, _: QPaintEvent):
        with QPainter(self) as painter:
            painter.fillRect(self.rect(), Qt.GlobalColor.transparent)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

            if self.currentCounter >= self._numberOfLines:
                self.currentCounter = 0

            painter.setPen(Qt.PenStyle.NoPen)
            for i in range(0, self._numberOfLines):
                painter.save()
                painter.translate(self._innerRadius + self._lineLength,
                                  self._innerRadius + self._lineLength)
                rotateAngle = float(360 * i) / float(self._numberOfLines)
                painter.rotate(rotateAngle)
                painter.translate(self._innerRadius, 0)
                distance = self._lineCountDistanceFromPrimary(
                    i, self.currentCounter, self._numberOfLines)
                color = self._currentLineColor(distance, self._numberOfLines, self._trailFadePercentage,
                                               self._minimumTrailOpacity, self._color)
                painter.setBrush(color)
                rect = QRect(0, int(-self._lineWidth / 2),
                             int(self._lineLength), int(self._lineWidth))
                painter.drawRoundedRect(
                    rect, self._roundness, self._roundness, Qt.SizeMode.RelativeSize)
                painter.restore()

    def _setSize(self):
        size = int((self._innerRadius + self._lineLength) * 2)
        self.setFixedSize(size, size)

    def _lineCountDistanceFromPrimary(self, current, primary, totalNrOfLines):
        distance = primary - current
        if distance < 0:
            distance += totalNrOfLines
        return distance

    def _currentLineColor(self, countDistance, totalNrOfLines, trailFadePerc, minOpacity, colorinput):
        color = QColor(colorinput)
        if countDistance == 0:
            return color
        minAlphaF = minOpacity / 100.0
        distanceThreshold = int(
            math.ceil((totalNrOfLines - 1) * trailFadePerc / 100.0))
        if countDistance > distanceThreshold:
            color.setAlphaF(minAlphaF)
        else:
            alphaDiff = color.alphaF() - minAlphaF
            gradient = alphaDiff / float(distanceThreshold + 1)
            resultAlpha = color.alphaF() - gradient * countDistance
            # If alpha is out of bounds, clip it.
            resultAlpha = min(1.0, max(0.0, resultAlpha))
            color.setAlphaF(resultAlpha)
        return color
