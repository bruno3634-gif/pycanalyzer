# slcan_manager.py
import serial
import serial.tools.list_ports
import time
import threading
from datetime import datetime
import struct

class SLCANManager:
    def __init__(self):
        self.serial_port = None
        self.is_connected = False
        self.is_listening = False
        self.listen_thread = None
        self.message_callback = None
        self.stop_listening = False
        
    def list_serial_ports(self):
        """List all available serial ports"""
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    
    def test_connection(self, port, baudrate=115200):
        """Test if a device responds to SLCAN commands"""
        try:
            test_port = serial.Serial(port, baudrate, timeout=2)
            time.sleep(1)
            
            # Clear buffers
            test_port.flushInput()
            test_port.flushOutput()
            
            # Try a simple command
            test_port.write(b'V\r')
            test_port.flush()
            time.sleep(0.2)
            
            response = ""
            start_time = time.time()
            while time.time() - start_time < 1.0:
                if test_port.in_waiting > 0:
                    response += test_port.read(test_port.in_waiting).decode('ascii', errors='ignore')
                    break
                time.sleep(0.01)
            
            test_port.close()
            return len(response) > 0
            
        except Exception as e:
            print(f"Test connection failed: {e}")
            return False
    
    def connect(self, port, baudrate=115200, loopback=False):
        """Connect to SLCAN device"""
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=2)
            time.sleep(2)  # Wait for device to initialize
            
            # Clear any existing data
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            
            # Close any existing connection (ignore response)
            self.send_command("C")
            time.sleep(0.2)
            
            # Clear buffers again
            self.serial_port.flushInput()
            self.serial_port.flushOutput()
            
            # Set loopback mode if requested
            if loopback:
                loopback_response = self.send_command("L")
                print(f"Loopback enable response: {repr(loopback_response)}")
                if loopback_response and loopback_response.strip() == '\x07':
                    print("Warning: Device may not support loopback mode (returned \\x07)")
                time.sleep(0.2)
            
            # Set bitrate (default to 500kbps - S6)
            response = self.send_command("S6")
            print(f"Bitrate command response: {repr(response)}")
            time.sleep(0.2)
            
            # Open CAN channel
            response = self.send_command("O")
            print(f"Open command response: {repr(response)}")
            
            # Check for success - many devices return different responses
            if response and (response.strip() in ['\r', '', 'OK'] or '\r' in response):
                self.is_connected = True
                print("SLCAN connection successful")
                return True
            else:
                print(f"SLCAN connection failed - unexpected response: {repr(response)}")
                self.disconnect()
                return False
                
        except Exception as e:
            print(f"Error connecting to SLCAN device: {e}")
            if self.serial_port:
                try:
                    self.serial_port.close()
                except:
                    pass
                self.serial_port = None
            return False
    
    def disconnect(self):
        """Disconnect from SLCAN device"""
        if self.serial_port:
            try:
                self.stop_listening_messages()
                self.send_command("C")  # Close CAN channel
                self.serial_port.close()
            except:
                pass
            finally:
                self.serial_port = None
                self.is_connected = False
    
    def send_command(self, command):
        """Send command to SLCAN device"""
        if not self.serial_port:
            return None
        try:
            # Clear input buffer first
            self.serial_port.flushInput()
            
            # Send command
            self.serial_port.write((command + '\r').encode())
            self.serial_port.flush()
            
            # Wait a bit for response
            time.sleep(0.1)
            
            # Read response with timeout
            response = ""
            start_time = time.time()
            while time.time() - start_time < 1.0:  # 1 second timeout
                if self.serial_port.in_waiting > 0:
                    char = self.serial_port.read(1).decode('ascii', errors='ignore')
                    response += char
                    if char == '\r' or char == '\n':
                        break
                else:
                    time.sleep(0.01)
            
            print(f"Command '{command}' -> Response: {repr(response)}")
            return response
            
        except Exception as e:
            print(f"Error sending command '{command}': {e}")
            return None
    
    def set_bitrate(self, bitrate, loopback=False):
        """Set CAN bitrate"""
        bitrate_map = {
            10000: "S0",    # 10kbps
            20000: "S1",    # 20kbps
            50000: "S2",    # 50kbps
            100000: "S3",   # 100kbps
            125000: "S4",   # 125kbps
            250000: "S5",   # 250kbps
            500000: "S6",   # 500kbps
            800000: "S7",   # 800kbps
            1000000: "S8"   # 1Mbps
        }
        
        if bitrate in bitrate_map:
            # Close channel first
            close_response = self.send_command("C")
            print(f"Close response: {repr(close_response)}")
            time.sleep(0.2)
            
            # Set loopback mode if requested
            if loopback:
                loopback_response = self.send_command("L")
                print(f"Loopback enable response: {repr(loopback_response)}")
                time.sleep(0.2)
            
            # Set new bitrate
            bitrate_response = self.send_command(bitrate_map[bitrate])
            print(f"Bitrate response: {repr(bitrate_response)}")
            time.sleep(0.2)
            
            # Reopen channel
            open_response = self.send_command("O")
            print(f"Reopen response: {repr(open_response)}")
            
            # Check if successful
            success = open_response and (open_response.strip() in ['\r', '', 'OK'] or '\r' in open_response)
            print(f"Bitrate set to {bitrate}: {'Success' if success else 'Failed'}")
            return success
        else:
            print(f"Unsupported bitrate: {bitrate}")
            return False
    
    def check_device_info(self):
        """Get device version and capabilities"""
        if not self.is_connected:
            return None
        
        # Try version command
        version_response = self.send_command("V")
        print(f"Version response: {repr(version_response)}")
        
        # Try getting serial number
        serial_response = self.send_command("N")
        print(f"Serial response: {repr(serial_response)}")
        
        return {
            "version": version_response,
            "serial": serial_response
        }
    
    def send_message(self, msg_id, data, extended=False):
        """Send CAN message"""
        if not self.is_connected:
            return False
        
        try:
            # Ensure data length is valid
            if len(data) > 8:
                print(f"Error: Data length {len(data)} exceeds maximum of 8 bytes")
                return False
            
            # Format message - try standard SLCAN format first
            if extended:
                cmd = f"T{msg_id:08X}{len(data)}"
            else:
                cmd = f"t{msg_id:03X}{len(data)}"
            
            for byte in data:
                cmd += f"{byte:02X}"
            
            response = self.send_command(cmd)
            print(f"Send message command: {cmd}")
            print(f"Send message response: {repr(response)} (expected 'z')")
            
            # Check for success - should be 'z' but some devices might respond differently
            if response:
                response_clean = response.strip()
                if response_clean == 'z':
                    print("Message sent successfully!")
                    return True
                elif response_clean == '\x07':
                    print("Device returned error (\\x07) - trying alternative format...")
                    # Try alternative format (some cheap devices need different formatting)
                    return self._try_alternative_send_formats(msg_id, data, extended)
                elif response_clean == '\r' or response_clean == '':
                    print("Device returned \\r - some devices accept this as success")
                    return True
                else:
                    print(f"Unexpected response: {repr(response_clean)}")
                    return False
            else:
                print("No response from device")
                return False
            
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
    
    def _try_alternative_send_formats(self, msg_id, data, extended=False):
        """Try alternative message formats for devices that don't support standard SLCAN"""
        print("Trying alternative message formats...")
        
        # Format 1: Try without DLC
        try:
            if extended:
                cmd = f"T{msg_id:08X}"
            else:
                cmd = f"t{msg_id:03X}"
            
            for byte in data:
                cmd += f"{byte:02X}"
            
            response = self.send_command(cmd)
            print(f"Alternative format 1: {cmd} -> {repr(response)}")
            if response and response.strip() in ['z', '\r', '']:
                return True
        except Exception as e:
            print(f"Alternative format 1 failed: {e}")
        
        # Format 2: Try with spaces
        try:
            if extended:
                cmd = f"T {msg_id:08X} {len(data)}"
            else:
                cmd = f"t {msg_id:03X} {len(data)}"
            
            for byte in data:
                cmd += f" {byte:02X}"
            
            response = self.send_command(cmd)
            print(f"Alternative format 2: {cmd} -> {repr(response)}")
            if response and response.strip() in ['z', '\r', '']:
                return True
        except Exception as e:
            print(f"Alternative format 2 failed: {e}")
        
        print("All alternative formats failed")
        return False
    
    def start_listening(self, callback):
        """Start listening for CAN messages"""
        if not self.is_connected or self.is_listening:
            return False
        
        self.message_callback = callback
        self.is_listening = True
        self.stop_listening = False
        self.listen_thread = threading.Thread(target=self._listen_loop)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        return True
    
    def stop_listening_messages(self):
        """Stop listening for CAN messages"""
        self.stop_listening = True
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=1)
    
    def _listen_loop(self):
        """Main listening loop"""
        while not self.stop_listening and self.is_connected:
            try:
                if self.serial_port and self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode().strip()
                    if line:
                        message = self._parse_message(line)
                        if message and self.message_callback:
                            self.message_callback(message)
                else:
                    time.sleep(0.001)  # Small delay to prevent CPU spinning
                    
            except Exception as e:
                print(f"Error in listen loop: {e}")
                break
    
    def _parse_message(self, line):
        """Parse SLCAN message format"""
        try:
            if not line:
                return None
            
            # Standard frame: tiiil[data...]
            # Extended frame: Tiiiiiiiil[data...]
            if line.startswith('t') and len(line) >= 5:
                # Standard frame
                msg_id = int(line[1:4], 16)
                dlc = int(line[4])
                data_start = 5
                extended = False
            elif line.startswith('T') and len(line) >= 10:
                # Extended frame
                msg_id = int(line[1:9], 16)
                dlc = int(line[9])
                data_start = 10
                extended = True
            else:
                return None
            
            # Extract data bytes
            data = []
            for i in range(dlc):
                if data_start + i*2 + 1 < len(line):
                    byte_str = line[data_start + i*2:data_start + i*2 + 2]
                    data.append(int(byte_str, 16))
            
            return {
                "id": msg_id,
                "data": data,
                "extended": extended,
                "timestamp": datetime.now(),
                "type": "EXT" if extended else "STD"
            }
            
        except Exception as e:
            print(f"Error parsing message: {e}")
            return None
