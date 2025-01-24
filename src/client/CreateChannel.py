from PyQt5 import QtWidgets


class CreateChannelDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Channel")

        # Layout
        layout = QtWidgets.QVBoxLayout()

        self.channel_name = QtWidgets.QLineEdit()
        layout.addWidget(QtWidgets.QLabel("Enter channel name:"))
        layout.addWidget(self.channel_name)

        # Create button box (OK and Cancel)
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
