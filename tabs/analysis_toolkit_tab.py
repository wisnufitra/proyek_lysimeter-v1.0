# file: tabs/analysis_toolkit_tab.py

import pandas as pd
import numpy as np
import pywt
import pyqtgraph as pg
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QCalendarWidget, QComboBox, QPushButton, QMessageBox,
    QGroupBox, QSpinBox
)


class AnalysisToolkitTab(QWidget):
    """Tab untuk analisis data historis dengan fungsi matematika."""
    def __init__(self, data_file=None):
        super().__init__()
        self.data_file = data_file
        self.df = None
        self.initUI()

    def initUI(self):
        main_layout = QHBoxLayout(self)

        # --- Panel Kontrol di Kiri ---
        control_panel = QGroupBox("Panel Kontrol Analisis")
        control_panel.setFixedWidth(350)
        control_layout = QVBoxLayout(control_panel)

        # 1. Pemilihan Data
        control_layout.addWidget(QLabel("<b>1. Pilih Data Sumber</b>"))
        self.system_selector = QComboBox()
        self.system_selector.addItems(["Lisimeter_1", "Lisimeter_2"])
        self.param_selector = QComboBox()
        self.param_selector.addItems([
            'temperature', 'humidity', 'moisture', 'ph', 'ec',
            'cps', 'activity', 'nitrogen', 'phosphorus', 'potassium', 'energy'
        ])

        form_layout_1 = QGridLayout()
        form_layout_1.addWidget(QLabel("Sistem:"), 0, 0)
        form_layout_1.addWidget(self.system_selector, 0, 1)
        form_layout_1.addWidget(QLabel("Parameter:"), 1, 0)
        form_layout_1.addWidget(self.param_selector, 1, 1)
        control_layout.addLayout(form_layout_1)

        # 2. Pemilihan Rentang Waktu
        control_layout.addWidget(QLabel("<b>2. Pilih Rentang Tanggal</b>"))
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        control_layout.addWidget(self.calendar)

        # 3. Pemilihan Fungsi Analisis
        control_layout.addWidget(QLabel("<b>3. Pilih Fungsi Analisis</b>"))
        self.func_selector = QComboBox()
        self.func_selector.addItems(["Moving Average", "Fast Fourier Transform (FFT)"])
        self.func_selector.currentTextChanged.connect(self.toggle_param_box)

        self.param_box_label = QLabel("Ukuran Window:")
        self.param_box = QSpinBox(self, value=10, minimum=2, maximum=200, suffix=" sampel")

        func_layout = QHBoxLayout()
        func_layout.addWidget(self.func_selector)
        func_layout.addWidget(self.param_box_label)
        func_layout.addWidget(self.param_box)
        control_layout.addLayout(func_layout)

        # 4. Tombol Aksi
        self.run_btn = QPushButton("🚀 Jalankan Analisis")
        self.run_btn.setFixedHeight(40)
        self.run_btn.clicked.connect(self.run_analysis)
        control_layout.addWidget(self.run_btn)
        control_layout.addStretch()

        # --- Area Grafik di Kanan ---
        plot_layout = QVBoxLayout()
        self.plot_original = pg.PlotWidget(title="Sinyal Asli")
        self.plot_fft = pg.PlotWidget(title="Fast Fourier Transform (FFT)")
        self.plot_autocorr = pg.PlotWidget(title="Autocorrelation")
        self.plot_denoised = pg.PlotWidget(title="Denoised (Wavelet)")

        self.plot_original.addLegend()
        self.plot_fft.addLegend()
        self.plot_autocorr.addLegend()
        self.plot_denoised.addLegend()

        plot_layout.addWidget(self.plot_original)
        plot_layout.addWidget(self.plot_fft)
        plot_layout.addWidget(self.plot_autocorr)
        plot_layout.addWidget(self.plot_denoised)

        main_layout.addWidget(control_panel)
        main_layout.addLayout(plot_layout)

        self.toggle_param_box(self.func_selector.currentText())

    def toggle_param_box(self, text):
        is_ma = "Moving Average" in text
        self.param_box.setVisible(is_ma)
        self.param_box_label.setVisible(is_ma)

    def run_analysis(self):
        """Menjalankan analisis data."""
        if self.data_file is None:
            QMessageBox.warning(self, "Data Error", "Data file tidak ditemukan.")
            return

        try:
            self.df = pd.read_csv(self.data_file, parse_dates=['timestamp'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Gagal membaca file: {e}")
            return

        param = self.param_selector.currentText()
        if param not in self.df.columns:
            QMessageBox.warning(self, "Parameter Error", f"Kolom '{param}' tidak ada di file data.")
            return

        data = self.df.dropna(subset=[param])
        ts = data['timestamp'].astype('int64') / 1e9
        signal = data[param].to_numpy()
        n = len(signal)

        # Bersihkan plot sebelum menggambar ulang
        self.plot_original.clear()
        self.plot_fft.clear()
        self.plot_autocorr.clear()
        self.plot_denoised.clear()

        # --- 1. Sinyal Asli ---
        self.plot_original.plot(
            ts, signal,
            pen=pg.mkPen('#9CA3AF', width=2),
            name="Sinyal Asli"
        )

        # --- 2. FFT ---
        fft_vals = np.fft.fft(signal)
        fft_freqs = np.fft.fftfreq(n, d=np.median(np.diff(ts)))
        self.plot_fft.plot(
            fft_freqs[:n // 2],
            np.abs(fft_vals[:n // 2]),
            pen=pg.mkPen('#F59E0B', width=2),
            name="FFT"
        )

        # --- 3. Autocorrelation ---
        autocorr = np.correlate(signal - np.mean(signal), signal - np.mean(signal), mode='full')
        lags = np.arange(-n + 1, n)
        self.plot_autocorr.plot(
            lags, autocorr,
            pen=pg.mkPen('#10B981', width=2),
            name="Autocorrelation"
        )

        # --- 4. Denoising (Wavelet) ---
        coeffs = pywt.wavedec(signal, 'db4', level=4)
        sigma = np.median(np.abs(coeffs[-1])) / 0.6745
        uthresh = sigma * np.sqrt(2 * np.log(len(signal)))
        coeffs[1:] = [pywt.threshold(c, value=uthresh, mode='soft') for c in coeffs[1:]]
        denoised = pywt.waverec(coeffs, 'db4')

        min_len = min(len(ts), len(denoised))
        self.plot_denoised.plot(
            ts[:min_len],
            denoised[:min_len],
            pen='b',
            name="Denoised"
        )
