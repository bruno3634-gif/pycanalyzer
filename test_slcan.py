#!/usr/bin/env python3
"""
SLCAN Connection Test Script
This script helps debug SLCAN device connections
"""

import serial
import serial.tools.list_ports
import time

def list_ports():
    """List all available serial ports"""
    print("Available serial ports:")
    ports = serial.tools.list_ports.comports()
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")
    return [port.device for port in ports]

def test_port(port, baudrate):
    """Test a specific port with SLCAN commands"""
    print(f"\nTesting {port} at {baudrate} baud...")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=2)
        time.sleep(2)  # Wait for device initialization
        
        # Clear buffers
        ser.flushInput()
        ser.flushOutput()
        
        # Test commands in order
        commands = [
            ("V", "Get version"),
            ("C", "Close channel"),
            ("L", "Enable loopback"),
            ("S6", "Set 500kbps"),
            ("O", "Open channel")
        ]
        
        for cmd, desc in commands:
            print(f"  Sending '{cmd}' ({desc})...")
            ser.write((cmd + '\r').encode())
            ser.flush()
            time.sleep(0.2)
            
            response = ""
            start_time = time.time()
            while time.time() - start_time < 1.0:
                if ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting).decode('ascii', errors='ignore')
                    break
                time.sleep(0.01)
            
            print(f"    Response: {repr(response)}")
            
            if cmd == "O" and response and ('\r' in response or 'OK' in response):
                print("  ✓ SLCAN device detected!")
                ser.close()
                return True
        
        ser.close()
        print("  ✗ No valid SLCAN responses")
        return False
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False

def main():
    print("SLCAN Device Scanner")
    print("===================")
    
    ports = list_ports()
    if not ports:
        print("No serial ports found!")
        return
    
    # Test common baud rates
    baud_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
    
    found_devices = []
    
    for port in ports:
        print(f"\n--- Testing {port} ---")
        for baud in baud_rates:
            if test_port(port, baud):
                found_devices.append((port, baud))
                break  # Found working combination, move to next port
    
    print("\n" + "="*50)
    if found_devices:
        print("SLCAN devices found:")
        for port, baud in found_devices:
            print(f"  {port} at {baud} baud")
    else:
        print("No SLCAN devices found.")
        print("\nTroubleshooting tips:")
        print("1. Make sure your device is plugged in")
        print("2. Check if drivers are installed")
        print("3. Try a different USB cable")
        print("4. Some devices need specific firmware (SLCAN protocol)")

if __name__ == "__main__":
    main()
