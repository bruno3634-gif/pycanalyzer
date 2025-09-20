#!/usr/bin/env python3
"""
Test script for transmit window
"""

import sys
from PyQt6.QtWidgets import QApplication
from transmit_window import TransmitWindow
from slcan_manager import SLCANManager
from dbc_manager import DBCManager

def test_transmit_window():
    app = QApplication(sys.argv)
    
    # Create managers
    slcan_manager = SLCANManager()
    dbc_manager = DBCManager()
    
    # Create transmit window
    window = TransmitWindow(slcan_manager, dbc_manager)
    window.show()
    
    print("Transmit window test - window should be visible")
    sys.exit(app.exec())

if __name__ == "__main__":
    test_transmit_window()
