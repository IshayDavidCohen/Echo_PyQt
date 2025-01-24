import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QWidget,QVBoxLayout, QGridLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self, send_message):
        super().__init__()
        # Window configuration
        self.setWindowTitle("Chat Server")
        self.setGeometry(200, 200, 750, 750)
        self.setFixedSize(750, 800)
        
        # Create vbox -> all messages appear
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.vbox = QVBoxLayout(self.central_widget)
        self.setLayout(self.vbox)

        # Create input 
        self.input_text = QLineEdit(self) # qtext edit
        self.send_button = QPushButton("Send", self)
                
        self.initUI() # run initialize screen objects
 
        
    def initUI(self):
        # input sizes and location
        self.input_text.setGeometry( 110 , 700, 400, 65)
        self.send_button.setGeometry( 520, 700, 120, 65)
        
        # input and vbox style
        self.input_text.setPlaceholderText("write here")
        self.input_text.setStyleSheet("font-size: 30px; font-family: Arial")
        self.send_button.setStyleSheet("font-size: 30px; font-family: Arial")
        self.vbox.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # set on click function to input button
        self.send_button.clicked.connect(self.send_click)
        
        
    def send_click(self):
        text = self.input_text.text()  # get text
        self.input_text.setText("")  # clear input
        
        self.add_message(text, "green")
        send_message(text)
        
        
    def add_message(self, text, color):
        # Create label message and add to vbox
        label = QLabel(text, self) 
        label.setStyleSheet(f"color: {color}; font-famliy: Arial; font-size: 25px;")
        self.vbox.addWidget(label)
    
    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
