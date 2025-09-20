# gui.py
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QMenu, QFileDialog, QDialog, QPushButton, QInputDialog, QComboBox,
    QMessageBox, QSpinBox, QCheckBox, QLineEdit
)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import QTimer, Qt
from message_processor import MessageProcessor
from dbc_manager import DBCManager
from slcan_manager import SLCANManager
import random, datetime, json

class SLCANConnectionDialog(QDialog):
    def __init__(self, slcan_manager):
        super().__init__()
        self.setWindowTitle("SLCAN Connection")
        self.resize(400, 300)
        self.slcan_manager = slcan_manager
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Port selection
        port_layout = QHBoxLayout()
        layout.addLayout(port_layout)
        port_layout.addWidget(QLabel("Serial Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        
        test_btn = QPushButton("Test")
        test_btn.clicked.connect(self.test_connection)
        port_layout.addWidget(test_btn)
        
        # Baudrate selection
        baud_layout = QHBoxLayout()
        layout.addLayout(baud_layout)
        baud_layout.addWidget(QLabel("Baudrate:"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")
        baud_layout.addWidget(self.baud_combo)
        
        # CAN Bitrate selection
        can_baud_layout = QHBoxLayout()
        layout.addLayout(can_baud_layout)
        can_baud_layout.addWidget(QLabel("CAN Bitrate:"))
        self.can_baud_combo = QComboBox()
        self.can_baud_combo.addItems([
            "10000", "20000", "50000", "100000", 
            "125000", "250000", "500000", "800000", "1000000"
        ])
        self.can_baud_combo.setCurrentText("500000")
        can_baud_layout.addWidget(self.can_baud_combo)
        
        # Loopback mode checkbox
        self.loopback_cb = QCheckBox("Enable Loopback Mode")
        self.loopback_cb.setToolTip("Receive your own transmitted messages (useful for testing)")
        layout.addWidget(self.loopback_cb)
        
        # Connect button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.connect_device)
        layout.addWidget(self.connect_btn)
        
        # Disconnect button
        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        layout.addWidget(self.disconnect_btn)
        
        # Status label
        self.status_label = QLabel("Status: Disconnected")
        layout.addWidget(self.status_label)
        
        # Device info button
        self.device_info_btn = QPushButton("Check Device Info")
        self.device_info_btn.clicked.connect(self.check_device_info)
        self.device_info_btn.setEnabled(False)
        layout.addWidget(self.device_info_btn)
        
        # Send message section
        layout.addWidget(QLabel("Send CAN Message:"))
        
        msg_layout = QHBoxLayout()
        layout.addLayout(msg_layout)
        msg_layout.addWidget(QLabel("ID:"))
        self.msg_id_input = QSpinBox()
        self.msg_id_input.setMinimum(0)
        self.msg_id_input.setMaximum(0x7FF)
        self.msg_id_input.setDisplayIntegerBase(16)
        self.msg_id_input.setValue(0x100)
        msg_layout.addWidget(self.msg_id_input)
        
        self.extended_cb = QCheckBox("Extended")
        msg_layout.addWidget(self.extended_cb)
        
        data_layout = QHBoxLayout()
        layout.addLayout(data_layout)
        data_layout.addWidget(QLabel("Data (hex):"))
        self.data_input = QLineEdit("00 01 02 03 04 05 06 07")
        data_layout.addWidget(self.data_input)
        
        send_btn = QPushButton("Send Message")
        send_btn.clicked.connect(self.send_message)
        layout.addWidget(send_btn)
    
    def refresh_ports(self):
        self.port_combo.clear()
        ports = self.slcan_manager.list_serial_ports()
        self.port_combo.addItems(ports)
    
    def test_connection(self):
        port = self.port_combo.currentText()
        baudrate = int(self.baud_combo.currentText())
        
        if not port:
            QMessageBox.warning(self, "Error", "Please select a serial port")
            return
        
        self.status_label.setText("Testing connection...")
        if self.slcan_manager.test_connection(port, baudrate):
            QMessageBox.information(self, "Test Result", f"Device found on {port} at {baudrate} baud!")
            self.status_label.setText("Test successful - device responds")
        else:
            QMessageBox.warning(self, "Test Result", f"No SLCAN device found on {port} at {baudrate} baud")
            self.status_label.setText("Test failed - no response")
    
    def connect_device(self):
        port = self.port_combo.currentText()
        baudrate = int(self.baud_combo.currentText())
        loopback = self.loopback_cb.isChecked()
        
        if not port:
            QMessageBox.warning(self, "Error", "Please select a serial port")
            return
        
        self.status_label.setText("Connecting...")
        
        if self.slcan_manager.connect(port, baudrate, loopback):
            can_bitrate = int(self.can_baud_combo.currentText())
            if self.slcan_manager.set_bitrate(can_bitrate, loopback):
                loopback_text = " (Loopback ON)" if loopback else ""
                self.status_label.setText(f"Connected to {port} at {baudrate} baud, CAN: {can_bitrate}bps{loopback_text}")
                self.connect_btn.setEnabled(False)
                self.disconnect_btn.setEnabled(True)
                self.device_info_btn.setEnabled(True)
                QMessageBox.information(self, "Success", f"Connected to SLCAN device successfully!{loopback_text}")
            else:
                self.status_label.setText("Failed to set CAN bitrate")
                QMessageBox.warning(self, "Error", "Connected but failed to set CAN bitrate")
                self.slcan_manager.disconnect()
        else:
            self.status_label.setText("Connection failed")
            QMessageBox.warning(self, "Error", f"Failed to connect to SLCAN device on {port}.\n\nTry:\n1. Check if device is plugged in\n2. Test connection first\n3. Try different baud rates\n4. Check if another program is using the port")
    
    def disconnect_device(self):
        self.slcan_manager.disconnect()
        self.status_label.setText("Status: Disconnected")
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.device_info_btn.setEnabled(False)
    
    def check_device_info(self):
        if not self.slcan_manager.is_connected:
            QMessageBox.warning(self, "Error", "Not connected to SLCAN device")
            return
        
        info = self.slcan_manager.check_device_info()
        if info:
            msg = f"Device Information:\n\nVersion: {repr(info['version'])}\nSerial: {repr(info['serial'])}"
            QMessageBox.information(self, "Device Info", msg)
        else:
            QMessageBox.warning(self, "Error", "Failed to get device information")
    
    def send_message(self):
        if not self.slcan_manager.is_connected:
            QMessageBox.warning(self, "Error", "Not connected to SLCAN device")
            return
        
        try:
            msg_id = self.msg_id_input.value()
            extended = self.extended_cb.isChecked()
            
            # Parse data string
            data_str = self.data_input.text().strip()
            data = []
            if data_str:
                hex_bytes = data_str.replace(" ", "").replace(",", "")
                for i in range(0, len(hex_bytes), 2):
                    if i + 1 < len(hex_bytes):
                        data.append(int(hex_bytes[i:i+2], 16))
            
            print(f"Attempting to send: ID=0x{msg_id:X}, Data={data}, Extended={extended}")
            
            if self.slcan_manager.send_message(msg_id, data, extended):
                self.status_label.setText(f"✓ Message sent: ID=0x{msg_id:X}, Data={data}")
                QMessageBox.information(self, "Success", f"Message sent successfully!\nID: 0x{msg_id:X}\nData: {data}")
            else:
                self.status_label.setText(f"✗ Failed to send: ID=0x{msg_id:X}")
                QMessageBox.warning(self, "Error", f"Failed to send message.\n\nThis could mean:\n1. Device doesn't support message transmission\n2. Wrong SLCAN format\n3. Device is not properly connected to CAN bus\n4. Loopback mode may be required for testing")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error sending message: {e}")

class ConversionDialog(QDialog):
    def __init__(self, dbc_manager):
        super().__init__()
        self.setWindowTitle("DBC ↔ Symb Conversion")
        self.resize(400, 200)
        self.dbc_manager = dbc_manager
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.load_dbc_btn = QPushButton("Load DBC and Convert to Symb (JSON)")
        self.load_dbc_btn.clicked.connect(self.convert_dbc_to_symb)
        layout.addWidget(self.load_dbc_btn)

        self.load_symb_btn = QPushButton("Load Symb and Convert to DBC")
        self.load_symb_btn.clicked.connect(self.convert_symb_to_dbc)
        layout.addWidget(self.load_symb_btn)

    def convert_dbc_to_symb(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open DBC", "", "DBC Files (*.dbc)")
        if file_name:
            self.dbc_manager.load_dbc(file_name)
            symb_file, _ = QFileDialog.getSaveFileName(self, "Save Symb File", "", "JSON Files (*.json)")
            if symb_file:
                self.dbc_manager.dbc_to_symb(symb_file)

    def convert_symb_to_dbc(self):
        symb_file, _ = QFileDialog.getOpenFileName(self, "Open Symb File", "", "JSON Files (*.json)")
        if symb_file:
            dbc_file, _ = QFileDialog.getSaveFileName(self, "Save DBC File", "", "DBC Files (*.dbc)")
            if dbc_file:
                self.dbc_manager.symb_to_dbc(symb_file, dbc_file)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PCAN Custom GUI")
        self.resize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout()
        central.setLayout(self.layout)

        # Menu Bar
        self.menu_bar = self.menuBar()
        self.hardware_menu = QMenu("Hardware", self)
        self.menu_bar.addMenu(self.hardware_menu)
        self.select_channel_action = QAction("Select Channel", self)
        self.select_channel_action.triggered.connect(self.select_channel)
        self.hardware_menu.addAction(self.select_channel_action)
        self.select_bitrate_action = QAction("Select Bitrate", self)
        self.select_bitrate_action.triggered.connect(self.select_bitrate)
        self.hardware_menu.addAction(self.select_bitrate_action)
        
        # Add SLCAN menu item
        self.slcan_action = QAction("SLCAN Connection", self)
        self.slcan_action.triggered.connect(self.open_slcan_dialog)
        self.hardware_menu.addAction(self.slcan_action)

        self.dbc_menu = QMenu("DBC", self)
        self.menu_bar.addMenu(self.dbc_menu)
        self.load_dbc_action = QAction("Load DBC", self)
        self.load_dbc_action.triggered.connect(self.load_dbc)
        self.dbc_menu.addAction(self.load_dbc_action)

        self.conv_menu = QMenu("Conversions", self)
        self.menu_bar.addMenu(self.conv_menu)
        self.open_conv_action = QAction("Open Conversion Dialog", self)
        self.open_conv_action.triggered.connect(self.open_conversion_dialog)
        self.conv_menu.addAction(self.open_conv_action)

        self.log_menu = QMenu("Logging", self)
        self.menu_bar.addMenu(self.log_menu)
        self.start_log_action = QAction("Start Log (.trc)", self)
        self.start_log_action.triggered.connect(self.start_log)
        self.log_menu.addAction(self.start_log_action)
        self.stop_log_action = QAction("Stop Log", self)
        self.stop_log_action.triggered.connect(self.stop_log)
        self.log_menu.addAction(self.stop_log_action)

        # Status layout
        self.status_layout = QHBoxLayout()
        self.label_status = QLabel("Status: Disconnected")
        self.status_layout.addWidget(self.label_status)

        self.autoscroll_enabled = True
        self.autoscroll_btn = QPushButton("Autoscroll")
        self.autoscroll_btn.setCheckable(True)
        self.autoscroll_btn.setChecked(True)
        self.autoscroll_btn.clicked.connect(self.toggle_autoscroll)
        self.status_layout.addWidget(self.autoscroll_btn)
        self.layout.addLayout(self.status_layout)

        # Controls layout (Time Mode)
        controls_layout = QHBoxLayout()
        self.layout.addLayout(controls_layout)
        controls_layout.addWidget(QLabel("Time Mode:"))
        self.time_mode_combo = QComboBox()
        self.time_mode_combo.addItems(["Absolute","Incremental","Differential"])
        self.time_mode_combo.currentIndexChanged.connect(self.update_all_timestamps)
        controls_layout.addWidget(self.time_mode_combo)
        self.time_mode = "Absolute"

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Type", "DLC", "Raw Data", "Decoded Signals", "Timestamp"])
        self.layout.addWidget(self.table)
        self.table.horizontalHeader().sectionClicked.connect(self.on_header_clicked)

        # Managers
        self.dbc_manager = DBCManager()
        self.slcan_manager = SLCANManager()
        self.processor = MessageProcessor(self.dbc_manager)
        
        # SLCAN state
        self.using_slcan = False
        self.received_messages = {}

        # IDs fixos
        self.test_ids = [0x100,0x101,0x102,0x103,0x104]
        self.messages_by_id = {}

        # Formatos atuais
        self.id_display_format = "Hex"
        self.raw_display_format = "Hex"

        # Timer
        self.last_timestamp_global = None
        self.last_timestamp_by_id = {}
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_messages)
        self.timer.start(500)

        # Inicializar tabela com 5 linhas
        self.table.setRowCount(len(self.test_ids))
        for i,row_id in enumerate(self.test_ids):
            self.set_table_item(i,0,f"0x{row_id:X}")
            self.set_table_item(i,1,"STD")
            self.set_table_item(i,2,"8")
            self.set_table_item(i,3,"")
            self.set_table_item(i,4,"")
            self.set_table_item(i,5,"")
            item_id = self.table.item(i,0)
            if item_id:
                item_id.setData(Qt.ItemDataRole.UserRole,row_id)

    # ---- Menu actions ----
    def select_channel(self): self.label_status.setText("Channel selected (simulated)")
    def select_bitrate(self): self.label_status.setText("Bitrate selected (simulated)")
    def load_dbc(self):
        file_name,_ = QFileDialog.getOpenFileName(self,"Open DBC","","DBC Files (*.dbc)")
        if file_name:
            self.dbc_manager.load_dbc(file_name)
            self.label_status.setText(f"DBC loaded: {file_name}")
    def open_conversion_dialog(self):
        dlg = ConversionDialog(self.dbc_manager)
        dlg.exec()
    def open_slcan_dialog(self):
        dlg = SLCANConnectionDialog(self.slcan_manager)
        # Connect SLCAN message callback
        if not self.using_slcan:
            self.slcan_manager.start_listening(self.on_slcan_message)
            self.using_slcan = True
        dlg.exec()
    def start_log(self): self.label_status.setText("Logging started (simulated)")
    def stop_log(self): self.label_status.setText("Logging stopped (simulated)")
    def toggle_autoscroll(self): self.autoscroll_enabled = self.autoscroll_btn.isChecked()
    
    def on_slcan_message(self, message):
        """Handle incoming SLCAN messages"""
        msg_id = message["id"]
        self.received_messages[msg_id] = message
        
        # Update the table if this ID is being displayed
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                displayed_id = item.data(Qt.ItemDataRole.UserRole)
                if displayed_id == msg_id:
                    self.update_row_with_message(row, message)
                    break

    # ---- Formatação ----
    def format_data(self,data,fmt):
        if fmt=="Decimal": return " ".join(str(b) for b in data)
        elif fmt=="Hex": return " ".join(f"0x{b:02X}" for b in data)
        elif fmt=="Octal": return " ".join(oct(b)[2:] for b in data)
        elif fmt=="ASCII": return "".join(chr(b) if 32<=b<=126 else "." for b in data)
        return str(data)

    # ---- Cabeçalho clicado ----
    def on_header_clicked(self,index):
        if index==3:  # Raw Data
            fmt_list=["Decimal","Hex","Octal","ASCII"]
            fmt,ok=QInputDialog.getItem(self,"Select Column Format",
                "Choose data format for Raw Data column:",fmt_list,current=fmt_list.index(self.raw_display_format),editable=False)
            if ok and fmt: self.raw_display_format=fmt; self.update_all_raw_data()
        elif index==0: # ID
            fmt_list=["Hex","Decimal"]
            fmt,ok=QInputDialog.getItem(self,"Select Column Format",
                "Choose display format for ID column:",fmt_list,current=fmt_list.index(self.id_display_format),editable=False)
            if ok and fmt: self.id_display_format=fmt; self.update_all_ids()

    # ---- Atualizar células ----
    def set_table_item(self,row,column,text):
        item=self.table.item(row,column)
        if not item:
            item=QTableWidgetItem()
            self.table.setItem(row,column,item)
        item.setText(text)

    def update_all_ids(self):
        for row in range(self.table.rowCount()):
            item=self.table.item(row,0)
            if item:
                value=item.data(Qt.ItemDataRole.UserRole)
                if value is not None:
                    item.setText(f"0x{value:X}" if self.id_display_format=="Hex" else str(value))

    def update_all_raw_data(self):
        for row in range(self.table.rowCount()):
            item=self.table.item(row,3)
            if item:
                data=item.data(Qt.ItemDataRole.UserRole)
                if data:
                    item.setText(self.format_data(data,self.raw_display_format))

    def update_all_timestamps(self):
        self.time_mode=self.time_mode_combo.currentText()
        self.last_timestamp_global=None
        self.last_timestamp_by_id={}
        for row in range(self.table.rowCount()):
            msg_id = self.table.item(row,0).data(Qt.ItemDataRole.UserRole)
            msg_data = self.messages_by_id.get(msg_id)
            if msg_data:
                self.update_timestamp_for_row(row,msg_data)

    def update_timestamp_for_row(self,row,msg):
        raw_time=msg["timestamp"]
        ts_text=""
        if self.time_mode=="Absolute": ts_text=raw_time.strftime("%H:%M:%S.%f")[:-3]
        elif self.time_mode=="Incremental":
            delta=0.0 if self.last_timestamp_global is None else (raw_time - self.last_timestamp_global).total_seconds()
            ts_text=f"{delta:.3f}s"
            self.last_timestamp_global=raw_time
        elif self.time_mode=="Differential":
            last=self.last_timestamp_by_id.get(msg["id"])
            delta=0.0 if last is None else (raw_time - last).total_seconds()
            ts_text=f"{delta:.3f}s"
            self.last_timestamp_by_id[msg["id"]]=raw_time
        self.set_table_item(row,5,ts_text)
    
    def update_row_with_message(self, row, msg):
        """Update a table row with a real CAN message"""
        msg["decoded"] = self.processor.decode_message(msg)
        
        # Update all columns
        self.set_table_item(row, 1, msg["type"])
        self.set_table_item(row, 2, str(len(msg["data"])))
        
        # Raw data
        raw_item = self.table.item(row, 3)
        if not raw_item: 
            raw_item = QTableWidgetItem()
            self.table.setItem(row, 3, raw_item)
        raw_item.setData(Qt.ItemDataRole.UserRole, msg["data"])
        raw_item.setText(self.format_data(msg["data"], self.raw_display_format))
        
        # Decoded signals
        self.set_table_item(row, 4, json.dumps(msg["decoded"]))
        
        # ID
        msg_id = msg["id"]
        id_item = self.table.item(row, 0)
        if id_item: 
            id_item.setText(f"0x{msg_id:X}" if self.id_display_format == "Hex" else str(msg_id))
        
        # Timestamp
        self.update_timestamp_for_row(row, msg)

    # ---- Atualizar mensagens ----
    def update_messages(self):
        # If using SLCAN and we have real messages, display them
        if self.using_slcan and self.slcan_manager.is_connected:
            # Update status
            self.label_status.setText("Status: Connected to SLCAN")
            
            # Show received messages in the table
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 0)
                if id_item:
                    displayed_id = id_item.data(Qt.ItemDataRole.UserRole)
                    if displayed_id in self.received_messages:
                        msg = self.received_messages[displayed_id]
                        self.update_row_with_message(row, msg)
        else:
            # Fall back to simulated messages
            for i,row_id in enumerate(self.test_ids):
                msg={"id":row_id,"type":"STD","data":[random.randint(0,255) for _ in range(8)],
                     "timestamp":datetime.datetime.now()}
                msg["decoded"]=self.processor.decode_message(msg)
                self.messages_by_id[row_id]=msg

                # Atualizar linha fixa
                self.set_table_item(i,1,msg["type"])
                self.set_table_item(i,2,str(len(msg["data"])))
                raw_item=self.table.item(i,3)
                if not raw_item: raw_item=QTableWidgetItem(); self.table.setItem(i,3,raw_item)
                raw_item.setData(Qt.ItemDataRole.UserRole,msg["data"])
                raw_item.setText(self.format_data(msg["data"],self.raw_display_format))
                self.set_table_item(i,4,json.dumps(msg["decoded"]))

                # ID
                id_item=self.table.item(i,0)
                if id_item: id_item.setText(f"0x{row_id:X}" if self.id_display_format=="Hex" else str(row_id))

                # Timestamp
                self.update_timestamp_for_row(i,msg)

        if self.autoscroll_enabled: self.table.scrollToBottom()
    
    def closeEvent(self, event):
        """Clean up when closing the application"""
        if self.slcan_manager.is_connected:
            self.slcan_manager.disconnect()
        event.accept()
