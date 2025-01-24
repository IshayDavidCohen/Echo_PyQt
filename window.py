import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

# Path to the .ui file
ui_file = "chat.ui"

class MainWindow(QMainWindow):
    def __init__(self, client):
        super(MainWindow, self).__init__()
        loadUi(ui_file, self)  # Load the .ui file
        
        self.client = client  # Store reference to Client
        self.chat_name = None

        self.initialize_widgets()
        self.set_widget_style()
        
        
    def initialize_widgets(self):
        self.chat_display.setReadOnly(True)  # Ensure chat display is read-only
        self.chat_display.clear() # Clear any pre-existing text in the chat display
        
        self.send_message_button.setText("Send") # set text in button to 'send'
        self.send_message_button.clicked.connect(self.send_message)  # Connect button to function
        current_geometry = self.send_message_button.geometry()  # Get current geometry
        self.send_message_button.setGeometry(550, 342, 80, 40)  # (x, y, width, height)        
        
        self.username_label.setText(self.chat_name)  # Set the username label text
        
        current_geometry = self.message_input.geometry()  # Get current geometry
        self.message_input.setGeometry(current_geometry.x(), current_geometry.y(), current_geometry.width() - 30, 50) # change hight to 75px
        self.message_input.setPlaceholderText("Type your message here...")  # Add placeholder text


    def set_widget_style(self):
        # Style for the send_message_button
        self.send_message_button.setStyleSheet("""
            QPushButton {
                background-color: #2fba42; 
                color: black; 
                font-size: 18px; 
                border-radius: 12px; 
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #249634; 
                color: white; 
            }
        """)

        # Style for the chat_display (read-only QTextEdit)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; 
                border: 1px solid black; 
                font-size: 18px; 
                padding: 10px; 
                font-family: Arial;
            }
        """)

        # Style for the message_input
        self.message_input.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; 
                border: 1px solid #ccc; 
                font-size: 18px; 
                border-radius: 8px; 
                padding: 5px; 
                font-family: Arial;
            }
        """)

        # Style for the username_label
        self.username_label.setStyleSheet("""
            QLabel {
                font-size: 20px; 
                font-weight: bold; 
                color: red; 
            }
        """)


    def display_message(self, message, name=None):
        current_chat = self.chat_display.toHtml()  # Preserve existing chat
        
        new_message = f"<p>{name}: {message}</p>"
        if not name: new_message = f"<p><b>You:</b> {message}</p>"
        
        self.chat_display.setHtml(current_chat + new_message)
        self.message_input.clear()  # Clear the message input field


    def send_message(self):
        # Get the text from the message input field
        message = self.message_input.toPlainText().strip()
        
        if message:  # If there is a message, update the chat display
            self.display_message(message)
            self.client.send_message_to_server(message)
    
    
    def set_chat_name(self, name):
        self.chat_name = name


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("chat server")
    window.show()
    sys.exit(app.exec_())
