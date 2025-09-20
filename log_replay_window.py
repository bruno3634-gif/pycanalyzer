# log_replay_window.py
import csv
import json
import time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QSlider, QSpinBox, QFileDialog, QMessageBox, QCheckBox,
    QProgressBar, QComboBox, QSplitter
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
import datetime


class LogReplayThread(QThread):
    message_sent = pyqtSignal(dict, str)  # message, status
    progress_update = pyqtSignal(int)  # current position
    replay_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.slcan_manager = None
        self.messages = []
        self.start_idx = 0
        self.end_idx = 0
        self.current_idx = 0
        self.delay_ms = 100
        self.is_running = False
        self.respect_timing = True
        
    def setup_replay(self, slcan_manager, messages, start_idx, end_idx, delay_ms, respect_timing):
        self.slcan_manager = slcan_manager
        self.messages = messages
        self.start_idx = start_idx
        self.end_idx = end_idx
        self.current_idx = start_idx
        self.delay_ms = delay_ms
        self.respect_timing = respect_timing
        
    def run(self):
        self.is_running = True
        last_timestamp = None
        
        for i in range(self.start_idx, min(self.end_idx + 1, len(self.messages))):
            if not self.is_running:
                break
                
            self.current_idx = i
            message = self.messages[i]
            
            # Calculate delay
            delay = self.delay_ms / 1000.0
            if self.respect_timing and last_timestamp is not None:
                try:
                    current_time = float(message.get('timestamp', 0))
                    time_diff = current_time - last_timestamp
                    if time_diff > 0:
                        delay = time_diff
                except (ValueError, TypeError):
                    pass
            
            # Send message
            if self.slcan_manager and self.slcan_manager.is_connected():
                try:
                    success = self.slcan_manager.send_message(
                        message['id'], 
                        message['data'], 
                        message.get('extended', False)
                    )
                    status = "Sent" if success else "Failed"
                except Exception as e:
                    status = f"Error: {str(e)}"
            else:
                status = "Not connected"
                
            self.message_sent.emit(message, status)
            self.progress_update.emit(i)
            
            if self.respect_timing and 'timestamp' in message:
                try:
                    last_timestamp = float(message['timestamp'])
                except (ValueError, TypeError):
                    pass
            
            # Wait for delay
            if delay > 0:
                self.msleep(int(delay * 1000))
                
        self.replay_finished.emit()
        
    def stop(self):
        self.is_running = False


class LogReplayWindow(QMainWindow):
    def __init__(self, slcan_manager):
        super().__init__()
        self.slcan_manager = slcan_manager
        self.messages = []
        self.current_position = 0
        self.start_position = 0
        self.end_position = 0
        self.replay_thread = LogReplayThread()
        
        self.setWindowTitle("CAN Log Replay")
        self.setGeometry(100, 100, 1200, 800)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # File selection section
        file_section = QHBoxLayout()
        layout.addLayout(file_section)
        
        self.load_btn = QPushButton("Load Log File")
        file_section.addWidget(self.load_btn)
        
        self.file_label = QLabel("No file loaded")
        file_section.addWidget(self.file_label)
        
        file_section.addStretch()
        
        self.file_format_combo = QComboBox()
        self.file_format_combo.addItems(["Auto-detect", "CSV", "JSON", "TRC", "ASC"])
        file_section.addWidget(QLabel("Format:"))
        file_section.addWidget(self.file_format_combo)
        
        # Message count info
        info_layout = QHBoxLayout()
        layout.addLayout(info_layout)
        
        self.msg_count_label = QLabel("Messages: 0")
        info_layout.addWidget(self.msg_count_label)
        
        self.duration_label = QLabel("Duration: 0s")
        info_layout.addWidget(self.duration_label)
        
        info_layout.addStretch()
        
        # Create splitter for table and controls
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Message table
        self.message_table = QTableWidget()
        self.message_table.setColumnCount(6)
        self.message_table.setHorizontalHeaderLabels(["#", "Timestamp", "ID", "DLC", "Data", "Dir"])
        self.message_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        splitter.addWidget(self.message_table)
        
        # Control panel
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        splitter.addWidget(control_widget)
        
        # Position controls
        pos_group = QVBoxLayout()
        control_layout.addLayout(pos_group)
        
        pos_group.addWidget(QLabel("Position Control:"))
        
        # Current position slider
        pos_layout = QHBoxLayout()
        pos_group.addLayout(pos_layout)
        
        pos_layout.addWidget(QLabel("Current:"))
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setMinimum(0)
        self.position_slider.setMaximum(0)
        pos_layout.addWidget(self.position_slider)
        
        self.position_spinbox = QSpinBox()
        self.position_spinbox.setMinimum(0)
        self.position_spinbox.setMaximum(0)
        pos_layout.addWidget(self.position_spinbox)
        
        # Start position
        start_layout = QHBoxLayout()
        pos_group.addLayout(start_layout)
        
        start_layout.addWidget(QLabel("Start:"))
        self.start_slider = QSlider(Qt.Orientation.Horizontal)
        self.start_slider.setMinimum(0)
        self.start_slider.setMaximum(0)
        start_layout.addWidget(self.start_slider)
        
        self.start_spinbox = QSpinBox()
        self.start_spinbox.setMinimum(0)
        self.start_spinbox.setMaximum(0)
        start_layout.addWidget(self.start_spinbox)
        
        # End position
        end_layout = QHBoxLayout()
        pos_group.addLayout(end_layout)
        
        end_layout.addWidget(QLabel("End:"))
        self.end_slider = QSlider(Qt.Orientation.Horizontal)
        self.end_slider.setMinimum(0)
        self.end_slider.setMaximum(0)
        end_layout.addWidget(self.end_slider)
        
        self.end_spinbox = QSpinBox()
        self.end_spinbox.setMinimum(0)
        self.end_spinbox.setMaximum(0)
        end_layout.addWidget(self.end_spinbox)
        
        # Replay controls
        replay_group = QVBoxLayout()
        control_layout.addLayout(replay_group)
        
        replay_group.addWidget(QLabel("Replay Control:"))
        
        # Single message controls
        single_layout = QHBoxLayout()
        replay_group.addLayout(single_layout)
        
        self.send_current_btn = QPushButton("Send Current Message")
        single_layout.addWidget(self.send_current_btn)
        
        self.next_send_btn = QPushButton("Select Next & Send")
        single_layout.addWidget(self.next_send_btn)
        
        # Replay controls
        replay_ctrl_layout = QHBoxLayout()
        replay_group.addLayout(replay_ctrl_layout)
        
        self.replay_btn = QPushButton("Replay Range")
        replay_ctrl_layout.addWidget(self.replay_btn)
        
        self.stop_btn = QPushButton("Stop Replay")
        self.stop_btn.setEnabled(False)
        replay_ctrl_layout.addWidget(self.stop_btn)
        
        # Replay options
        options_layout = QHBoxLayout()
        replay_group.addLayout(options_layout)
        
        options_layout.addWidget(QLabel("Delay (ms):"))
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setMinimum(1)
        self.delay_spinbox.setMaximum(10000)
        self.delay_spinbox.setValue(100)
        options_layout.addWidget(self.delay_spinbox)
        
        self.respect_timing_cb = QCheckBox("Respect Original Timing")
        self.respect_timing_cb.setChecked(True)
        options_layout.addWidget(self.respect_timing_cb)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        control_layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        control_layout.addWidget(self.status_label)
        
        # Set splitter proportions
        splitter.setSizes([500, 300])
        
    def setup_connections(self):
        self.load_btn.clicked.connect(self.load_log_file)
        self.send_current_btn.clicked.connect(self.send_current_message)
        self.next_send_btn.clicked.connect(self.next_and_send)
        self.replay_btn.clicked.connect(self.start_replay)
        self.stop_btn.clicked.connect(self.stop_replay)
        
        # Position controls
        self.position_slider.valueChanged.connect(self.on_position_changed)
        self.position_spinbox.valueChanged.connect(self.on_position_spinbox_changed)
        self.start_slider.valueChanged.connect(self.on_start_changed)
        self.start_spinbox.valueChanged.connect(self.on_start_spinbox_changed)
        self.end_slider.valueChanged.connect(self.on_end_changed)
        self.end_spinbox.valueChanged.connect(self.on_end_spinbox_changed)
        
        # Table selection
        self.message_table.selectionModel().selectionChanged.connect(self.on_table_selection_changed)
        
        # Replay thread connections
        self.replay_thread.message_sent.connect(self.on_message_sent)
        self.replay_thread.progress_update.connect(self.on_replay_progress)
        self.replay_thread.replay_finished.connect(self.on_replay_finished)
        
    def load_log_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load CAN Log File", "", 
            "All Files (*.*);;CSV Files (*.csv);;JSON Files (*.json);;TRC Files (*.trc);;ASC Files (*.asc)"
        )
        
        if file_path:
            try:
                self.messages = self.parse_log_file(file_path)
                self.update_ui_after_load(file_path)
                self.status_label.setText(f"Loaded {len(self.messages)} messages from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load log file:\n{str(e)}")
                
    def parse_log_file(self, file_path):
        """Parse different log file formats"""
        messages = []
        file_format = self.file_format_combo.currentText()
        
        # Auto-detect format based on extension
        if file_format == "Auto-detect":
            ext = file_path.lower().split('.')[-1]
            if ext == 'csv':
                file_format = "CSV"
            elif ext == 'json':
                file_format = "JSON"
            elif ext == 'trc':
                file_format = "TRC"
            elif ext == 'asc':
                file_format = "ASC"
            else:
                file_format = "CSV"  # Default
                
        if file_format == "JSON":
            messages = self.parse_json_log(file_path)
        elif file_format == "TRC":
            messages = self.parse_trc_log(file_path)
        elif file_format == "ASC":
            messages = self.parse_asc_log(file_path)
        else:  # CSV
            messages = self.parse_csv_log(file_path)
            
        return messages
        
    def parse_csv_log(self, file_path):
        """Parse CSV log file with columns: timestamp,id,dlc,data,direction"""
        messages = []
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    message = {
                        'timestamp': float(row.get('timestamp', 0)),
                        'id': int(row['id'], 16) if isinstance(row['id'], str) else int(row['id']),
                        'dlc': int(row.get('dlc', len(row['data'].split()))),
                        'data': row['data'],
                        'direction': row.get('direction', 'Tx'),
                        'extended': len(hex(int(row['id'], 16) if isinstance(row['id'], str) else int(row['id']))) > 5
                    }
                    messages.append(message)
                except (ValueError, KeyError) as e:
                    print(f"Skipping invalid row: {row}, error: {e}")
        return messages
        
    def parse_json_log(self, file_path):
        """Parse JSON log file"""
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'messages' in data:
                return data['messages']
            else:
                raise ValueError("Invalid JSON format")
                
    def parse_trc_log(self, file_path):
        """Parse TRC log file format"""
        messages = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith(';'):
                    continue
                    
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        timestamp = float(parts[0])
                        direction = parts[1]  # Rx/Tx
                        can_id = int(parts[2], 16)
                        dlc = int(parts[3])
                        data = ' '.join(parts[4:4+dlc]) if len(parts) > 4 else ''
                        
                        message = {
                            'timestamp': timestamp,
                            'id': can_id,
                            'dlc': dlc,
                            'data': data,
                            'direction': direction,
                            'extended': can_id > 0x7FF
                        }
                        messages.append(message)
                except (ValueError, IndexError) as e:
                    print(f"Skipping invalid TRC line: {line}, error: {e}")
                    
        return messages
        
    def parse_asc_log(self, file_path):
        """Parse ASC log file format"""
        messages = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('date') or line.startswith('base'):
                    continue
                    
                try:
                    if ' CAN ' in line:
                        parts = line.split()
                        timestamp = float(parts[0])
                        can_id = int(parts[2], 16)
                        direction = parts[3]  # Rx/Tx
                        dlc = int(parts[4])
                        data = ' '.join(parts[5:5+dlc]) if len(parts) > 5 else ''
                        
                        message = {
                            'timestamp': timestamp,
                            'id': can_id,
                            'dlc': dlc,
                            'data': data,
                            'direction': direction,
                            'extended': can_id > 0x7FF
                        }
                        messages.append(message)
                except (ValueError, IndexError) as e:
                    print(f"Skipping invalid ASC line: {line}, error: {e}")
                    
        return messages
        
    def update_ui_after_load(self, file_path):
        """Update UI elements after loading a log file"""
        self.file_label.setText(f"File: {file_path.split('/')[-1]}")
        
        if not self.messages:
            return
            
        # Update message count
        self.msg_count_label.setText(f"Messages: {len(self.messages)}")
        
        # Calculate duration
        if len(self.messages) > 1:
            try:
                start_time = self.messages[0].get('timestamp', 0)
                end_time = self.messages[-1].get('timestamp', 0)
                duration = end_time - start_time
                self.duration_label.setText(f"Duration: {duration:.2f}s")
            except (TypeError, ValueError):
                self.duration_label.setText("Duration: Unknown")
        else:
            self.duration_label.setText("Duration: 0s")
            
        # Update sliders and spinboxes
        max_idx = len(self.messages) - 1
        
        self.position_slider.setMaximum(max_idx)
        self.position_spinbox.setMaximum(max_idx)
        self.start_slider.setMaximum(max_idx)
        self.start_spinbox.setMaximum(max_idx)
        self.end_slider.setMaximum(max_idx)
        self.end_spinbox.setMaximum(max_idx)
        
        # Set initial values
        self.position_slider.setValue(0)
        self.start_slider.setValue(0)
        self.end_slider.setValue(max_idx)
        
        self.current_position = 0
        self.start_position = 0
        self.end_position = max_idx
        
        # Update table
        self.update_message_table()
        
        # Update progress bar
        self.progress_bar.setMaximum(max_idx)
        self.progress_bar.setValue(0)
        
    def update_message_table(self):
        """Update the message table with loaded messages"""
        self.message_table.setRowCount(len(self.messages))
        
        for i, msg in enumerate(self.messages):
            self.message_table.setItem(i, 0, QTableWidgetItem(str(i)))
            self.message_table.setItem(i, 1, QTableWidgetItem(str(msg.get('timestamp', 'N/A'))))
            self.message_table.setItem(i, 2, QTableWidgetItem(f"0x{msg['id']:X}"))
            self.message_table.setItem(i, 3, QTableWidgetItem(str(msg.get('dlc', 0))))
            self.message_table.setItem(i, 4, QTableWidgetItem(str(msg.get('data', ''))))
            self.message_table.setItem(i, 5, QTableWidgetItem(str(msg.get('direction', 'Tx'))))
            
        # Highlight current position
        self.highlight_current_position()
        
    def highlight_current_position(self):
        """Highlight the current position in the table"""
        self.message_table.clearSelection()
        if 0 <= self.current_position < len(self.messages):
            self.message_table.selectRow(self.current_position)
            self.message_table.scrollToItem(self.message_table.item(self.current_position, 0))
            
    def on_position_changed(self, value):
        self.current_position = value
        self.position_spinbox.setValue(value)
        self.highlight_current_position()
        
    def on_position_spinbox_changed(self, value):
        self.current_position = value
        self.position_slider.setValue(value)
        self.highlight_current_position()
        
    def on_start_changed(self, value):
        self.start_position = value
        self.start_spinbox.setValue(value)
        if value > self.end_position:
            self.end_slider.setValue(value)
            
    def on_start_spinbox_changed(self, value):
        self.start_position = value
        self.start_slider.setValue(value)
        if value > self.end_position:
            self.end_slider.setValue(value)
            
    def on_end_changed(self, value):
        self.end_position = value
        self.end_spinbox.setValue(value)
        if value < self.start_position:
            self.start_slider.setValue(value)
            
    def on_end_spinbox_changed(self, value):
        self.end_position = value
        self.end_slider.setValue(value)
        if value < self.start_position:
            self.start_slider.setValue(value)
            
    def on_table_selection_changed(self):
        """Update position when table selection changes"""
        selected_rows = self.message_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            self.position_slider.setValue(row)
            
    def send_current_message(self):
        """Send the currently selected message"""
        if not self.messages or not (0 <= self.current_position < len(self.messages)):
            self.status_label.setText("No valid message selected")
            return
            
        if not self.slcan_manager or not self.slcan_manager.is_connected():
            self.status_label.setText("SLCAN not connected")
            return
            
        message = self.messages[self.current_position]
        try:
            success = self.slcan_manager.send_message(
                message['id'], 
                message['data'], 
                message.get('extended', False)
            )
            
            if success:
                self.status_label.setText(f"Sent message {self.current_position}: 0x{message['id']:X}")
            else:
                self.status_label.setText(f"Failed to send message {self.current_position}")
                
        except Exception as e:
            self.status_label.setText(f"Error sending message: {str(e)}")
            
    def next_and_send(self):
        """Move to next message and send it"""
        if self.current_position < len(self.messages) - 1:
            self.position_slider.setValue(self.current_position + 1)
            self.send_current_message()
        else:
            self.status_label.setText("Already at last message")
            
    def start_replay(self):
        """Start replaying messages in the selected range"""
        if not self.messages:
            self.status_label.setText("No messages loaded")
            return
            
        if not self.slcan_manager or not self.slcan_manager.is_connected():
            self.status_label.setText("SLCAN not connected")
            return
            
        if self.replay_thread.isRunning():
            self.status_label.setText("Replay already running")
            return
            
        # Setup replay parameters
        self.replay_thread.setup_replay(
            self.slcan_manager,
            self.messages,
            self.start_position,
            self.end_position,
            self.delay_spinbox.value(),
            self.respect_timing_cb.isChecked()
        )
        
        # Update UI
        self.replay_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress_bar.setRange(self.start_position, self.end_position)
        self.status_label.setText(f"Replaying messages {self.start_position} to {self.end_position}")
        
        # Start replay
        self.replay_thread.start()
        
    def stop_replay(self):
        """Stop the current replay"""
        if self.replay_thread.isRunning():
            self.replay_thread.stop()
            self.replay_thread.wait()
            
        self.on_replay_finished()
        
    def on_message_sent(self, message, status):
        """Handle message sent from replay thread"""
        self.status_label.setText(f"Sent 0x{message['id']:X} - {status}")
        
    def on_replay_progress(self, position):
        """Update progress during replay"""
        self.progress_bar.setValue(position)
        self.position_slider.setValue(position)
        
    def on_replay_finished(self):
        """Handle replay completion"""
        self.replay_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Replay finished")
        
    def closeEvent(self, event):
        """Handle window close event"""
        if self.replay_thread.isRunning():
            self.replay_thread.stop()
            self.replay_thread.wait()
        event.accept()
