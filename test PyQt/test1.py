import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QWidget,QVBoxLayout, QGridLayout
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chat Server")
        self.setGeometry(200, 200, 750, 750)
        
        self.line_edit = QLineEdit(self)

        self.initUI()
        

        
        """
        label = QLabel("Hello", self)
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("color: blue; background-color: #6fdcf7")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        label.setGeometry((self.width() - label.width())// 2, (self.height() - label.height())// 2, label.width(), label.height())
        """
        
    def initUI(self):
        self.line_edit.setGeometry(10, 10, 200, 40)
        self.line_edit.setStyleSheet("font-size: 25px;"
                                     "font-family: Arial")
        self.line_edit.setPlaceholderText("write here")
        self.submit_button = QPushButton("submit", self)

        self.submit_button.setGeometry(210, 10, 100, 40)
        self.submit_button.setStyleSheet("font-size: 25px; font-family: Arial")
        
        self.submit_button.clicked.connect(self.submit)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        label1 = QLabel("1", self)
        label2 = QLabel("1", self)
        label3 = QLabel("1", self)
    
        vbox = QVBoxLayout()
        vbox.addWidget(label1)
        vbox.addWidget(label2)
        vbox.addWidget(label3)
    
        self.button = QPushButton("click", self)
        self.button.setGeometry(150, 200, 200, 100)
        self.button.setStyleSheet("font-size: 30px;")
        self.button.clicked.connect(self.onClick)
        
    def submit(self):
        text = self.line_edit.text()
        print(text)
        
        
    def onClick(self):
        print("click")
        self.button.setText("clicked")



    
def main():
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
        
   
if __name__ == "__main__":
    main()
    print(111)
