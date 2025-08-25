# file: main_window.py

import os
import csv
import socket
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QLabel, QComboBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import QThread, QTimer
from serial.tools import list_ports

from config_manager import ConfigManager
from worker import DataWorker  # <- pastikan ini DataWorker, bukan Worker
from custom_widgets import AnimatedTabWidget, HealthStatusWidget
from tabs.overview_tab import OverviewTab
from tabs.detailed_view_tab import DetailedViewTab
from tabs.comparison_tab import ComparisonTab
from tabs.datalog_tab import DataLogTab
from tabs.settings_tab import SettingsTab
from tabs.analysis_toolkit_tab import AnalysisToolkitTab
from styles import DARK_STYLE, LIGHT_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.settings = self.config.load_settings()
        self.setWindowTitle("LISIDA - Professional Dashboard v2.4")

        if self.settings.get('theme', 'Dark') == 'Light':
            self.setStyleSheet(LIGHT_STYLE)
        else:
            self.setStyleSheet(DARK_STYLE)

        self.connections = {}        # {system_id: {...}}
        self.DATA_FILE = "master_datalog.csv"
        self.health_timers = {}      # {system_id: QTimer}

        self.initUI()
        self.config.log_audit("Aplikasi LISIDA dimulai.")

    def initUI(self):
        self.showMaximized()
        main_layout = QVBoxLayout()

        # Panel kontrol koneksi
        control_panel = QHBoxLayout()
        control_panel.addWidget(self.create_connection_box("Lisimeter_1"))
        control_panel.addWidget(self.create_connection_box("Lisimeter_2"))
        main_layout.addLayout(control_panel)

        # Panel status kesehatan
        health_panel_box = QGroupBox("Status Kesehatan Sistem")
        health_panel_layout = QHBoxLayout(health_panel_box)
        self.health_widgets = {
            "Lisimeter_1": HealthStatusWidget("Lisimeter 1"),
            "Lisimeter_2": HealthStatusWidget("Lisimeter 2")
        }
        health_panel_layout.addWidget(self.health_widgets["Lisimeter_1"])
        health_panel_layout.addWidget(self.health_widgets["Lisimeter_2"])
        main_layout.addWidget(health_panel_box)

        # Tab utama
        self.tabs = AnimatedTabWidget()
        self.overview_tab = OverviewTab()
        self.detailed_tab = DetailedViewTab()
        self.comparison_tab = ComparisonTab(self.DATA_FILE)
        self.analysis_tab = AnalysisToolkitTab(self.DATA_FILE)
        self.datalog_tab = DataLogTab(self.DATA_FILE)
        self.settings_tab = SettingsTab(self)

        self.tabs.addTab(self.overview_tab, "📊  Overview")
        self.tabs.addTab(self.detailed_tab, "📈  Tampilan Detail")
        self.tabs.addTab(self.comparison_tab, "🔍  Analisis Perbandingan")
        self.tabs.addTab(self.analysis_tab, "🔬  Toolkit Analisis")
        self.tabs.addTab(self.datalog_tab, "📚  Log Data & Ekspor")
        self.tabs.addTab(self.settings_tab, "⚙️  Pengaturan & Kalibrasi")
        main_layout.addWidget(self.tabs)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.statusBar().showMessage("Aplikasi LISIDA Siap.")

    def create_connection_box(self, system_id):
        box = QGroupBox(system_id)
        layout = QHBoxLayout(box)

        port_selector = QComboBox()
        refresh_btn = QPushButton("🔄")
        refresh_btn.setFixedWidth(40)
        refresh_btn.clicked.connect(lambda: self.refresh_ports(port_selector))

        connect_btn = QPushButton("Hubungkan")
        disconnect_btn = QPushButton("Putuskan")
        disconnect_btn.setEnabled(False)

        layout.addWidget(QLabel("Port:"))
        layout.addWidget(port_selector)
        layout.addWidget(refresh_btn)
        layout.addWidget(connect_btn)
        layout.addWidget(disconnect_btn)

        self.refresh_ports(port_selector)

        connect_btn.clicked.connect(
            lambda: self.start_connection(system_id, port_selector, connect_btn, disconnect_btn)
        )
        disconnect_btn.clicked.connect(
            lambda: self.stop_connection(system_id, connect_btn, disconnect_btn, port_selector)
        )
        return box

    def check_simulator_availability(self, port):
        """Cek apakah simulator mendengar di port tsb. Timeout dibuat agak longgar."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.2)  # sebelumnya 0.05 -> mudah false negative
                s.connect(('127.0.0.1', port))
            return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False

    def refresh_ports(self, port_selector):
        current_selection = port_selector.currentText()
        port_selector.clear()

        port_list = []
        if self.check_simulator_availability(65431):
            port_list.append("SIMULATOR_1")
        if self.check_simulator_availability(65432):
            port_list.append("SIMULATOR_2")

        # Port serial fisik (kalau dipakai)
        try:
            available_ports = [p.device for p in list_ports.comports()]
            port_list.extend(available_ports)
        except Exception:
            pass

        if not port_list:
            port_selector.addItem("Tidak ada port")
        else:
            port_selector.addItems(port_list)

        index = port_selector.findText(current_selection)
        if index != -1:
            port_selector.setCurrentIndex(index)

    def start_connection(self, system_id, port_selector, connect_btn, disconnect_btn):
        port = port_selector.currentText()
        if not port or "Tidak ada" in port:
            QMessageBox.warning(self, "Peringatan", "Tidak ada port serial/simulator yang tersedia.")
            return

        self.config.log_audit(f"Koneksi dimulai untuk {system_id} di port {port}.")
        thread = QThread(self)
        worker = DataWorker(port_info=port)
        worker.moveToThread(thread)

        # Sinyal data & status
        worker.data_received.connect(lambda data: self.process_incoming_data(system_id, data))
        worker.status_update.connect(lambda msg: self.statusBar().showMessage(f"[{system_id}] {msg}"))

        # Start worker ketika thread mulai
        thread.started.connect(worker.run)
        # Bersihkan worker saat thread selesai
        thread.finished.connect(worker.deleteLater)

        # Mulai thread
        thread.start()

        # Timer kesehatan untuk deteksi "signal lost"
        self.health_timers[system_id] = QTimer(self)
        self.health_timers[system_id].setSingleShot(True)
        self.health_timers[system_id].timeout.connect(lambda: self.signal_lost(system_id))

        # Simpan referensi supaya tidak di-GC
        self.connections[system_id] = {
            'thread': thread,
            'worker': worker,
            'port_selector': port_selector,
            'connect_btn': connect_btn,
            'disconnect_btn': disconnect_btn
        }

        connect_btn.setEnabled(False)
        disconnect_btn.setEnabled(True)
        port_selector.setEnabled(False)

    def stop_connection(self, system_id, connect_btn, disconnect_btn, port_selector):
        if system_id in self.connections and 'worker' in self.connections[system_id]:
            try:
                if system_id in self.health_timers:
                    self.health_timers[system_id].stop()

                self.connections[system_id]['worker'].stop()     # akan kirim STOP ke simulator jika perlu
                self.connections[system_id]['thread'].quit()
                self.connections[system_id]['thread'].wait()
                self.config.log_audit(f"Koneksi dihentikan untuk {system_id}.")
                self.health_widgets[system_id].set_status("disconnected")
            except Exception as e:
                print(f"⚠️ Gagal stop {system_id}: {e}")

        connect_btn.setEnabled(True)
        disconnect_btn.setEnabled(False)
        port_selector.setEnabled(True)
        self.refresh_ports(port_selector)
        self.statusBar().showMessage(f"[{system_id}] Terputus.")

    def process_incoming_data(self, system_id, raw_data):
        # reset/ulang timer kesehatan setiap kali ada data
        if system_id in self.health_timers:
            self.health_timers[system_id].start(10000)  # 10 detik tanpa data => warning
            self.health_widgets[system_id].set_status("connected")

        calibrated_data = raw_data.copy()

        # kalibrasi linear m*x + c
        cal_params = self.settings.get('calibration', {})
        for param, values in cal_params.items():
            if param in calibrated_data:
                raw_value = calibrated_data[param]
                m = values.get('m', 1.0)
                c = values.get('c', 0.0)
                try:
                    calibrated_data[param] = (raw_value * m) + c
                except Exception:
                    pass

        thresholds = self.settings.get('thresholds', {})
        self.overview_tab.update_data(system_id, calibrated_data, thresholds)
        self.detailed_tab.update_data(system_id, calibrated_data)
        self.save_calibrated_data_to_log(system_id, calibrated_data)

    def signal_lost(self, system_id):
        self.health_widgets[system_id].set_status("warning")
        self.config.log_audit(f"PERINGATAN: Sinyal hilang dari {system_id}.")
        self.statusBar().showMessage(f"[{system_id}] PERINGATAN: Sinyal tidak diterima > 10 detik.")

    def update_settings(self, new_settings):
        self.settings = new_settings
        if self.settings.get('theme') == 'Light':
            self.setStyleSheet(LIGHT_STYLE)
        else:
            self.setStyleSheet(DARK_STYLE)
        self.config.save_settings(self.settings)

    def save_calibrated_data_to_log(self, system_id, data):
        header = [
            'system_id', 'timestamp', 'temperature', 'humidity', 'moisture', 'ph', 'ec',
            'nitrogen', 'phosphorus', 'potassium', 'source_name', 'energy', 'cps', 'activity'
        ]
        file_exists = os.path.exists(self.DATA_FILE)
        with open(self.DATA_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            if not file_exists:
                writer.writeheader()
            # pastikan format timestamp string
            if isinstance(data.get('timestamp'), datetime):
                data = data.copy()
                data['timestamp'] = data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
            row = {'system_id': system_id, **data}
            filtered_row = {key: row.get(key) for key in header}
            writer.writerow(filtered_row)

    def closeEvent(self, event):
        self.config.log_audit("Aplikasi LISIDA ditutup.")
        for system_id in list(self.connections.keys()):
            if 'worker' in self.connections[system_id]:
                conn_info = self.connections[system_id]
                try:
                    self.stop_connection(system_id, conn_info['connect_btn'], conn_info['disconnect_btn'], conn_info['port_selector'])
                except Exception as e:
                    print(f"⚠️ Error saat menutup koneksi {system_id}: {e}")
        event.accept()
