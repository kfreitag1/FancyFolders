from typing import Callable

from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QButtonGroup, QHBoxLayout, QLayout, QRadioButton, QSizePolicy, QWidget


class ContainerRadioButton(QWidget):
    """Represents a radio button which has a layout container as its body
    instead of just a label
    """

    def __init__(self, layout: QLayout, group: QButtonGroup, parent: QWidget,
                 on_change: Callable[[], None] = None, is_default=False) -> None:
        """Constructs a new radio button with custom container

        :param layout: Child container to show to the right of the radio button
        :param group: Buttongroup to put the radio button in
        :param parent: Parent widget
        :param on_change: Optional callback whenever a selection is made
        :param is_default: Whether the radio button is the default choice
        """
        super().__init__()

        self.radio = QRadioButton(parent)
        self.radio.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.radio.setChecked(is_default)
        self.radio.clicked.connect(lambda _: on_change())
        group.addButton(self.radio)

        container = QHBoxLayout()
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(3)
        container.addWidget(self.radio)
        container.addLayout(layout)
        self.setLayout(container)

    def setEnabled(self, enabled: bool) -> None:
        """Passthrough method to set the enabled state of the radio button

        :param enabled: Should the radio button be enabled?
        """
        self.radio.setEnabled(enabled)

    def isChecked(self) -> bool:
        """Passthrough method to get the checked state of the radio button

        :returns: Is the radio button checked?
        """
        return self.radio.isChecked()

    def setChecked(self, checked: bool) -> None:
        """Passthrough method to set the checked state of the radio button

        :param checked: Should the radio button be checked?
        """
        self.radio.setChecked(checked)

    def mousePressEvent(self, _: QMouseEvent) -> None:
        """Overriden mouse press event to pass through to radio button

        :param _: Unused mouse event
        """
        if self.radio.isEnabled():
            self.radio.setDown(True)

    def mouseReleaseEvent(self, _: QMouseEvent) -> None:
        """Overriden mouse release event to pass through to radio button

        :param _: Unused mouse event
        """
        if self.radio.isEnabled():
            self.radio.setChecked(True)
            self.radio.setDown(False)
