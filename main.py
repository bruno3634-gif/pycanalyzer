# mai# Configuration variables for development
ENABLE_TEST_MESSAGES = True   # Set to False to disable test message generation
TEST_MESSAGE_INTERVAL = 500   # Interval in milliseconds for test message updates (default: 500ms)
VERBOSE_LOGGING = True        # Set to True to enable detailed logging output
import sys
from gui import MainWindow
from PyQt6.QtWidgets import QApplication

# Configuration variables for development
ENABLE_TEST_MESSAGES = True  # Set to False to disable test message generation
TEST_MESSAGE_INTERVAL = 500   # Interval in milliseconds for test message updates (default: 500ms)
VERBOSE_LOGGING = False        # Set to True to enable detailed logging output

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    
    # Pass configuration to the main window
    window.enable_test_messages = ENABLE_TEST_MESSAGES
    window.test_message_interval = TEST_MESSAGE_INTERVAL
    window.verbose_logging = VERBOSE_LOGGING
    
    # Initialize test messages based on configuration
    window.initialize_test_messages()
    
    # Print configuration status
    if ENABLE_TEST_MESSAGES:
        print(f"✓ Test messages enabled (interval: {TEST_MESSAGE_INTERVAL}ms)")
    else:
        print("✗ Test messages disabled")
    
    if VERBOSE_LOGGING:
        print("✓ Verbose logging enabled")
    
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
