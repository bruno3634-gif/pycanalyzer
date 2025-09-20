# simple_transmit.py
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton

class SimpleTransmitWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Transmit Test")
        self.resize(400, 300)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        layout.addWidget(QLabel("This is a test transmit window"))
        
        test_btn = QPushButton("Test Button")
        layout.addWidget(test_btn)
        
        print("Simple transmit window created")
