# transmit_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QInputDialog, QComboBox, QSpinBox, QCheckBox, QLineEdit,
    QGroupBox, QGridLayout, QMessageBox, QHeaderView, QTabWidget
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt
import json
import datetime

class TransmitWindow(QMainWindow):
    def __init__(self, slcan_manager, dbc_manager, pcan_manager=None):
        super().__init__()
        print("Initializing TransmitWindow...")
        self.slcan_manager = slcan_manager
        self.dbc_manager = dbc_manager
        self.pcan_manager = pcan_manager
        self.periodic_timers = {}
        
        print("Setting up window properties...")
        self.setWindowTitle("CAN Message Transmitter")
        self.resize(800, 600)
        
        print("Creating central widget...")
        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        print("Creating tab widget...")
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        print("Creating tabs...")
        # Manual transmission tab
        self.manual_tab = self.create_manual_tab()
        self.tab_widget.addTab(self.manual_tab, "Manual Send")
        
        # Periodic transmission tab
        self.periodic_tab = self.create_periodic_tab()
        self.tab_widget.addTab(self.periodic_tab, "Periodic Messages")
        
        # Quick send tab
        self.quick_tab = self.create_quick_tab()
        self.tab_widget.addTab(self.quick_tab, "Quick Send")
        
        # Status bar with adapter information
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        status_layout.addWidget(self.status_label)
        
        # Adapter selector
        status_layout.addWidget(QLabel("Send via:"))
        self.adapter_combo = QComboBox()
        self.adapter_combo.setMinimumWidth(150)
        status_layout.addWidget(self.adapter_combo)
        
        self.refresh_adapters_btn = QPushButton("Refresh")
        self.refresh_adapters_btn.clicked.connect(self.refresh_adapters)
        status_layout.addWidget(self.refresh_adapters_btn)
        
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # Refresh adapter list initially
        self.refresh_adapters()
        
        print("TransmitWindow initialization complete")
        
    def create_manual_tab(self):
        """Create manual transmission tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Message configuration group
        msg_group = QGroupBox("Message Configuration")
        msg_layout = QGridLayout()
        msg_group.setLayout(msg_layout)
        layout.addWidget(msg_group)
        
        # ID input
        msg_layout.addWidget(QLabel("CAN ID:"), 0, 0)
        self.manual_id_input = QSpinBox()
        self.manual_id_input.setMinimum(0)
        self.manual_id_input.setMaximum(0x1FFFFFFF)
        self.manual_id_input.setDisplayIntegerBase(16)
        self.manual_id_input.setValue(0x123)
        msg_layout.addWidget(self.manual_id_input, 0, 1)
        
        # Extended frame checkbox
        self.manual_extended_cb = QCheckBox("Extended Frame (29-bit)")
        msg_layout.addWidget(self.manual_extended_cb, 0, 2)
        
        # Data input
        msg_layout.addWidget(QLabel("Data (hex):"), 1, 0)
        self.manual_data_input = QLineEdit("00 01 02 03 04 05 06 07")
        msg_layout.addWidget(self.manual_data_input, 1, 1, 1, 2)
        
        # DLC
        msg_layout.addWidget(QLabel("DLC:"), 2, 0)
        self.manual_dlc_input = QSpinBox()
        self.manual_dlc_input.setMinimum(0)
        self.manual_dlc_input.setMaximum(8)
        self.manual_dlc_input.setValue(8)
        msg_layout.addWidget(self.manual_dlc_input, 2, 1)
        
        # Auto-update DLC checkbox
        self.auto_dlc_cb = QCheckBox("Auto-update DLC from data")
        self.auto_dlc_cb.setChecked(True)
        self.auto_dlc_cb.toggled.connect(self.update_manual_dlc)
        msg_layout.addWidget(self.auto_dlc_cb, 2, 2)
        
        # Data input change handler
        self.manual_data_input.textChanged.connect(self.update_manual_dlc)
        
        # Send controls group
        send_group = QGroupBox("Send Controls")
        send_layout = QHBoxLayout()
        send_group.setLayout(send_layout)
        layout.addWidget(send_group)
        
        # Single send button
        self.send_once_btn = QPushButton("Send Once")
        self.send_once_btn.clicked.connect(self.send_manual_message)
        send_layout.addWidget(self.send_once_btn)
        
        # Multiple send
        send_layout.addWidget(QLabel("Count:"))
        self.send_count_input = QSpinBox()
        self.send_count_input.setMinimum(1)
        self.send_count_input.setMaximum(1000)
        self.send_count_input.setValue(10)
        send_layout.addWidget(self.send_count_input)
        
        self.send_multiple_btn = QPushButton("Send Multiple")
        self.send_multiple_btn.clicked.connect(self.send_multiple_messages)
        send_layout.addWidget(self.send_multiple_btn)
        
        # Interval input
        send_layout.addWidget(QLabel("Interval (ms):"))
        self.send_interval_input = QSpinBox()
        self.send_interval_input.setMinimum(1)
        self.send_interval_input.setMaximum(10000)
        self.send_interval_input.setValue(100)
        send_layout.addWidget(self.send_interval_input)
        
        # DBC signals group (if DBC loaded)
        self.dbc_group = QGroupBox("DBC Signal Encoding")
        dbc_layout = QVBoxLayout()
        self.dbc_group.setLayout(dbc_layout)
        layout.addWidget(self.dbc_group)
        
        # Message selector
        dbc_select_layout = QHBoxLayout()
        dbc_select_layout.addWidget(QLabel("DBC Message:"))
        self.dbc_message_combo = QComboBox()
        self.dbc_message_combo.currentTextChanged.connect(self.load_dbc_signals)
        dbc_select_layout.addWidget(self.dbc_message_combo)
        
        self.refresh_dbc_btn = QPushButton("Refresh")
        self.refresh_dbc_btn.clicked.connect(self.refresh_dbc_messages)
        dbc_select_layout.addWidget(self.refresh_dbc_btn)
        dbc_layout.addLayout(dbc_select_layout)
        
        # Signal table
        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(3)
        self.signal_table.setHorizontalHeaderLabels(["Signal", "Value", "Unit"])
        self.signal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        dbc_layout.addWidget(self.signal_table)
        
        # Encode button
        self.encode_btn = QPushButton("Encode Signals to Data")
        self.encode_btn.clicked.connect(self.encode_signals)
        dbc_layout.addWidget(self.encode_btn)
        
        layout.addStretch()
        self.refresh_dbc_messages()
        
        return widget
    
    def create_periodic_tab(self):
        """Create periodic transmission tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)
        
        self.add_periodic_btn = QPushButton("Add Periodic Message")
        self.add_periodic_btn.clicked.connect(self.add_periodic_message)
        controls_layout.addWidget(self.add_periodic_btn)
        
        self.start_all_btn = QPushButton("Start All")
        self.start_all_btn.clicked.connect(self.start_all_periodic)
        controls_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = QPushButton("Stop All")
        self.stop_all_btn.clicked.connect(self.stop_all_periodic)
        controls_layout.addWidget(self.stop_all_btn)
        
        controls_layout.addStretch()
        
        # Periodic messages table
        self.periodic_table = QTableWidget()
        self.periodic_table.setColumnCount(8)
        self.periodic_table.setHorizontalHeaderLabels([
            "ID", "Extended", "Data", "Period (ms)", "Status", "Count", "Start/Stop", "Remove"
        ])
        self.periodic_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.periodic_table)
        
        return widget
    
    def create_quick_tab(self):
        """Create quick send tab with predefined messages"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        # Controls
        controls_layout = QHBoxLayout()
        layout.addLayout(controls_layout)
        
        self.add_quick_btn = QPushButton("Add Quick Message")
        self.add_quick_btn.clicked.connect(self.add_quick_message)
        controls_layout.addWidget(self.add_quick_btn)
        
        self.save_quick_btn = QPushButton("Save Templates")
        self.save_quick_btn.clicked.connect(self.save_quick_templates)
        controls_layout.addWidget(self.save_quick_btn)
        
        self.load_quick_btn = QPushButton("Load Templates")
        self.load_quick_btn.clicked.connect(self.load_quick_templates)
        controls_layout.addWidget(self.load_quick_btn)
        
        controls_layout.addStretch()
        
        # Quick messages grid
        self.quick_scroll = QWidget()
        self.quick_layout = QGridLayout()
        self.quick_scroll.setLayout(self.quick_layout)
        layout.addWidget(self.quick_scroll)
        
        # Add some default quick messages
        self.add_default_quick_messages()
        
        return widget
    
    def update_manual_dlc(self):
        """Update DLC based on data input"""
        if self.auto_dlc_cb.isChecked():
            data_str = self.manual_data_input.text().strip()
            if data_str:
                hex_bytes = data_str.replace(" ", "").replace(",", "")
                dlc = min(len(hex_bytes) // 2, 8)
                self.manual_dlc_input.setValue(dlc)
    
    def send_manual_message(self):
        """Send a single manual message"""
        if not self.is_any_adapter_connected():
            QMessageBox.warning(self, "Error", "Not connected to any CAN adapter")
            return
        
        try:
            msg_id = self.manual_id_input.value()
            extended = self.manual_extended_cb.isChecked()
            
            # Parse data
            data = self.parse_data_string(self.manual_data_input.text())
            
            # Limit to DLC
            dlc = self.manual_dlc_input.value()
            data = data[:dlc]
            
            success = self.send_can_message(msg_id, data, extended)
            
            if success:
                self.status_label.setText(f"✓ Sent: ID=0x{msg_id:X}, Data={data}")
            else:
                self.status_label.setText(f"✗ Failed: ID=0x{msg_id:X}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error sending message: {e}")
    
    def send_multiple_messages(self):
        """Send multiple messages with interval"""
        if not self.is_any_adapter_connected():
            QMessageBox.warning(self, "Error", "Not connected to any CAN adapter")
            return
        
        count = self.send_count_input.value()
        interval = self.send_interval_input.value()
        
        # Create timer for multiple sends
        self.multi_send_timer = QTimer()
        self.multi_send_count = 0
        self.multi_send_max = count
        
        def send_next():
            if self.multi_send_count < self.multi_send_max:
                self.send_manual_message()
                self.multi_send_count += 1
                self.status_label.setText(f"Sending {self.multi_send_count}/{self.multi_send_max}...")
            else:
                self.multi_send_timer.stop()
                self.status_label.setText(f"✓ Sent {self.multi_send_max} messages")
        
        self.multi_send_timer.timeout.connect(send_next)
        self.multi_send_timer.start(interval)
    
    def parse_data_string(self, data_str):
        """Parse hex data string into byte array"""
        data = []
        if data_str.strip():
            hex_bytes = data_str.replace(" ", "").replace(",", "")
            for i in range(0, len(hex_bytes), 2):
                if i + 1 < len(hex_bytes):
                    data.append(int(hex_bytes[i:i+2], 16))
        return data
    
    def refresh_dbc_messages(self):
        """Refresh DBC message list"""
        self.dbc_message_combo.clear()
        if self.dbc_manager.db:
            for msg in self.dbc_manager.db.messages:
                self.dbc_message_combo.addItem(msg.name)
        self.load_dbc_signals()
    
    def load_dbc_signals(self):
        """Load signals for selected DBC message"""
        self.signal_table.setRowCount(0)
        
        if not self.dbc_manager.db:
            return
        
        msg_name = self.dbc_message_combo.currentText()
        if not msg_name:
            return
        
        try:
            message = next((msg for msg in self.dbc_manager.db.messages if msg.name == msg_name), None)
            if not message:
                return
            
            # Update ID
            self.manual_id_input.setValue(message.frame_id)
            
            # Load signals
            self.signal_table.setRowCount(len(message.signals))
            for i, signal in enumerate(message.signals):
                # Signal name
                self.signal_table.setItem(i, 0, QTableWidgetItem(signal.name))
                
                # Value input (spinbox or line edit)
                value_widget = QSpinBox()
                if hasattr(signal, 'minimum') and hasattr(signal, 'maximum'):
                    value_widget.setMinimum(int(signal.minimum) if signal.minimum is not None else -2147483648)
                    value_widget.setMaximum(int(signal.maximum) if signal.maximum is not None else 2147483647)
                else:
                    value_widget.setMinimum(-2147483648)
                    value_widget.setMaximum(2147483647)
                value_widget.setValue(0)
                self.signal_table.setCellWidget(i, 1, value_widget)
                
                # Unit
                unit = signal.unit if signal.unit else ""
                self.signal_table.setItem(i, 2, QTableWidgetItem(unit))
                
        except Exception as e:
            print(f"Error loading DBC signals: {e}")
    
    def encode_signals(self):
        """Encode signals to data bytes"""
        if not self.dbc_manager.db:
            QMessageBox.warning(self, "Error", "No DBC file loaded")
            return
        
        msg_name = self.dbc_message_combo.currentText()
        if not msg_name:
            return
        
        try:
            message = next((msg for msg in self.dbc_manager.db.messages if msg.name == msg_name), None)
            if not message:
                return
            
            # Collect signal values
            signal_values = {}
            for i in range(self.signal_table.rowCount()):
                signal_name = self.signal_table.item(i, 0).text()
                value_widget = self.signal_table.cellWidget(i, 1)
                if value_widget:
                    signal_values[signal_name] = value_widget.value()
            
            # Encode message
            data = message.encode(signal_values)
            
            # Update data field
            hex_str = " ".join(f"{b:02X}" for b in data)
            self.manual_data_input.setText(hex_str)
            
            self.status_label.setText(f"✓ Encoded {msg_name} with {len(signal_values)} signals")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error encoding signals: {e}")
    
    def add_periodic_message(self):
        """Add a new periodic message"""
        row = self.periodic_table.rowCount()
        self.periodic_table.insertRow(row)
        
        # ID
        id_widget = QSpinBox()
        id_widget.setMaximum(0x1FFFFFFF)
        id_widget.setDisplayIntegerBase(16)
        id_widget.setValue(0x100 + row)
        self.periodic_table.setCellWidget(row, 0, id_widget)
        
        # Extended
        ext_widget = QCheckBox()
        self.periodic_table.setCellWidget(row, 1, ext_widget)
        
        # Data
        data_widget = QLineEdit("00 01 02 03 04 05 06 07")
        self.periodic_table.setCellWidget(row, 2, data_widget)
        
        # Period
        period_widget = QSpinBox()
        period_widget.setMinimum(10)
        period_widget.setMaximum(60000)
        period_widget.setValue(1000)
        self.periodic_table.setCellWidget(row, 3, period_widget)
        
        # Status
        self.periodic_table.setItem(row, 4, QTableWidgetItem("Stopped"))
        
        # Count
        self.periodic_table.setItem(row, 5, QTableWidgetItem("0"))
        
        # Start/Stop button
        start_stop_btn = QPushButton("Start")
        start_stop_btn.clicked.connect(lambda: self.toggle_periodic_message(row))
        self.periodic_table.setCellWidget(row, 6, start_stop_btn)
        
        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.remove_periodic_message(row))
        self.periodic_table.setCellWidget(row, 7, remove_btn)
    
    def toggle_periodic_message(self, row):
        """Start or stop a periodic message"""
        if row in self.periodic_timers:
            # Stop
            self.periodic_timers[row].stop()
            del self.periodic_timers[row]
            self.periodic_table.item(row, 4).setText("Stopped")
            button = self.periodic_table.cellWidget(row, 6)
            if button:
                button.setText("Start")
        else:
            # Start
            if not self.is_any_adapter_connected():
                QMessageBox.warning(self, "Error", "Not connected to any CAN adapter")
                return
            
            period_widget = self.periodic_table.cellWidget(row, 3)
            period = period_widget.value() if period_widget else 1000
            
            timer = QTimer()
            timer.timeout.connect(lambda: self.send_periodic_message(row))
            timer.start(period)
            
            self.periodic_timers[row] = timer
            self.periodic_table.item(row, 4).setText("Running")
            button = self.periodic_table.cellWidget(row, 6)
            if button:
                button.setText("Stop")
    
    def send_periodic_message(self, row):
        """Send a periodic message"""
        try:
            # Get message data
            id_widget = self.periodic_table.cellWidget(row, 0)
            ext_widget = self.periodic_table.cellWidget(row, 1)
            data_widget = self.periodic_table.cellWidget(row, 2)
            
            if not all([id_widget, ext_widget, data_widget]):
                return
            
            msg_id = id_widget.value()
            extended = ext_widget.isChecked()
            data = self.parse_data_string(data_widget.text())
            
            success = self.send_can_message(msg_id, data, extended)
            
            # Update count
            count_item = self.periodic_table.item(row, 5)
            if count_item:
                current_count = int(count_item.text())
                count_item.setText(str(current_count + 1))
            
            if not success:
                self.status_label.setText(f"✗ Periodic send failed: ID=0x{msg_id:X}")
                
        except Exception as e:
            print(f"Error sending periodic message: {e}")
    
    def start_all_periodic(self):
        """Start all periodic messages"""
        for row in range(self.periodic_table.rowCount()):
            if row not in self.periodic_timers:
                self.toggle_periodic_message(row)
    
    def stop_all_periodic(self):
        """Stop all periodic messages"""
        for row in list(self.periodic_timers.keys()):
            self.toggle_periodic_message(row)
    
    def remove_periodic_message(self, row):
        """Remove a periodic message"""
        if row in self.periodic_timers:
            self.periodic_timers[row].stop()
            del self.periodic_timers[row]
        self.periodic_table.removeRow(row)
        
        # Update timer indices
        new_timers = {}
        for old_row, timer in self.periodic_timers.items():
            new_row = old_row if old_row < row else old_row - 1
            new_timers[new_row] = timer
        self.periodic_timers = new_timers
    
    def add_quick_message(self):
        """Add a new quick send button"""
        # Get message details from user
        msg_id, ok = QInputDialog.getInt(self, "Quick Message", "CAN ID (hex):", 0x123, 0, 0x1FFFFFFF)
        if not ok:
            return
        
        data_str, ok = QInputDialog.getText(self, "Quick Message", "Data (hex):", text="00 01 02 03")
        if not ok:
            return
        
        name, ok = QInputDialog.getText(self, "Quick Message", "Button Name:", text=f"ID_{msg_id:X}")
        if not ok:
            return
        
        self.add_quick_button(name, msg_id, data_str, False)
    
    def add_quick_button(self, name, msg_id, data_str, extended=False):
        """Add a quick send button"""
        row = self.quick_layout.rowCount()
        col = 0
        
        # Find next available position
        while self.quick_layout.itemAtPosition(row, col):
            col += 1
            if col >= 4:  # 4 columns max
                col = 0
                row += 1
        
        button = QPushButton(name)
        button.setMinimumHeight(50)
        button.clicked.connect(lambda: self.send_quick_message(msg_id, data_str, extended))
        
        # Add context menu for editing/removing
        button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        button.customContextMenuRequested.connect(
            lambda pos: self.show_quick_context_menu(button, name, msg_id, data_str, extended)
        )
        
        self.quick_layout.addWidget(button, row, col)
    
    def send_quick_message(self, msg_id, data_str, extended):
        """Send a quick message"""
        if not self.is_any_adapter_connected():
            QMessageBox.warning(self, "Error", "Not connected to any CAN adapter")
            return
        
        try:
            data = self.parse_data_string(data_str)
            success = self.send_can_message(msg_id, data, extended)
            
            if success:
                self.status_label.setText(f"✓ Quick sent: ID=0x{msg_id:X}")
            else:
                self.status_label.setText(f"✗ Quick send failed: ID=0x{msg_id:X}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error sending quick message: {e}")
    
    def show_quick_context_menu(self, button, name, msg_id, data_str, extended):
        """Show context menu for quick button"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        
        edit_action = menu.addAction("Edit")
        remove_action = menu.addAction("Remove")
        
        action = menu.exec(button.mapToGlobal(button.rect().center()))
        
        if action == edit_action:
            self.edit_quick_button(button, name, msg_id, data_str, extended)
        elif action == remove_action:
            self.remove_quick_button(button)
    
    def edit_quick_button(self, button, name, msg_id, data_str, extended):
        """Edit a quick button"""
        # Implementation for editing quick buttons
        pass
    
    def remove_quick_button(self, button):
        """Remove a quick button"""
        self.quick_layout.removeWidget(button)
        button.deleteLater()
    
    def add_default_quick_messages(self):
        """Add some default quick messages"""
        defaults = [
            ("Engine RPM", 0x200, "10 27 00 00 00 00 00 00"),
            ("Vehicle Speed", 0x201, "00 00 3C 00 00 00 00 00"),
            ("Brake Status", 0x202, "01 00 00 00 00 00 00 00"),
            ("Turn Signals", 0x203, "02 00 00 00 00 00 00 00"),
        ]
        
        for name, msg_id, data in defaults:
            self.add_quick_button(name, msg_id, data)
    
    def save_quick_templates(self):
        """Save quick message templates to file"""
        # Implementation for saving templates
        QMessageBox.information(self, "Info", "Save templates feature to be implemented")
    
    def load_quick_templates(self):
        """Load quick message templates from file"""
        # Implementation for loading templates
        QMessageBox.information(self, "Info", "Load templates feature to be implemented")
    
    def is_any_adapter_connected(self):
        """Check if any CAN adapter is connected"""
        return ((self.pcan_manager and (self.pcan_manager.is_connected or self.pcan_manager.connected_channels)) or 
                (self.slcan_manager and self.slcan_manager.is_connected))
    
    def refresh_adapters(self):
        """Refresh the list of available adapters and channels"""
        self.adapter_combo.clear()
        
        # Add SLCAN if connected
        if self.slcan_manager and self.slcan_manager.is_connected:
            self.adapter_combo.addItem("SLCAN", ("slcan", None))
        
        # Add PCAN channels if connected
        if self.pcan_manager and self.pcan_manager.connected_channels:
            for channel in self.pcan_manager.get_connected_channels():
                channel_name = next((name for name, ch in self.pcan_manager.available_channels if ch == channel), f"PCAN-{channel:02X}")
                self.adapter_combo.addItem(f"PCAN: {channel_name}", ("pcan", channel))
        
        # Add option to send on all PCAN channels
        if self.pcan_manager and len(self.pcan_manager.connected_channels) > 1:
            self.adapter_combo.addItem("PCAN: All Channels", ("pcan", "all"))
        
        # If no adapters, add placeholder
        if self.adapter_combo.count() == 0:
            self.adapter_combo.addItem("No adapters connected", None)
        
        # Auto-select first available adapter
        if self.adapter_combo.count() > 0 and self.adapter_combo.itemData(0):
            self.adapter_combo.setCurrentIndex(0)
    
    def send_can_message(self, msg_id, data, extended=False, rtr=False):
        """Universal method to send CAN message via selected adapter"""
        if self.adapter_combo.currentData() is None:
            self.status_label.setText("No CAN adapter selected")
            return False
        
        adapter_type, channel = self.adapter_combo.currentData()
        
        if adapter_type == "pcan":
            if not self.pcan_manager:
                self.status_label.setText("PCAN manager not available")
                return False
            
            if channel == "all":
                # Send on all connected PCAN channels
                success_count = 0
                total_channels = len(self.pcan_manager.connected_channels)
                
                for ch in self.pcan_manager.get_connected_channels():
                    success, message = self.pcan_manager.send_message_on_channel(ch, msg_id, data, extended, rtr)
                    if success:
                        success_count += 1
                
                if success_count == total_channels:
                    self.status_label.setText(f"✓ Sent on all {total_channels} PCAN channels")
                    return True
                elif success_count > 0:
                    self.status_label.setText(f"⚠ Sent on {success_count}/{total_channels} PCAN channels")
                    return True
                else:
                    self.status_label.setText(f"✗ Failed to send on any PCAN channels")
                    return False
            else:
                # Send on specific PCAN channel
                success, message = self.pcan_manager.send_message_on_channel(channel, msg_id, data, extended, rtr)
                if success:
                    channel_name = next((name for name, ch in self.pcan_manager.available_channels if ch == channel), f"PCAN-{channel:02X}")
                    self.status_label.setText(f"✓ Sent via {channel_name}")
                    return True
                else:
                    self.status_label.setText(f"PCAN send failed: {message}")
                    return False
        
        elif adapter_type == "slcan":
            if not self.slcan_manager or not self.slcan_manager.is_connected:
                self.status_label.setText("SLCAN not connected")
                return False
            
            success = self.slcan_manager.send_message(msg_id, data, extended)
            if success:
                self.status_label.setText("✓ Sent via SLCAN")
                return True
            else:
                self.status_label.setText("SLCAN send failed")
                return False
        
        else:
            self.status_label.setText("Unknown adapter type")
            return False
    
    def closeEvent(self, event):
        """Clean up when closing"""
        self.stop_all_periodic()
        event.accept()
