# PyCAN Analyzer 🚗💻

A professional CAN bus analyzer and debugging tool built with Python and PyQt6. Supports multiple CAN adapters including SLCAN devices and PCAN PCIExpress cards with advanced multi-channel capabilities.

## 🎯 Overview

PyCAN Analyzer is a comprehensive CAN bus analysis tool designed for automotive diagnostics, embedded systems development, and CAN network debugging. It provides real-time message monitoring, transmission capabilities, and advanced filtering with support for multiple CAN adapters simultaneously.

## ✨ Key Features

- **🔌 Multi-Adapter Support**: SLCAN devices, PCAN PCIExpress cards
- **📊 Real-time Monitoring**: Live CAN message analysis with filtering
- **🎛️ Multi-Channel Management**: Individual or simultaneous channel control
- **📤 Message Transmission**: Send custom CAN messages with ID, data, and timing control
- **🔧 Configurable Test Messages**: Production-ready with optional simulated traffic
- **📋 DBC File Support**: Import and use CAN database files for message interpretation
- **💾 Log Replay**: Replay previously captured CAN sessions
- **🎨 Modern UI**: Clean, intuitive interface built with PyQt6

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PyQt6
- CAN adapter (SLCAN device or PCAN PCIExpress card)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd pycanalyzer
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python main.py
   ```

### Dependencies

```
PyQt6              # GUI framework
cantools           # CAN database support
pyserial           # Serial communication for SLCAN
python-can[pcan]   # PCAN support
```

## 🔧 Configuration

### Test Message Control

Configure development vs production behavior in `main.py`:

```python
# Configuration variables for development
ENABLE_TEST_MESSAGES = False  # Set to False to disable test message generation
TEST_MESSAGE_INTERVAL = 500   # Interval in milliseconds for test message updates
VERBOSE_LOGGING = False       # Set to True to enable detailed logging output
```

### Configuration Modes

#### **Production/Real Hardware Use**
```python
ENABLE_TEST_MESSAGES = False
TEST_MESSAGE_INTERVAL = 500
VERBOSE_LOGGING = False
```
- Clean interface showing only real CAN traffic
- No background processing overhead
- Minimal console output

#### **Development/Testing**
```python
ENABLE_TEST_MESSAGES = True
TEST_MESSAGE_INTERVAL = 100    # Fast updates for testing
VERBOSE_LOGGING = True
```
- Simulated traffic for GUI testing
- Detailed logging for debugging
- Fast message updates

#### **Demo Mode**
```python
ENABLE_TEST_MESSAGES = True
TEST_MESSAGE_INTERVAL = 1000   # Slower updates for presentation
VERBOSE_LOGGING = False
```
- Simulated traffic for demonstrations
- Realistic update speed
- Clean console output

## 🎛️ Hardware Support

### SLCAN Devices
- AliExpress CAN adapters
- USB-CAN analyzers
- Serial-based CAN interfaces
- Automatic device detection

### PCAN PCIExpress Cards
- Multi-channel PCIExpress CAN cards
- Individual channel management
- Real-time status monitoring
- Graceful degradation when hardware unavailable

## 📊 PCAN Multi-Channel Usage

### 1. **Open PCAN Connection Dialog**
   - Go to **Hardware** → **PCAN Connection**
   - The interface shows a table with all available PCAN channels

### 2. **Channel Management**
   - **Channel**: Channel name (PCAN-PCIe1, PCAN-PCIe2, etc.)
   - **Status**: Real-time Connected/Disconnected status
   - **Connect**: Individual connect/disconnect button per channel
   - **Test**: Test individual channel availability
   - **Send Test**: Send test message on specific channel

### 3. **Connection Options**
   
   **Individual Channels:**
   - Click "Connect" button for each desired channel
   - Each channel connects independently
   - Status updates in real-time
   
   **Multiple Channels:**
   - Select multiple rows in the table (Ctrl+click)
   - Connect to all selected channels simultaneously
   
   **Quick Testing:**
   - Click "Test All" to quickly check all channels
   - Shows availability status for each channel

### 4. **Message Transmission**
   - Open **Tools** → **Transmit Window**
   - Adapter selector shows all connected channels:
     - `SLCAN` - If SLCAN device connected
     - `PCAN: PCAN-PCIe1` - Individual PCAN channels
     - `PCAN: PCAN-PCIe2` - Individual PCAN channels
     - `PCAN: All Channels` - Send to all connected PCAN channels
   
   - **Select target adapter** from dropdown
   - **Click "Refresh"** to update available adapters

## 🎯 Usage Examples

### **Example 1: Single PCIExpress Channel**
1. Connect PCAN PCIExpress adapter
2. Open PCAN Connection → Connect to "PCAN-PCIe1"
3. In Transmit Window → Select "PCAN: PCAN-PCIe1"
4. Send messages on that specific channel

### **Example 2: Dual Channel Testing**
1. Connect two PCAN adapters or dual-channel card
2. Connect to both "PCAN-PCIe1" and "PCAN-PCIe2"
3. In Transmit Window → Select "PCAN: All Channels"
4. Send test message to both channels simultaneously

### **Example 3: Mixed Protocol Setup**
1. Connect SLCAN device (AliExpress adapter)
2. Connect PCAN PCIExpress adapter
3. Both appear in transmit window adapter list
4. Switch between protocols as needed for testing

## 📁 Project Structure

```
pycanalyzer/
├── main.py                 # Application entry point and configuration
├── gui.py                  # Main GUI window and interface logic
├── pcan_manager.py         # PCAN hardware management
├── slcan_manager.py        # SLCAN device management
├── transmit_window.py      # CAN message transmission interface
├── message_processor.py    # CAN message processing and filtering
├── dbc_manager.py          # DBC file handling
├── log_replay_window.py    # Log replay functionality
├── requirements.txt        # Python dependencies
├── autonomous.json         # Configuration file
└── test_*.py              # Test scripts
```

## 🔍 Features Deep Dive

### Real-time Message Monitoring
- Live CAN bus traffic display
- Filtering by message ID, data patterns
- Message frequency analysis
- Time-stamped message logging

### Message Transmission
- Custom CAN message creation
- Periodic message transmission
- Burst message sending
- Multi-channel broadcast support

### Configuration System
The application uses a three-variable configuration system:

1. **ENABLE_TEST_MESSAGES**: Controls simulated traffic generation
   - `False`: Production mode (clean interface, real traffic only)
   - `True`: Development mode (includes test messages for GUI testing)

2. **TEST_MESSAGE_INTERVAL**: Controls update frequency (1-10000ms)
   - Default: 500ms (2 updates per second)
   - Configurable for different testing scenarios

3. **VERBOSE_LOGGING**: Controls debug output
   - `False`: Minimal console output
   - `True`: Detailed status messages and debugging info

### Console Output Examples

**Test Messages Disabled (Production):**
```
✗ Test messages disabled
```

**Test Messages Enabled (Development):**
```
✓ Test messages enabled (interval: 500ms)
✓ Verbose logging enabled
```

### Hardware Status Feedback

**Connection Status:**
- ✅ **Connected**: Channel ready for use
- ❌ **Disconnected**: Channel not connected
- 🔄 **Real-time updates**: Status refreshes automatically

**Send Status:**
- `✓ Sent via PCAN-PCIe1` - Success on specific channel
- `✓ Sent on all 2 PCAN channels` - Success on all channels
- `⚠ Sent on 1/2 PCAN channels` - Partial success
- `✗ Failed to send on any PCAN channels` - All failed

## 🛠️ Development

### How Test Message System Works

1. **Startup**: Configuration variables read from `main.py`
2. **Initialization**: Settings passed to GUI main window
3. **Table Setup**: 
   - If enabled: Table populated with test IDs (0x100-0x104)
   - If disabled: Table left empty
4. **Timer**: 
   - If enabled: Timer started for periodic updates
   - If disabled: No timer created
5. **Runtime**: Test messages only generated when timer runs

### Adding New Adapters

To add support for additional CAN adapters:

1. Create a new manager class following the pattern of `pcan_manager.py` or `slcan_manager.py`
2. Implement required methods: `connect()`, `disconnect()`, `send_message()`, `start_listening()`
3. Add adapter selection logic to `transmit_window.py`
4. Update GUI connection dialogs as needed

## 🎨 Benefits

- **🎯 Professional Interface**: Clean, modern UI designed for efficiency
- **⚡ Performance**: Optimized for real-time CAN traffic analysis
- **🔧 Developer Friendly**: Easy configuration switching between development and production
- **📊 Flexibility**: Support for multiple adapter types and configurations
- **🛠️ Debugging Support**: Comprehensive logging and status feedback
- **🚀 Scalability**: Supports multiple adapters and channels simultaneously

## 📋 Requirements

- **Operating System**: Linux, Windows, macOS
- **Python**: 3.8 or higher
- **Hardware**: SLCAN device or PCAN PCIExpress card
- **Dependencies**: Listed in `requirements.txt`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with different hardware configurations
5. Submit a pull request

## 📜 License

[Add your license information here]

## 🆘 Support

For issues and questions:
1. Check the configuration guide above
2. Verify hardware connections
3. Enable verbose logging for debugging
4. Check console output for error messages

---

**PyCAN Analyzer** - Professional CAN bus analysis made simple! 🚗⚡
