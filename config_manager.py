# file: config_manager.py

import json
import os
import logging

class ConfigManager:
    """Kelas untuk mengelola semua konfigurasi dan log audit."""
    def __init__(self, config_file="config.json", audit_log_file="audit.log"):
        self.config_file = config_file
        self.settings = self.load_settings()
        self.setup_audit_log(audit_log_file)

    def get_default_settings(self):
        """Menyediakan struktur dan nilai default untuk pengaturan."""
        return {
            'theme': 'Dark',
            'calibration': {
                # Format: 'parameter': {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'}
                # m = faktor pengali, c = faktor penambah (offset)
                'temperature': {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'humidity':    {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'moisture':    {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'ph':          {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'ec':          {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'nitrogen':    {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'phosphorus':  {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'potassium':   {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'energy':      {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'cps':         {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
                'activity':    {'m': 1.0, 'c': 0.0, 'last_calibrated': 'N/A'},
            }
        }

    def load_settings(self):
        """Memuat pengaturan dari file JSON, atau membuat file jika tidak ada."""
        if not os.path.exists(self.config_file):
            # Jika file tidak ada, buat dengan nilai default
            default_settings = self.get_default_settings()
            with open(self.config_file, 'w') as f:
                json.dump(default_settings, f, indent=4)
            return default_settings
        else:
            # Jika file ada, buka dan baca
            with open(self.config_file, 'r') as f:
                return json.load(f)

    def save_settings(self, settings_data):
        """Menyimpan kamus pengaturan ke file JSON."""
        self.settings = settings_data
        with open(self.config_file, 'w') as f:
            json.dump(self.settings, f, indent=4)
        self.log_audit("Pengaturan aplikasi diperbarui dan disimpan.")

    def setup_audit_log(self, audit_log_file):
        """Mengkonfigurasi file log untuk jejak audit."""
        self.audit_logger = logging.getLogger('AuditLogger')
        self.audit_logger.setLevel(logging.INFO)
        handler = logging.FileHandler(audit_log_file)
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        if not self.audit_logger.handlers:
            self.audit_logger.addHandler(handler)
        
    def log_audit(self, message):
        """Menulis pesan ke file log audit."""
        self.audit_logger.info(message)