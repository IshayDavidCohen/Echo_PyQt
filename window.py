import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.uic import loadUi

# Path to the .ui file
ui_file = "chat.ui"

class MainWindow(QMainWindow):
    def __init__(self, client):
        super(MainWindow, self).__init__()
        
        loadUi(ui_file, self)  # Load the .ui file
        self.setWindowTitle("Chat Server")

        self.client = client  # Store reference to Client

        self.initialize_widgets()  # Setting for componnets
        self.set_widget_style()  # Setting componnets style
        
        
    def initialize_widgets(self):
        self.chat_display.setReadOnly(True)  # Ensure chat display is read-only
        self.chat_display.clear() # Clear any pre-existing text in the chat display
        
        self.send_message_button.setText("Send") # set text in button to 'send'
        self.send_message_button.clicked.connect(self.send_message)  # Connect button to function send_meesage
        self.send_message_button.setGeometry(550, 342, 80, 40)  # (x, y, width, height)        
                
        current_geometry = self.message_input.geometry()  # Get current size and index of componnets
        self.message_input.setGeometry(current_geometry.x(), current_geometry.y(), current_geometry.width() - 30, 50) # change hight and width
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


    def display_message(self, type_, message, name=None):
        current_chat = self.chat_display.toHtml()  # Get existing chat as Html
        new_message = None
        
        if type_ == "me":
            new_message = f"<p><b>You:</b> {message}</p>"
            
        elif type_ == "new user":
           new_message = f"<p style='color: green;'>{message}</p>"
           
        elif type_ == "user leave":
            new_message = f"<p style='color: red;'>{message}</p>"
             
        else:
            new_message = f"<p>{name}: {message}</p>"
        
        self.chat_display.setHtml(current_chat + new_message)
        
        self.chat_display.moveCursor(self.chat_display.textCursor().End) # Automatically scroll to the bottom of the window
        self.message_input.clear()  # Clear the message input field


    def send_message(self):
        # Get the text from the message input field
        message = self.message_input.toPlainText().strip()
        
        if message:  # If there is a message 
            self.display_message("me", message)  # Update the chat display
            self.client.send_message_to_server(message)  # Send message to server using client object
    
    
    def set_window_name(self, chat_name):
        # set window name to new name, client is calling that function
        self.setWindowTitle(f"Chat: {chat_name}")  # Update the window title


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow("chat server")
    window.show()
    sys.exit(app.exec_())
