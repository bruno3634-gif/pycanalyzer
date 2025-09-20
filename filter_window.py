# filter_window.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QLineEdit, QGroupBox, QHeaderView, QCheckBox, QComboBox,
    QMessageBox, QListWidget, QListWidgetItem, QAbstractItemView, QInputDialog
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt
import datetime
import json


class FilterWindow(QMainWindow):
    def __init__(self, main_window, filter_type="include"):
        super().__init__()
        self.main_window = main_window
        self.filter_type = filter_type  # "include" or "exclude"
        self.filtered_ids = set()
        self.received_messages = {}
        
        # Display format options (same as main window)
        self.id_display_format = "Hex"
        self.raw_display_format = "Hex"
        self.time_mode = "Absolute"
        
        # Timestamp tracking for incremental/differential modes
        self.last_timestamp_global = None
        self.last_timestamp_by_id = {}
        
        self.setWindowTitle(f"CAN Message Filter - {'Include Only' if filter_type == 'include' else 'Exclude'}")
        self.resize(1200, 700)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)
        
        # Filter controls
        self.setup_filter_controls(layout)
        
        # Display options (same as main window)
        self.setup_display_controls(layout)
        
        # Message table
        self.setup_message_table(layout)
        
        # Timer for updating messages
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_filtered_messages)
        self.timer.start(100)  # Update more frequently for responsiveness
        
    def setup_filter_controls(self, layout):
        """Setup the filter control interface"""
        filter_group = QGroupBox(f"Filter Settings - {'Include Only' if self.filter_type == 'include' else 'Exclude'}")
        filter_layout = QVBoxLayout()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Filter type explanation
        explanation = QLabel()
        if self.filter_type == "include":
            explanation.setText("🎯 Include Mode: Only show messages with IDs in the list below")
        else:
            explanation.setText("🚫 Exclude Mode: Hide messages with IDs in the list below")
        filter_layout.addWidget(explanation)
        
        # ID input and controls
        input_layout = QHBoxLayout()
        filter_layout.addLayout(input_layout)
        
        input_layout.addWidget(QLabel("CAN ID:"))
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter ID (e.g., 0x100, 256, 100)")
        self.id_input.returnPressed.connect(self.add_filter_id)
        input_layout.addWidget(self.id_input)
        
        add_btn = QPushButton("Add ID")
        add_btn.clicked.connect(self.add_filter_id)
        input_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self.remove_selected_id)
        input_layout.addWidget(remove_btn)
        
        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.clear_all_ids)
        input_layout.addWidget(clear_btn)
        
        # Auto-detect controls
        auto_layout = QHBoxLayout()
        filter_layout.addLayout(auto_layout)
        
        auto_add_btn = QPushButton("Auto-Add Active IDs")
        auto_add_btn.clicked.connect(self.auto_add_active_ids)
        auto_add_btn.setToolTip("Add all currently active message IDs from main window")
        auto_layout.addWidget(auto_add_btn)
        
        # Filter list
        list_layout = QHBoxLayout()
        filter_layout.addLayout(list_layout)
        
        list_layout.addWidget(QLabel("Filtered IDs:"))
        self.filter_list = QListWidget()
        self.filter_list.setMaximumHeight(100)
        self.filter_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        list_layout.addWidget(self.filter_list)
        
        # Status
        self.status_label = QLabel("Status: No filters active")
        filter_layout.addWidget(self.status_label)
        
    def setup_display_controls(self, layout):
        """Setup display format controls (same as main window)"""
        display_group = QGroupBox("Display Options")
        display_layout = QHBoxLayout()
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Time Mode
        display_layout.addWidget(QLabel("Time Mode:"))
        self.time_mode_combo = QComboBox()
        self.time_mode_combo.addItems(["Absolute", "Incremental", "Differential"])
        self.time_mode_combo.currentIndexChanged.connect(self.update_all_timestamps)
        display_layout.addWidget(self.time_mode_combo)
        
        # ID Format
        display_layout.addWidget(QLabel("ID Format:"))
        self.id_format_combo = QComboBox()
        self.id_format_combo.addItems(["Hex", "Decimal"])
        self.id_format_combo.currentIndexChanged.connect(self.update_all_ids)
        display_layout.addWidget(self.id_format_combo)
        
        # Raw Data Format
        display_layout.addWidget(QLabel("Data Format:"))
        self.data_format_combo = QComboBox()
        self.data_format_combo.addItems(["Hex", "Decimal", "Octal", "ASCII"])
        self.data_format_combo.currentIndexChanged.connect(self.update_all_raw_data)
        display_layout.addWidget(self.data_format_combo)
        
    def setup_message_table(self, layout):
        """Setup the filtered message table"""
        # Table controls
        table_controls = QHBoxLayout()
        layout.addLayout(table_controls)
        
        table_controls.addWidget(QLabel("Filtered Messages:"))
        
        self.autoscroll_enabled = True
        self.autoscroll_btn = QPushButton("Autoscroll")
        self.autoscroll_btn.setCheckable(True)
        self.autoscroll_btn.setChecked(True)
        self.autoscroll_btn.clicked.connect(self.toggle_autoscroll)
        table_controls.addWidget(self.autoscroll_btn)
        
        clear_table_btn = QPushButton("Clear Table")
        clear_table_btn.clicked.connect(self.clear_table)
        table_controls.addWidget(clear_table_btn)
        
        # Message table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "DLC", "Raw Data", "Decoded Signals", "Timestamp"])
        layout.addWidget(self.table)
        
        # Enable header clicking for format changes (same as main window)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
        
        # Auto-resize columns
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
    def add_filter_id(self):
        """Add a CAN ID to the filter list"""
        id_text = self.id_input.text().strip()
        if not id_text:
            return
            
        try:
            # Parse various formats (0x100, 256, 100)
            if id_text.startswith('0x') or id_text.startswith('0X'):
                can_id = int(id_text, 16)
            else:
                can_id = int(id_text)
                
            if can_id < 0 or can_id > 0x1FFFFFFF:
                QMessageBox.warning(self, "Invalid ID", "CAN ID must be between 0 and 0x1FFFFFFF")
                return
                
            if can_id not in self.filtered_ids:
                self.filtered_ids.add(can_id)
                self.update_filter_list()
                self.update_status()
                
            self.id_input.clear()
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Format", "Please enter a valid CAN ID (e.g., 0x100, 256)")
            
    def remove_selected_id(self):
        """Remove selected IDs from the filter list"""
        selected_items = self.filter_list.selectedItems()
        for item in selected_items:
            id_text = item.text().split()[0]  # Get ID part before description
            try:
                if id_text.startswith('0x'):
                    can_id = int(id_text, 16)
                else:
                    can_id = int(id_text)
                self.filtered_ids.discard(can_id)
            except ValueError:
                continue
                
        self.update_filter_list()
        self.update_status()
        
    def clear_all_ids(self):
        """Clear all filter IDs"""
        self.filtered_ids.clear()
        self.update_filter_list()
        self.update_status()
        
    def auto_add_active_ids(self):
        """Add all currently active IDs from the main window"""
        added_count = 0
        
        # Get IDs from main window table
        for row in range(self.main_window.table.rowCount()):
            id_item = self.main_window.table.item(row, 0)
            if id_item:
                can_id = id_item.data(Qt.ItemDataRole.UserRole)
                if can_id is not None and can_id not in self.filtered_ids:
                    self.filtered_ids.add(can_id)
                    added_count += 1
                    
        # Get IDs from received messages
        for can_id in self.main_window.received_messages.keys():
            if can_id not in self.filtered_ids:
                self.filtered_ids.add(can_id)
                added_count += 1
                
        self.update_filter_list()
        self.update_status()
        
        if added_count > 0:
            QMessageBox.information(self, "Auto-Add Complete", f"Added {added_count} active IDs to filter")
        else:
            QMessageBox.information(self, "Auto-Add Complete", "No new IDs found to add")
            
    def update_filter_list(self):
        """Update the visual filter list"""
        self.filter_list.clear()
        
        for can_id in sorted(self.filtered_ids):
            # Add description if available from main window
            description = ""
            if hasattr(self.main_window, 'dbc_manager') and self.main_window.dbc_manager.db:
                try:
                    message = self.main_window.dbc_manager.db.get_message_by_id(can_id)
                    description = f" - {message.name}"
                except:
                    pass
                    
            item_text = f"0x{can_id:X} ({can_id}){description}"
            self.filter_list.addItem(item_text)
            
    def update_status(self):
        """Update the status label"""
        count = len(self.filtered_ids)
        if count == 0:
            self.status_label.setText("Status: No filters active")
        else:
            action = "included" if self.filter_type == "include" else "excluded"
            self.status_label.setText(f"Status: {count} IDs {action}")
            
    def toggle_autoscroll(self):
        """Toggle autoscroll functionality"""
        self.autoscroll_enabled = self.autoscroll_btn.isChecked()
        
    def clear_table(self):
        """Clear the message table"""
        self.table.setRowCount(0)
        self.received_messages.clear()
        
    def should_show_message(self, can_id):
        """Determine if a message should be shown based on filter type and IDs"""
        if len(self.filtered_ids) == 0:
            return True  # No filters = show all
            
        if self.filter_type == "include":
            return can_id in self.filtered_ids
        else:  # exclude
            return can_id not in self.filtered_ids
            
    def update_filtered_messages(self):
        """Update the filtered message table with new messages"""
        # Get messages from main window
        new_messages = {}
        
        # From test messages/simulated data
        if hasattr(self.main_window, 'messages_by_id'):
            for can_id, msg in self.main_window.messages_by_id.items():
                if self.should_show_message(can_id):
                    new_messages[can_id] = msg
                    
        # From received messages
        for can_id, msg in self.main_window.received_messages.items():
            if self.should_show_message(can_id):
                new_messages[can_id] = msg
                
        # Update our local copy and table
        messages_changed = False
        for can_id, msg in new_messages.items():
            if can_id not in self.received_messages or self.received_messages[can_id] != msg:
                self.received_messages[can_id] = msg
                messages_changed = True
                
        if messages_changed:
            self.refresh_table()
            
    def refresh_table(self):
        """Refresh the entire table with current filtered messages"""
        # Sort messages by ID for consistent display
        sorted_messages = sorted(self.received_messages.items())
        
        self.table.setRowCount(len(sorted_messages))
        
        for row, (can_id, msg) in enumerate(sorted_messages):
            # ID
            id_text = f"0x{can_id:X}" if self.id_display_format == "Hex" else str(can_id)
            id_item = QTableWidgetItem(id_text)
            id_item.setData(Qt.ItemDataRole.UserRole, can_id)
            self.table.setItem(row, 0, id_item)
            
            # Type
            msg_type = msg.get("type", "STD")
            self.table.setItem(row, 1, QTableWidgetItem(msg_type))
            
            # DLC
            data = msg.get("data", [])
            self.table.setItem(row, 2, QTableWidgetItem(str(len(data))))
            
            # Raw Data
            raw_item = QTableWidgetItem()
            raw_item.setData(Qt.ItemDataRole.UserRole, data)
            raw_item.setText(self.format_data(data, self.raw_display_format))
            self.table.setItem(row, 3, raw_item)
            
            # Decoded Signals
            decoded = msg.get("decoded", {})
            decoded_str = json.dumps(decoded) if decoded else ""
            self.table.setItem(row, 4, QTableWidgetItem(decoded_str))
            
            # Timestamp - use the timestamp update method for proper formatting
            self.update_timestamp_for_row(row, msg)
            
        if self.autoscroll_enabled:
            self.table.scrollToBottom()
    
    def format_data(self, data, fmt):
        """Format data based on selected format (same as main window)"""
        if fmt == "Decimal": 
            return " ".join(str(b) for b in data)
        elif fmt == "Hex": 
            return " ".join(f"{b:02X}" for b in data)
        elif fmt == "Octal": 
            return " ".join(oct(b)[2:] for b in data)
        elif fmt == "ASCII": 
            return "".join(chr(b) if 32 <= b <= 126 else "." for b in data)
        return str(data)
    
    def on_header_clicked(self, index):
        """Handle header clicks for format changes (same as main window)"""
        if index == 3:  # Raw Data
            fmt_list = ["Decimal", "Hex", "Octal", "ASCII"]
            current_index = fmt_list.index(self.raw_display_format) if self.raw_display_format in fmt_list else 0
            fmt, ok = QInputDialog.getItem(self, "Select Column Format",
                "Choose data format for Raw Data column:", fmt_list, current=current_index, editable=False)
            if ok and fmt: 
                self.raw_display_format = fmt
                self.data_format_combo.setCurrentText(fmt)
                self.update_all_raw_data()
        elif index == 0:  # ID
            fmt_list = ["Hex", "Decimal"]
            current_index = fmt_list.index(self.id_display_format) if self.id_display_format in fmt_list else 0
            fmt, ok = QInputDialog.getItem(self, "Select Column Format",
                "Choose format for ID column:", fmt_list, current=current_index, editable=False)
            if ok and fmt: 
                self.id_display_format = fmt
                self.id_format_combo.setCurrentText(fmt)
                self.update_all_ids()
    
    def set_table_item(self, row, column, text):
        """Set table item text (same as main window)"""
        item = self.table.item(row, column)
        if not item:
            item = QTableWidgetItem()
            self.table.setItem(row, column, item)
        item.setText(text)
    
    def update_all_ids(self):
        """Update all ID column formats"""
        self.id_display_format = self.id_format_combo.currentText()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                value = item.data(Qt.ItemDataRole.UserRole)
                if value is not None:
                    item.setText(f"0x{value:X}" if self.id_display_format == "Hex" else str(value))
    
    def update_all_raw_data(self):
        """Update all raw data column formats"""
        self.raw_display_format = self.data_format_combo.currentText()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item:
                data = item.data(Qt.ItemDataRole.UserRole)
                if data:
                    item.setText(self.format_data(data, self.raw_display_format))
    
    def update_all_timestamps(self):
        """Update all timestamps when time mode changes"""
        self.time_mode = self.time_mode_combo.currentText()
        self.last_timestamp_global = None
        self.last_timestamp_by_id = {}
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item:
                msg_id = id_item.data(Qt.ItemDataRole.UserRole)
                if msg_id in self.received_messages:
                    msg = self.received_messages[msg_id]
                    self.update_timestamp_for_row(row, msg)
    
    def update_timestamp_for_row(self, row, msg):
        """Update timestamp for a specific row (same logic as main window)"""
        raw_time = msg["timestamp"]
        ts_text = ""
        if self.time_mode == "Absolute": 
            ts_text = raw_time.strftime("%H:%M:%S.%f")[:-3]
        elif self.time_mode == "Incremental":
            delta = 0.0 if self.last_timestamp_global is None else (raw_time - self.last_timestamp_global).total_seconds()
            ts_text = f"{delta:.3f}s"
            self.last_timestamp_global = raw_time
        elif self.time_mode == "Differential":
            last = self.last_timestamp_by_id.get(msg["id"])
            delta = 0.0 if last is None else (raw_time - last).total_seconds()
            ts_text = f"{delta:.3f}s"
            self.last_timestamp_by_id[msg["id"]] = raw_time
        self.set_table_item(row, 5, ts_text)
            
    def closeEvent(self, event):
        """Clean up when closing the filter window"""
        if self.timer:
            self.timer.stop()
        event.accept()
