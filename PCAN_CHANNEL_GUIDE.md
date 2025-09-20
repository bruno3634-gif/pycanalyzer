# PCAN Multi-Channel Selection Guide

## 🎯 Overview
Your CAN analyzer now supports selecting and using multiple PCAN channels simultaneously! You can connect to individual PCIExpress channels or use multiple channels at once.

## 🚀 How to Select PCAN Channels

### 1. **Open PCAN Connection Dialog**
   - Go to **Hardware** → **PCAN Connection**
   - The new interface shows a table with all available PCAN channels

### 2. **Channel Table Columns**
   - **Channel**: Channel name (PCAN-PCIe1, PCAN-PCIe2, etc.)
   - **Status**: Connected/Disconnected status
   - **Connect**: Individual connect/disconnect button per channel
   - **Test**: Test individual channel availability
   - **Send Test**: Send test message on specific channel

### 3. **Connect to Channels**
   
   **Option A: Individual Channels**
   - Click "Connect" button for each desired channel
   - Each channel connects independently
   - Status updates in real-time
   
   **Option B: Multiple Channels**
   - Select multiple rows in the table (Ctrl+click)
   - Click "Connect" button (legacy method)
   - Connects to all selected channels
   
   **Option C: Test All**
   - Click "Test All" to quickly check all channels
   - Shows availability status for each channel

### 4. **Using Channels in Transmit Window**
   - Open **Tools** → **Transmit Window**
   - New adapter selector shows all connected channels:
     - `SLCAN` - If SLCAN device connected
     - `PCAN: PCAN-PCIe1` - Individual PCAN channels
     - `PCAN: PCAN-PCIe2` - Individual PCAN channels
     - `PCAN: All Channels` - Send to all connected PCAN channels
   
   - **Select target adapter** from dropdown
   - **Click "Refresh"** to update available adapters

## 🎛️ Channel Selection Options

### **Single Channel Mode**
```
Send via: [PCAN: PCAN-PCIe1 ▼] [Refresh]
```
- Sends messages only on selected channel
- Perfect for channel-specific testing
- Individual channel monitoring

### **Multi-Channel Broadcast**
```
Send via: [PCAN: All Channels ▼] [Refresh]
```
- Sends same message to all connected PCAN channels
- Great for network-wide broadcasts
- Status shows success/failure count per channel

### **Mixed Adapter Usage**
```
Send via: [SLCAN ▼] [Refresh]
```
- Can use SLCAN and PCAN simultaneously
- Switch between adapters as needed
- Each adapter maintains independent connection

## 📊 Status Feedback

### **Connection Status**
- ✅ **Connected**: Channel ready for use
- ❌ **Disconnected**: Channel not connected
- 🔄 **Real-time updates**: Status refreshes automatically

### **Send Status**
- `✓ Sent via PCAN-PCIe1` - Success on specific channel
- `✓ Sent on all 2 PCAN channels` - Success on all channels
- `⚠ Sent on 1/2 PCAN channels` - Partial success
- `✗ Failed to send on any PCAN channels` - All failed

## 🔧 Advanced Features

### **Per-Channel Testing**
- Test each channel individually before connecting
- Send test messages to verify channel functionality
- Independent error reporting per channel

### **Automatic Refresh**
- Adapter list updates when channels connect/disconnect
- No need to restart application
- Seamless channel switching

### **Background Monitoring**
- All connected channels receive messages simultaneously
- Messages tagged with source channel
- Mixed protocol monitoring (SLCAN + PCAN)

## 💡 Usage Examples

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

## 🎯 Benefits

- **Flexibility**: Use any combination of PCAN channels
- **Efficiency**: Test multiple channels without reconnecting
- **Clarity**: Always know which channel you're using
- **Reliability**: Independent channel management
- **Scalability**: Supports multiple PCIExpress cards

Your CAN analyzer now gives you complete control over PCAN channel selection! 🚀
