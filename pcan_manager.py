# pcan_manager.py
import time
import threading
from datetime import datetime

try:
    from PCANBasic import *
    PCAN_AVAILABLE = True
except ImportError:
    PCAN_AVAILABLE = False
    print("PCAN library not available. Please install python-can[pcan] or PCANBasic")
    
    # Define dummy constants to prevent NameError
    PCAN_USBBUS1 = PCAN_USBBUS2 = PCAN_USBBUS3 = PCAN_USBBUS4 = None
    PCAN_USBBUS5 = PCAN_USBBUS6 = PCAN_USBBUS7 = PCAN_USBBUS8 = None
    PCAN_PCIBUS1 = PCAN_PCIBUS2 = PCAN_PCIBUS3 = PCAN_PCIBUS4 = None
    PCAN_PCIBUS5 = PCAN_PCIBUS6 = PCAN_PCIBUS7 = PCAN_PCIBUS8 = None
    PCAN_PCCBUS1 = PCAN_PCCBUS2 = None
    PCAN_BAUD_1M = PCAN_BAUD_500K = PCAN_BAUD_250K = PCAN_BAUD_125K = None
    PCAN_BAUD_100K = PCAN_BAUD_95K = PCAN_BAUD_83K = PCAN_BAUD_50K = None
    PCAN_BAUD_47K = PCAN_BAUD_33K = PCAN_BAUD_20K = PCAN_BAUD_10K = PCAN_BAUD_5K = None
    PCAN_ERROR_OK = PCAN_ERROR_ILLHW = PCAN_ERROR_QRCVEMPTY = None
    PCAN_MESSAGE_STANDARD = PCAN_MESSAGE_EXTENDED = PCAN_MESSAGE_RTR = None
    PCAN_RECEIVE_EVENT = None
    
    class TPCANMsg:
        def __init__(self):
            self.ID = 0
            self.LEN = 0
            self.MSGTYPE = 0
            self.DATA = [0] * 8
    
    def CAN_Initialize(channel, baudrate): return None
    def CAN_Uninitialize(channel): return None
    def CAN_GetStatus(channel): return None
    def CAN_SetValue(channel, param, value): return None
    def CAN_Write(channel, msg): return None
    def CAN_Read(channel): return (None, None, None)
    def CAN_GetErrorText(error, lang): return (None, "")

class PCANManager:
    def __init__(self):
        self.pcan_handle = None
        self.is_connected = False
        self.is_listening = False
        self.listen_thread = None
        self.message_callback = None
        self.stop_listening = False
        self.available_channels = []
        
        # Multi-channel support
        self.connected_channels = {}  # {channel: handle}
        self.channel_listeners = {}   # {channel: thread}
        
        if PCAN_AVAILABLE:
            self._initialize_channels()
    
    def _initialize_channels(self):
        """Initialize list of available PCAN channels"""
        self.available_channels = [
            ("PCAN-USB1", PCAN_USBBUS1),
            ("PCAN-USB2", PCAN_USBBUS2),
            ("PCAN-USB3", PCAN_USBBUS3),
            ("PCAN-USB4", PCAN_USBBUS4),
            ("PCAN-USB5", PCAN_USBBUS5),
            ("PCAN-USB6", PCAN_USBBUS6),
            ("PCAN-USB7", PCAN_USBBUS7),
            ("PCAN-USB8", PCAN_USBBUS8),
            ("PCAN-PCI1", PCAN_PCIBUS1),
            ("PCAN-PCI2", PCAN_PCIBUS2),
            ("PCAN-PCI3", PCAN_PCIBUS3),
            ("PCAN-PCI4", PCAN_PCIBUS4),
            ("PCAN-PCI5", PCAN_PCIBUS5),
            ("PCAN-PCI6", PCAN_PCIBUS6),
            ("PCAN-PCI7", PCAN_PCIBUS7),
            ("PCAN-PCI8", PCAN_PCIBUS8),
            ("PCAN-PCIe1", PCAN_PCCBUS1),
            ("PCAN-PCIe2", PCAN_PCCBUS2),
        ]
    
    def list_available_channels(self):
        """List all available PCAN channels"""
        if not PCAN_AVAILABLE:
            return []
        
        available = []
        for name, channel in self.available_channels:
            try:
                # Try to get channel condition to see if it's available
                result = CAN_GetStatus(channel)
                if result != PCAN_ERROR_ILLHW:  # Channel exists
                    available.append((name, channel))
            except:
                continue
        
        return available
    
    def test_connection(self, channel, baudrate=None):
        """Test if a PCAN channel is available and can be initialized"""
        if not PCAN_AVAILABLE:
            return False
        
        if baudrate is None:
            baudrate = PCAN_BAUD_500K
        
        try:
            # Try to initialize the channel
            result = CAN_Initialize(channel, baudrate)
            if result == PCAN_ERROR_OK:
                # Uninitialize immediately after test
                CAN_Uninitialize(channel)
                return True
            return False
        except Exception as e:
            print(f"PCAN test connection failed: {e}")
            return False
    
    def connect(self, channel, baudrate=PCAN_BAUD_500K):
        """Connect to PCAN channel"""
        if not PCAN_AVAILABLE:
            return False, "PCAN library not available"
        
        try:
            # Initialize the PCAN channel
            result = CAN_Initialize(channel, baudrate)
            
            if result != PCAN_ERROR_OK:
                error_text = self._get_error_text(result)
                return False, f"Failed to initialize PCAN: {error_text}"
            
            self.pcan_handle = channel
            self.is_connected = True
            
            # Set receive queue size
            CAN_SetValue(channel, PCAN_RECEIVE_EVENT, 0)
            
            return True, "Connected successfully"
            
        except Exception as e:
            return False, f"PCAN connection error: {str(e)}"
    
    def disconnect(self):
        """Disconnect from PCAN"""
        if self.is_connected and self.pcan_handle:
            try:
                self.stop_listening_messages()
                CAN_Uninitialize(self.pcan_handle)
                self.is_connected = False
                self.pcan_handle = None
                return True, "Disconnected successfully"
            except Exception as e:
                return False, f"Disconnect error: {str(e)}"
        return True, "Already disconnected"
    
    def send_message(self, msg_id, data, is_extended=False, is_rtr=False):
        """Send a CAN message"""
        if not self.is_connected:
            return False, "Not connected"
        
        try:
            # Create PCAN message
            msg = TPCANMsg()
            msg.ID = msg_id
            msg.LEN = len(data)
            msg.MSGTYPE = PCAN_MESSAGE_STANDARD
            
            if is_extended:
                msg.MSGTYPE |= PCAN_MESSAGE_EXTENDED
            if is_rtr:
                msg.MSGTYPE |= PCAN_MESSAGE_RTR
            
            # Set data
            for i in range(len(data)):
                msg.DATA[i] = data[i]
            
            # Send message
            result = CAN_Write(self.pcan_handle, msg)
            
            if result == PCAN_ERROR_OK:
                return True, "Message sent successfully"
            else:
                error_text = self._get_error_text(result)
                return False, f"Send failed: {error_text}"
                
        except Exception as e:
            return False, f"Send error: {str(e)}"
    
    def start_listening(self, callback):
        """Start listening for CAN messages"""
        if not self.is_connected:
            return False, "Not connected"
        
        self.message_callback = callback
        self.stop_listening = False
        self.is_listening = True
        
        self.listen_thread = threading.Thread(target=self._listen_worker)
        self.listen_thread.daemon = True
        self.listen_thread.start()
        
        return True, "Started listening"
    
    def stop_listening_messages(self):
        """Stop listening for messages"""
        self.stop_listening = True
        self.is_listening = False
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)
    
    def _listen_worker(self):
        """Worker thread for listening to messages"""
        while not self.stop_listening and self.is_connected:
            try:
                # Read message from PCAN
                result = CAN_Read(self.pcan_handle)
                
                if result[0] == PCAN_ERROR_OK:
                    msg, timestamp = result[1], result[2]
                    
                    # Convert to our message format
                    message = {
                        "id": msg.ID,
                        "data": list(msg.DATA[:msg.LEN]),
                        "dlc": msg.LEN,
                        "timestamp": datetime.now(),
                        "is_extended": bool(msg.MSGTYPE & PCAN_MESSAGE_EXTENDED),
                        "is_rtr": bool(msg.MSGTYPE & PCAN_MESSAGE_RTR),
                        "source": "PCAN"
                    }
                    
                    if self.message_callback:
                        self.message_callback(message)
                
                elif result[0] == PCAN_ERROR_QRCVEMPTY:
                    # No message available, wait a bit
                    time.sleep(0.001)
                else:
                    # Other error
                    error_text = self._get_error_text(result[0])
                    print(f"PCAN read error: {error_text}")
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"PCAN listen error: {e}")
                time.sleep(0.01)
    
    def _get_error_text(self, error_code):
        """Get error text for PCAN error code"""
        if not PCAN_AVAILABLE:
            return "PCAN not available"
        
        try:
            result = CAN_GetErrorText(error_code, 0x09)  # English
            if result[0] == PCAN_ERROR_OK:
                return result[1].decode('utf-8', errors='ignore')
            else:
                return f"Error code: {error_code:X}"
        except:
            return f"Error code: {error_code:X}"
    
    @staticmethod
    def get_baudrate_value(baudrate_str):
        """Convert baudrate string to PCAN constant"""
        baudrates = {
            "1000000": PCAN_BAUD_1M,
            "500000": PCAN_BAUD_500K,
            "250000": PCAN_BAUD_250K,
            "125000": PCAN_BAUD_125K,
            "100000": PCAN_BAUD_100K,
            "95000": PCAN_BAUD_95K,
            "83000": PCAN_BAUD_83K,
            "50000": PCAN_BAUD_50K,
            "47000": PCAN_BAUD_47K,
            "33000": PCAN_BAUD_33K,
            "20000": PCAN_BAUD_20K,
            "10000": PCAN_BAUD_10K,
            "5000": PCAN_BAUD_5K,
        }
        return baudrates.get(str(baudrate_str), PCAN_BAUD_500K)
    
    @staticmethod
    def get_available_baudrates():
        """Get list of available baudrates"""
        return [
            "1000000", "500000", "250000", "125000", "100000",
            "95000", "83000", "50000", "47000", "33000",
            "20000", "10000", "5000"
        ]
    
    # Multi-channel methods
    def connect_channel(self, channel, baudrate=None):
        """Connect to a specific PCAN channel"""
        if not PCAN_AVAILABLE:
            return False, "PCAN library not available"
        
        if baudrate is None:
            baudrate = PCAN_BAUD_500K
        
        try:
            # Initialize the specific PCAN channel
            result = CAN_Initialize(channel, baudrate)
            
            if result != PCAN_ERROR_OK:
                error_text = self._get_error_text(result)
                return False, f"Failed to initialize PCAN channel: {error_text}"
            
            self.connected_channels[channel] = channel
            
            # Set receive queue size
            CAN_SetValue(channel, PCAN_RECEIVE_EVENT, 0)
            
            # Update overall connection status
            self.is_connected = len(self.connected_channels) > 0
            if not self.pcan_handle:  # Set primary handle to first connected channel
                self.pcan_handle = channel
            
            return True, "Connected successfully"
            
        except Exception as e:
            return False, f"PCAN connection error: {str(e)}"
    
    def disconnect_channel(self, channel):
        """Disconnect from a specific PCAN channel"""
        if channel not in self.connected_channels:
            return True, "Channel not connected"
        
        try:
            # Stop listening on this channel
            if channel in self.channel_listeners:
                self.stop_channel_listening(channel)
            
            # Uninitialize the channel
            CAN_Uninitialize(channel)
            
            # Remove from connected channels
            del self.connected_channels[channel]
            
            # Update primary handle if needed
            if self.pcan_handle == channel:
                if self.connected_channels:
                    self.pcan_handle = next(iter(self.connected_channels.keys()))
                else:
                    self.pcan_handle = None
                    self.is_connected = False
            
            return True, "Disconnected successfully"
            
        except Exception as e:
            return False, f"Disconnect error: {str(e)}"
    
    def disconnect_all(self):
        """Disconnect from all PCAN channels"""
        errors = []
        
        # Disconnect each channel
        for channel in list(self.connected_channels.keys()):
            success, message = self.disconnect_channel(channel)
            if not success:
                errors.append(f"Channel {channel:02X}: {message}")
        
        if errors:
            return False, "; ".join(errors)
        else:
            return True, "All channels disconnected"
    
    def send_message_on_channel(self, channel, msg_id, data, is_extended=False, is_rtr=False):
        """Send a CAN message on a specific channel"""
        if channel not in self.connected_channels:
            return False, "Channel not connected"
        
        try:
            # Create PCAN message
            msg = TPCANMsg()
            msg.ID = msg_id
            msg.LEN = len(data)
            msg.MSGTYPE = PCAN_MESSAGE_STANDARD
            
            if is_extended:
                msg.MSGTYPE |= PCAN_MESSAGE_EXTENDED
            if is_rtr:
                msg.MSGTYPE |= PCAN_MESSAGE_RTR
            
            # Set data
            for i in range(len(data)):
                msg.DATA[i] = data[i]
            
            # Send message on specific channel
            result = CAN_Write(channel, msg)
            
            if result == PCAN_ERROR_OK:
                return True, "Message sent successfully"
            else:
                error_text = self._get_error_text(result)
                return False, f"Send failed: {error_text}"
                
        except Exception as e:
            return False, f"Send error: {str(e)}"
    
    def start_channel_listening(self, channel, callback):
        """Start listening on a specific channel"""
        if channel not in self.connected_channels:
            return False, "Channel not connected"
        
        if channel in self.channel_listeners:
            return True, "Already listening on this channel"
        
        # Create listener thread for this channel
        thread = threading.Thread(target=self._channel_listen_worker, args=(channel, callback))
        thread.daemon = True
        self.channel_listeners[channel] = {'thread': thread, 'stop': False}
        thread.start()
        
        return True, "Started listening on channel"
    
    def stop_channel_listening(self, channel):
        """Stop listening on a specific channel"""
        if channel not in self.channel_listeners:
            return
        
        # Signal thread to stop
        self.channel_listeners[channel]['stop'] = True
        
        # Wait for thread to finish
        thread = self.channel_listeners[channel]['thread']
        if thread.is_alive():
            thread.join(timeout=1.0)
        
        # Remove from listeners
        del self.channel_listeners[channel]
    
    def _channel_listen_worker(self, channel, callback):
        """Worker thread for listening to messages on a specific channel"""
        listener_info = self.channel_listeners.get(channel)
        if not listener_info:
            return
        
        while not listener_info['stop'] and channel in self.connected_channels:
            try:
                # Read message from specific PCAN channel
                result = CAN_Read(channel)
                
                if result[0] == PCAN_ERROR_OK:
                    msg, timestamp = result[1], result[2]
                    
                    # Convert to our message format
                    message = {
                        "id": msg.ID,
                        "data": list(msg.DATA[:msg.LEN]),
                        "dlc": msg.LEN,
                        "timestamp": datetime.now(),
                        "is_extended": bool(msg.MSGTYPE & PCAN_MESSAGE_EXTENDED),
                        "is_rtr": bool(msg.MSGTYPE & PCAN_MESSAGE_RTR),
                        "source": f"PCAN-{channel:02X}",
                        "channel": channel
                    }
                    
                    if callback:
                        callback(message)
                
                elif result[0] == PCAN_ERROR_QRCVEMPTY:
                    # No message available, wait a bit
                    time.sleep(0.001)
                else:
                    # Other error
                    if result[0] != PCAN_ERROR_ILLHW:  # Don't spam for disconnected channels
                        error_text = self._get_error_text(result[0])
                        print(f"PCAN channel {channel:02X} read error: {error_text}")
                    time.sleep(0.01)
                    
            except Exception as e:
                print(f"PCAN channel {channel:02X} listen error: {e}")
                time.sleep(0.01)
    
    def get_connected_channels(self):
        """Get list of connected channels"""
        return list(self.connected_channels.keys())
    
    def is_channel_connected(self, channel):
        """Check if a specific channel is connected"""
        return channel in self.connected_channels
