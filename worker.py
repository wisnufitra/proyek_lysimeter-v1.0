# file: worker.py

import time
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import serial
import socket

class DataWorker(QObject):
    data_received = pyqtSignal(dict)
    status_update = pyqtSignal(str)
    
    def __init__(self, port_info):
        super().__init__()
        self.port_info = port_info
        self.running = True
        self.sock = None  # simpan socket supaya bisa ditutup dengan aman

    @pyqtSlot()
    def run(self):
        """Memilih mode koneksi berdasarkan nama port."""
        if "SIMULATOR" in self.port_info:
            self.run_simulator_client()
        else:
            self.run_serial_connection()

    def run_serial_connection(self):
        """Logika untuk terhubung ke perangkat keras asli (serial)."""
        try:
            ser = serial.Serial(self.port_info, 9600, timeout=1)
            self.status_update.emit(f"✅ Terhubung ke Hardware di {self.port_info}")
            while self.running:
                if ser.is_open and ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:
                        self.parse_and_emit(line)
                time.sleep(0.1)  # Beri jeda agar tidak membebani CPU
            if ser.is_open:
                ser.close()
        except serial.SerialException as e:
            self.status_update.emit(f"❌ Gagal: {e}")
        self.status_update.emit(f"🔌 Terputus dari {self.port_info}")

    def run_simulator_client(self):
        """Logika koneksi ke simulator via socket TCP."""
        port = 65431 if self.port_info == "SIMULATOR_1" else 65432
        host = '127.0.0.1'
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect((host, port))
            self.status_update.emit(f"✅ Terhubung ke Simulator di port {port}")
            f = self.sock.makefile('r', encoding='utf-8')

            while self.running:
                line = f.readline()
                if not line:
                    # jangan langsung break, tunggu sebentar
                    time.sleep(0.1)
                    continue
                # kalau server kirim sinyal "STOP", keluar loop
                if line.strip() == "STOP":
                    break
                self.parse_and_emit(line.strip())

        except Exception as e:
            self.status_update.emit(f"❌ Gagal terhubung ke Simulator: {e}")
        finally:
            try:
                if self.sock:
                    self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            if self.sock:
                self.sock.close()
            self.sock = None
            self.status_update.emit("🔌 Terputus dari Simulator")

    def parse_and_emit(self, line):
        """Mem-parsing baris data dan mengirimkannya via sinyal."""
        try:
            parts = line.split(',')
            if len(parts) == 12:
                data = {
                    'timestamp': datetime.now(),
                    'temperature': float(parts[0]), 'humidity': float(parts[1]),
                    'moisture': float(parts[2]), 'ph': float(parts[3]), 'ec': float(parts[4]),
                    'nitrogen': float(parts[5]), 'phosphorus': float(parts[6]),
                    'potassium': float(parts[7]), 'source_name': parts[8],
                    'energy': float(parts[9]), 'cps': int(parts[10]), 'activity': float(parts[11])
                }
                self.data_received.emit(data)
        except (ValueError, IndexError):
            pass  # Abaikan data yang formatnya salah

    def stop(self):
        """Hentikan loop dan beri tahu server."""
        self.running = False
        if self.sock:
            try:
                self.sock.sendall(b"STOP\n")
            except:
                pass
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except:
                pass
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
