# file: tabs/settings_tab.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel,
    QComboBox, QPushButton, QMessageBox, QDoubleSpinBox,
    QSpinBox, QTableWidget, QHeaderView, QTableWidgetItem,
    QDialog, QCalendarWidget, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from datetime import datetime

class SettingsTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.config_manager = main_app.config
        self.initUI()
        self.load_settings_to_ui()

    # ---------------- UI ----------------
    def initUI(self):
        main_layout = QVBoxLayout(self)

        # Tema
        theme_box = QGroupBox("Pengaturan Tampilan")
        theme_layout = QGridLayout(theme_box)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        theme_layout.addWidget(QLabel("Pilih Tema Aplikasi:"), 0, 0)
        theme_layout.addWidget(self.theme_combo, 0, 1)

        # Thresholds
        threshold_box = QGroupBox("Ambang Batas Peringatan Visual (Alarm)")
        threshold_layout = QGridLayout(threshold_box)

        self.threshold_inputs = {
            'temp_warn':      QDoubleSpinBox(self, value=28.0, suffix=" °C", decimals=1),
            'temp_danger':    QDoubleSpinBox(self, value=32.0, suffix=" °C", decimals=1),
            'moisture_warn':  QDoubleSpinBox(self, value=40.0, suffix=" %",  decimals=1),
            'moisture_danger':QDoubleSpinBox(self, value=30.0, suffix=" %",  decimals=1),
            'cps_warn':       QSpinBox(self, value=400, suffix=" CPS"),
            'cps_danger':     QSpinBox(self, value=500, suffix=" CPS"),
        }
        for spinbox in self.threshold_inputs.values():
            spinbox.setMaximum(9999)

        # Baris Temperature (aturan ">")
        threshold_layout.addWidget(QLabel("<b>Temperature:</b>"), 0, 0)
        threshold_layout.addWidget(QLabel("Warning >"), 0, 1)
        threshold_layout.addWidget(self.threshold_inputs['temp_warn'], 0, 2)
        threshold_layout.addWidget(QLabel("Danger >"), 0, 3)
        threshold_layout.addWidget(self.threshold_inputs['temp_danger'], 0, 4)

        # Baris Moisture (aturan "<")
        threshold_layout.addWidget(QLabel("<b>Moisture:</b>"), 1, 0)
        threshold_layout.addWidget(QLabel("Warning <"), 1, 1)
        threshold_layout.addWidget(self.threshold_inputs['moisture_warn'], 1, 2)
        threshold_layout.addWidget(QLabel("Danger <"), 1, 3)
        threshold_layout.addWidget(self.threshold_inputs['moisture_danger'], 1, 4)

        # Baris CPS (aturan ">")
        threshold_layout.addWidget(QLabel("<b>Counting Rate:</b>"), 2, 0)
        threshold_layout.addWidget(QLabel("Warning >"), 2, 1)
        threshold_layout.addWidget(self.threshold_inputs['cps_warn'], 2, 2)
        threshold_layout.addWidget(QLabel("Danger >"), 2, 3)
        threshold_layout.addWidget(self.threshold_inputs['cps_danger'], 2, 4)

        # Kalibrasi
        cal_box = QGroupBox("Manajemen Kalibrasi Sensor")
        cal_layout = QVBoxLayout(cal_box)
        self.cal_table = QTableWidget()
        self.cal_table.setColumnCount(4)
        self.cal_table.setHorizontalHeaderLabels(["Parameter", "Faktor Pengali (m)", "Faktor Penambah (c)", "Tgl Kalibrasi"])
        self.cal_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cal_table.cellDoubleClicked.connect(self.edit_calibration_date)
        cal_layout.addWidget(QLabel("Klik dua kali pada tanggal untuk mengubahnya."))
        cal_layout.addWidget(self.cal_table)

        # Tombol simpan
        apply_btn = QPushButton("Simpan & Terapkan Semua Pengaturan")
        apply_btn.clicked.connect(self.save_all_settings)

        # Susun ke layout utama
        main_layout.addWidget(theme_box)
        main_layout.addWidget(threshold_box)
        main_layout.addWidget(cal_box)
        main_layout.addWidget(apply_btn)
        main_layout.addStretch()

    # ------------- LOAD -------------
    def load_settings_to_ui(self):
        """Load config -> isi widget UI. Tahan banting walau key belum ada."""
        settings = self.config_manager.settings or {}

        # Tema
        theme = settings.get('theme', 'Dark')
        self.theme_combo.setCurrentIndex(0 if theme == 'Dark' else 1)

        # Thresholds
        thresholds = settings.get('thresholds') or {}
        for key, spinbox in self.threshold_inputs.items():
            if key in thresholds:
                try:
                    # QSpinBox expects int; QDoubleSpinBox expects float
                    if isinstance(spinbox, QSpinBox) and not isinstance(spinbox, QDoubleSpinBox):
                        spinbox.setValue(int(thresholds[key]))
                    else:
                        spinbox.setValue(float(thresholds[key]))
                except Exception:
                    # Abaikan jika tipe tidak pas; gunakan default bawaan widget
                    pass

        # Kalibrasi
        cal_data = settings.get('calibration') or {}
        self.cal_table.setRowCount(len(cal_data))
        for row, (param, values) in enumerate(cal_data.items()):
            param_item = QTableWidgetItem(param.replace('_', ' ').capitalize())
            param_item.setFlags(param_item.flags() & ~Qt.ItemIsEditable)
            self.cal_table.setItem(row, 0, param_item)

            m_item = QTableWidgetItem(str(values.get('m', 1.0)))
            self.cal_table.setItem(row, 1, m_item)

            c_item = QTableWidgetItem(str(values.get('c', 0.0)))
            self.cal_table.setItem(row, 2, c_item)

            date_item = QTableWidgetItem(str(values.get('last_calibrated', 'N/A')))
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.cal_table.setItem(row, 3, date_item)

    # ------------- SAVE -------------
    def save_all_settings(self):
        """Ambil semua nilai dari UI -> validasi -> kirim ke MainWindow."""
        try:
            # Salin dict supaya tidak mutate referensi langsung (aman kalau config_manager caching)
            settings_to_save = dict(self.config_manager.settings or {})

            # Tema
            settings_to_save['theme'] = self.theme_combo.currentText()

            # Pastikan dict thresholds ada
            thresholds = settings_to_save.get('thresholds')
            if not isinstance(thresholds, dict):
                thresholds = {}
                settings_to_save['thresholds'] = thresholds

            # Ambil nilai dari spinbox
            for key, spinbox in self.threshold_inputs.items():
                if isinstance(spinbox, QSpinBox) and not isinstance(spinbox, QDoubleSpinBox):
                    thresholds[key] = int(spinbox.value())
                else:
                    thresholds[key] = float(spinbox.value())

            # Validasi hubungan Warning/Danger
            self._validate_thresholds(thresholds)

            # Pastikan dict calibration ada
            calibration = settings_to_save.get('calibration')
            if not isinstance(calibration, dict):
                calibration = {}
                settings_to_save['calibration'] = calibration

            # Ambil data tabel kalibrasi
            for row in range(self.cal_table.rowCount()):
                item_param = self.cal_table.item(row, 0)
                if not item_param:
                    continue
                param = item_param.text().lower().replace(' ', '_')

                m_item = self.cal_table.item(row, 1)
                c_item = self.cal_table.item(row, 2)
                d_item = self.cal_table.item(row, 3)

                # Tangani sel kosong/invalid
                try:
                    m_val = float(m_item.text()) if (m_item and m_item.text().strip()) else 1.0
                    c_val = float(c_item.text()) if (c_item and c_item.text().strip()) else 0.0
                except ValueError:
                    raise ValueError(f"Nilai kalibrasi untuk '{param}' tidak valid. Gunakan angka untuk m/c.")

                date_val = d_item.text() if (d_item and d_item.text().strip() and d_item.text() != 'N/A') \
                           else datetime.now().strftime("%Y-%m-%d")

                if param not in calibration:
                    calibration[param] = {}
                calibration[param]['m'] = m_val
                calibration[param]['c'] = c_val
                calibration[param]['last_calibrated'] = date_val

            # Kirim ke MainWindow (menyimpan + menerapkan)
            self.main_app.update_settings(settings_to_save)
            QMessageBox.information(self, "Sukses", "Semua pengaturan berhasil disimpan dan diterapkan.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Terjadi kesalahan saat menyimpan: {e}")

    # ------------- UTIL -------------
    def _validate_thresholds(self, t: dict):
        """Pastikan urutan Warning/Danger sesuai aturan label UI."""
        required = ['temp_warn', 'temp_danger', 'moisture_warn', 'moisture_danger', 'cps_warn', 'cps_danger']
        missing = [k for k in required if k not in t]
        if missing:
            raise ValueError(f"Key thresholds hilang: {', '.join(missing)}")

        # Temperature & CPS: aturan 'Warning >' / 'Danger >' -> danger harus >= warn
        if t['temp_danger'] < t['temp_warn']:
            raise ValueError("Temperature: 'Danger' harus lebih besar/sama dengan 'Warning'.")
        if t['cps_danger'] < t['cps_warn']:
            raise ValueError("Counting Rate: 'Danger' harus lebih besar/sama dengan 'Warning'.")

        # Moisture: aturan 'Warning <' / 'Danger <' -> danger harus <= warn
        if t['moisture_danger'] > t['moisture_warn']:
            raise ValueError("Moisture: 'Danger' harus lebih kecil/sama dengan 'Warning'.")

    # ------------- Dialog tanggal kalibrasi -------------
    def edit_calibration_date(self, row, column):
        if column != 3:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Pilih Tanggal Kalibrasi")
        layout = QVBoxLayout(dialog)
        calendar = QCalendarWidget()
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(calendar)
        layout.addWidget(buttons)
        if dialog.exec_() == QDialog.Accepted:
            self.cal_table.item(row, column).setText(calendar.selectedDate().toString("yyyy-MM-dd"))
