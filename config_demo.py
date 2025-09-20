#!/usr/bin/env python3
"""
Configuration Demo - Shows how to control test messages in the CAN analyzer
"""

# Example 1: Disable test messages completely
print("=== Configuration Example 1: Disable Test Messages ===")
print("In main.py, set:")
print("ENABLE_TEST_MESSAGES = False")
print("This will:")
print("- Disable automatic test message generation")
print("- Stop the timer that updates messages every 500ms")
print("- Only show real CAN messages from SLCAN/PCAN adapters")
print()

# Example 2: Change test message update interval
print("=== Configuration Example 2: Change Update Interval ===")
print("In main.py, set:")
print("ENABLE_TEST_MESSAGES = True")
print("TEST_MESSAGE_INTERVAL = 1000  # Update every 1 second instead of 500ms")
print("This will:")
print("- Keep test messages enabled")
print("- Update test data every 1 second instead of every 500ms")
print("- Useful for slower development testing")
print()

# Example 3: Enable verbose logging
print("=== Configuration Example 3: Enable Verbose Logging ===")
print("In main.py, set:")
print("VERBOSE_LOGGING = True")
print("This will:")
print("- Show detailed console output")
print("- Log when test messages are generated")
print("- Help debug timing and message flow")
print()

# Example 4: Production configuration
print("=== Configuration Example 4: Production Mode ===")
print("In main.py, set:")
print("ENABLE_TEST_MESSAGES = False")
print("TEST_MESSAGE_INTERVAL = 500")
print("VERBOSE_LOGGING = False")
print("This will:")
print("- Disable all test message generation")
print("- Only process real CAN traffic")
print("- Clean console output for production use")
print()

print("=== Current Configuration Variables in main.py ===")
print("ENABLE_TEST_MESSAGES = True/False   # Enable/disable test message generation")
print("TEST_MESSAGE_INTERVAL = 500         # Interval in milliseconds (default: 500ms)")
print("VERBOSE_LOGGING = True/False        # Enable/disable detailed console output")
print()

print("=== Quick Configuration Changes ===")
print("1. Edit main.py")
print("2. Change the variables at the top of the file")
print("3. Save and restart the application")
print()

print("✓ Configuration system ready!")
