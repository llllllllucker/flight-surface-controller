import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QComboBox, QPushButton, QLabel, 
                             QTextEdit, QSpinBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
import time

class SerialThread(QThread):
    """Поток для обработки серийной коммуникации"""
    data_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, port, baudrate=9600):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.is_running = False
    
    def run(self):
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.is_running = True
            self.connection_status.emit(True)
            
            while self.is_running:
                if self.serial_connection.in_waiting:
                    data = self.serial_connection.readline().decode('utf-8', errors='ignore').strip()
                    if data:
                        self.data_received.emit(f"Получено: {data}")
        except Exception as e:
            self.connection_status.emit(False)
            self.data_received.emit(f"Ошибка подключения: {str(e)}")
    
    def stop(self):
        self.is_running = False
        if self.serial_connection:
            self.serial_connection.close()
    
    def send_data(self, data):
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.write((data + '\n').encode())

class FlightControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.serial_thread = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle('Контроллер модели самолета (Arduino)')
        self.setGeometry(100, 100, 800, 600)
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        
        # === ГРУППА ПОДКЛЮЧЕНИЯ ===
        connection_group = QGroupBox("Подключение")
        connection_layout = QHBoxLayout()
        
        # Выбор COM-порта
        connection_layout.addWidget(QLabel("COM-порт:"))
        self.com_port_combo = QComboBox()
        self.refresh_ports()
        connection_layout.addWidget(self.com_port_combo)
        
        # Кнопка обновления портов
        refresh_btn = QPushButton("Обновить порты")
        refresh_btn.clicked.connect(self.refresh_ports)
        connection_layout.addWidget(refresh_btn)
        
        # Скорость передачи
        connection_layout.addWidget(QLabel("Скорость (baud):"))
        self.baudrate_spin = QSpinBox()
        self.baudrate_spin.setValue(9600)
        self.baudrate_spin.setMinimum(300)
        self.baudrate_spin.setMaximum(115200)
        connection_layout.addWidget(self.baudrate_spin)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # === ГРУППА УПРАВЛЕНИЯ ===
        control_group = QGroupBox("Управление")
        control_layout = QHBoxLayout()
        
        # Кнопка подключения
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.clicked.connect(self.connect_to_device)
        self.connect_btn.setStyleSheet("background-color: green; color: white; font-weight: bold;")
        control_layout.addWidget(self.connect_btn)
        
        # Кнопка проверки
        self.test_btn = QPushButton("Тест подключения")
        self.test_btn.clicked.connect(self.test_connection)
        self.test_btn.setEnabled(False)
        control_layout.addWidget(self.test_btn)
        
        # Кнопка отключения
        self.disconnect_btn = QPushButton("Отключиться")
        self.disconnect_btn.clicked.connect(self.disconnect_device)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        control_layout.addWidget(self.disconnect_btn)
        
        # Статус подключения
        self.status_label = QLabel("Статус: Не подключено")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.status_label)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # === ГРУППА КОМАНД ===
        commands_group = QGroupBox("Команды управления")
        commands_layout = QHBoxLayout()
        
        self.command_input = QTextEdit()
        self.command_input.setPlaceholderText("Введите команду для отправки на Arduino...")
        self.command_input.setMaximumHeight(50)
        commands_layout.addWidget(self.command_input)
        
        send_btn = QPushButton("Отправить")
        send_btn.clicked.connect(self.send_command)
        commands_layout.addWidget(send_btn)
        
        commands_group.setLayout(commands_layout)
        main_layout.addWidget(commands_group)
        
        # === ЛОГИРОВАНИЕ ===
        log_group = QGroupBox("Логи")
        log_layout = QVBoxLayout()
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        central_widget.setLayout(main_layout)
    
    def refresh_ports(self):
        """Обновляет список доступных COM-портов"""
        self.com_port_combo.clear()
        ports = serial.tools.list_ports.comports()
        
        if not ports:
            self.com_port_combo.addItem("Нет доступных портов")
            self.log("Не найдено доступных COM-портов")
        else:
            for port in ports:
                self.com_port_combo.addItem(f"{port.device} - {port.description}")
                self.log(f"Найден порт: {port.device} ({port.description})")
    
    def connect_to_device(self):
        """Подключается к Arduino"""
        port_info = self.com_port_combo.currentText()
        
        if "Нет доступных портов" in port_info:
            self.log("Ошибка: нет доступных портов")
            return
        
        port = port_info.split(" - ")[0]
        baudrate = self.baudrate_spin.value()
        
        try:
            self.serial_thread = SerialThread(port, baudrate)
            self.serial_thread.data_received.connect(self.on_data_received)
            self.serial_thread.connection_status.connect(self.on_connection_status)
            self.serial_thread.start()
            
            self.log(f"Попытка подключения к {port} на скорости {baudrate} baud...")
        except Exception as e:
            self.log(f"Ошибка подключения: {str(e)}")
    
    def test_connection(self):
        """Тестирует подключение отправкой тестовой команды"""
        if self.serial_thread and self.serial_thread.is_running:
            self.serial_thread.send_data("TEST")
            self.log("Отправлена тестовая команда 'TEST'")
        else:
            self.log("Ошибка: устройство не подключено")
    
    def disconnect_device(self):
        """Отключается от Arduino"""
        if self.serial_thread:
            self.serial_thread.stop()
            self.log("Отключено от устройства")
            self.status_label.setText("Статус: Не подключено")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.test_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
    
    def send_command(self):
        """Отправляет команду на Arduino"""
        command = self.command_input.toPlainText().strip()
        if command:
            if self.serial_thread and self.serial_thread.is_running:
                self.serial_thread.send_data(command)
                self.log(f"Отправлено: {command}")
                self.command_input.clear()
            else:
                self.log("Ошибка: устройство не подключено")
    
    def on_data_received(self, data):
        """Обработчик получения данных""" 
        self.log(data)
    
    def on_connection_status(self, is_connected):
        """Обработчик изменения статуса подключения""" 
        if is_connected:
            self.log("Успешное подключение к устройству!")
            self.status_label.setText("Статус: Подключено")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_btn.setEnabled(False)
            self.test_btn.setEnabled(True)
            self.disconnect_btn.setEnabled(True)
        else:
            self.log("Ошибка подключения")
            self.status_label.setText("Статус: Ошибка подключения")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_btn.setEnabled(True)
            self.test_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(False)
    
    def log(self, message):
        """Добавляет сообщение в логи"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_output.append(f"[{timestamp}] {message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FlightControllerApp()
    window.show()
    sys.exit(app.exec_())
