# file: tabs/comparison_tab.py

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QCalendarWidget, QComboBox, QPushButton, QMessageBox
)
from PyQt5.QtCore import QDate, Qt
import pyqtgraph as pg
import pandas as pd
import numpy as np
import datetime

class ComparisonTab(QWidget):
    def __init__(self, data_file):
        super().__init__()
        self.data_file = data_file
        self.plots = []  # <-- penting: siapkan sebelum koneksi event
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)

        # --- Panel kontrol ---
        control_layout = QVBoxLayout()
        control_layout.addWidget(QLabel("<b>1. Pilih Parameter:</b>"))

        self.param_selector = QComboBox()
        self.param_selector.addItems([
            'temperature', 'humidity', 'moisture', 'ph', 'ec',
            'nitrogen', 'phosphorus', 'potassium', 'cps', 'activity'
        ])
        control_layout.addWidget(self.param_selector)

        control_layout.addWidget(QLabel("<b>2. Pilih Rentang Tanggal:</b>"))
        self.calendar_start = QCalendarWidget()
        self.calendar_end = QCalendarWidget()
        self.calendar_start.setMaximumDate(QDate.currentDate())
        self.calendar_end.setMaximumDate(QDate.currentDate())
        control_layout.addWidget(QLabel("Tanggal Mulai:"))
        control_layout.addWidget(self.calendar_start)
        control_layout.addWidget(QLabel("Tanggal Selesai:"))
        control_layout.addWidget(self.calendar_end)

        self.compare_btn = QPushButton("🚀 Proses & Bandingkan")
        self.compare_btn.setFixedHeight(50)
        self.compare_btn.clicked.connect(self.update_comparison)
        control_layout.addWidget(self.compare_btn)
        control_layout.addStretch()

        # --- Plot ---
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)
        self.plot_widget.addLegend()
        axis = pg.DateAxisItem(orientation='bottom')
        self.plot_widget.setAxisItems({'bottom': axis})

        # Crosshair + label koordinat
        self.vLine = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#aaaaaa', style=Qt.DashLine))
        self.hLine = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen('#aaaaaa', style=Qt.DashLine))
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)

        self.label = pg.LabelItem(justify='right')
        # Letakkan label di layout plot (pojok kanan atas)
        self.plot_widget.getPlotItem().layout.addItem(self.label, 0, 1)

        # Batasi frekuensi event mouse supaya ringan
        self.proxy = pg.SignalProxy(
            self.plot_widget.scene().sigMouseMoved,
            rateLimit=30,
            slot=self.mouseMoved
        )

        layout.addLayout(control_layout, 1)
        layout.addWidget(self.plot_widget, 3)

    def update_comparison(self):
        # Baca data
        try:
            df = pd.read_csv(self.data_file, parse_dates=['timestamp'])
        except FileNotFoundError:
            QMessageBox.warning(self, "Error", "File data log belum ditemukan.")
            return

        start_date = self.calendar_start.selectedDate().toPyDate()
        end_date = self.calendar_end.selectedDate().toPyDate()
        param = self.param_selector.currentText()

        filtered_df = df[(df['timestamp'].dt.date >= start_date) &
                         (df['timestamp'].dt.date <= end_date)]
        if filtered_df.empty:
            QMessageBox.information(self, "Info", "Tidak ada data pada rentang tanggal ini.")
            return

        data_sys1 = filtered_df[filtered_df['system_id'] == 'Lisimeter_1']
        data_sys2 = filtered_df[filtered_df['system_id'] == 'Lisimeter_2']

        # Bersihkan plot, lalu tambahkan kembali crosshair & label
        self.plot_widget.clear()
        self.plot_widget.addLegend()
        self.plot_widget.addItem(self.vLine, ignoreBounds=True)
        self.plot_widget.addItem(self.hLine, ignoreBounds=True)
        # pastikan label tetap di layout plot setelah clear
        self.plot_widget.getPlotItem().layout.addItem(self.label, 0, 1)

        self.plot_widget.setTitle(f"Perbandingan {param.capitalize()}",
                                  color="#ecf0f1", size="18pt")

        self.plots = []  # reset daftar data untuk crosshair

        # Plot Lisimeter 1
        if not data_sys1.empty:
            ts1 = (data_sys1['timestamp'].astype('int64') // 10**9).to_numpy()
            y1 = data_sys1[param].to_numpy()
            p1 = self.plot_widget.plot(ts1, y1,
                                       pen=pg.mkPen('#38BDF8', width=2),
                                       name="Lisimeter 1")
            # simpan info untuk crosshair/tooltip
            self.plots.append({
                'x': ts1, 'y': y1, 'name': 'Lisimeter 1', 'color': '#38BDF8', 'item': p1
            })

        # Plot Lisimeter 2
        if not data_sys2.empty:
            ts2 = (data_sys2['timestamp'].astype('int64') // 10**9).to_numpy()
            y2 = data_sys2[param].to_numpy()
            p2 = self.plot_widget.plot(ts2, y2,
                                       pen=pg.mkPen('#F43F5E', width=2),
                                       name="Lisimeter 2")
            self.plots.append({
                'x': ts2, 'y': y2, 'name': 'Lisimeter 2', 'color': '#F43F5E', 'item': p2
            })

    def mouseMoved(self, evt):
        # evt dari SignalProxy berupa tuple (QPointF,)
        pos = evt[0] if isinstance(evt, tuple) else evt

        plotItem = self.plot_widget.getPlotItem()
        vb = plotItem.vb

        # Abaikan jika kursor di luar area scene plot
        if not plotItem.sceneBoundingRect().contains(pos):
            return

        mousePoint = vb.mapSceneToView(pos)
        x = mousePoint.x()
        y = mousePoint.y()

        # Gerakkan crosshair
        self.vLine.setPos(x)
        self.hLine.setPos(y)

        # Jika belum ada data terplot, kosongkan label dan selesai
        if not self.plots:
            self.label.setText("")
            return

        # Susun teks label untuk tiap seri (nilai terdekat)
        lines = []
        for d in self.plots:
            ts = d['x']
            vals = d['y']
            if ts.size == 0:
                continue

            # Cari index x terdekat (pakai searchsorted lalu cek tetangga)
            idx = np.searchsorted(ts, x)
            if idx == len(ts):
                idx = len(ts) - 1
            elif idx > 0 and abs(x - ts[idx - 1]) < abs(x - ts[idx]):
                idx = idx - 1

            cx = float(ts[idx])
            cy = float(vals[idx])

            date_str = datetime.datetime.fromtimestamp(cx).strftime("%Y-%m-%d %H:%M:%S")
            lines.append(
                f"<span style='color:{d['color']}'>{d['name']}: {date_str} | {cy:.2f}</span>"
            )

        self.label.setText("<br>".join(lines))
