from typing import Callable
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLayout, QRadioButton, QSizePolicy, QWidget


class ContainerRadioButton(QWidget):
    """Represents a radio button which has a layout container as its body
    instead of just a label
    """

    def __init__(self, layout: QLayout, group: QButtonGroup, parent: QWidget,
                 update: Callable[[], None], is_default=False):
        super().__init__()

        self.radio = QRadioButton(parent)
        self.radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radio.setChecked(is_default)
        self.radio.clicked.connect(lambda _: update())
        group.addButton(self.radio)

        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(3)
        container.addWidget(self.radio)
        container.addLayout(layout)
        self.setLayout(container)

    def setEnabled(self, enabled: bool):
        """Passthrough method to set the enabled state of the radio button

        Args:
            enabled (bool): Should the radio button be enabled?
        """
        self.radio.setEnabled(enabled)

    def isChecked(self) -> bool:
        """Passthrough method to get the checked state of the radio button

        Returns:
            bool: Is the radio button checked?
        """
        return self.radio.isChecked()

    def setChecked(self, checked: bool):
        """Passthrough method to set the checked state of the radio button

        Args:
            checked (bool): Should the radio button be checked?
        """
        self.radio.setChecked(checked)

    def mousePressEvent(self, _: QMouseEvent):
        """Overriden mouse press event to pass through to radio button

        Args:
            _ (QMouseEvent): Unused mouse event
        """
        if self.radio.isEnabled():
            self.radio.setDown(True)

    def mouseReleaseEvent(self, _: QMouseEvent):
        """Overriden mouse release event to pass through to radio button

        Args:
            _ (QMouseEvent): Unused mouse event
        """
        if self.radio.isEnabled():
            self.radio.setChecked(True)
            self.radio.setDown(False)
