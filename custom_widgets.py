# file: custom_widgets.py

# --- SEMUA IMPORT DILETAKKAN DI ATAS ---
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTabBar, QStackedWidget
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtSlot, QParallelAnimationGroup
import pyqtgraph as pg
from collections import deque

# --- KELAS PARAMETERCARD YANG LAMA SUDAH DIHAPUS KARENA TIDAK DIGUNAKAN LAGI ---

# --- KELAS-KELAS YANG AKTIF DIGUNAKAN ---

class AnimatedTabWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tabBar = QTabBar()
        self.stackedWidget = QStackedWidget(self)

        main_layout.addWidget(self.tabBar)
        main_layout.addWidget(self.stackedWidget)

        self.tabBar.currentChanged.connect(self.change_tab)
        self._animation_group = QParallelAnimationGroup(self)
        self._current_index = -1

    def addTab(self, widget, label):
        self.tabBar.addTab(label)
        self.stackedWidget.addWidget(widget)
        if self._current_index == -1:
            self._current_index = 0
            self.stackedWidget.setCurrentIndex(0)

    @pyqtSlot(int)
    def change_tab(self, index):
        if self._current_index == index or index < 0:
            return

        current_widget = self.stackedWidget.widget(self._current_index)
        next_widget = self.stackedWidget.widget(index)
        
        if not current_widget or not next_widget:
            return

        # Hentikan dan bersihkan animasi sebelumnya
        self._animation_group.stop()
        for i in range(self._animation_group.animationCount()):
            self._animation_group.takeAnimation(0)

        # Animasi fade-out
        anim_out = QPropertyAnimation(current_widget, b"windowOpacity")
        anim_out.setDuration(150)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        self._animation_group.addAnimation(anim_out)
        
        # Animasi fade-in
        next_widget.setWindowOpacity(0.0)
        anim_in = QPropertyAnimation(next_widget, b"windowOpacity")
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        self._animation_group.addAnimation(anim_in)
        
        # Pindahkan widget ke depan
        self.stackedWidget.setCurrentWidget(next_widget)
        self._current_index = index
        self._animation_group.start()

class HealthStatusWidget(QWidget):
    """Widget untuk menampilkan status 'detak jantung' dari sebuah sistem."""
    def __init__(self, system_name):
        super().__init__()
        self.setObjectName("HealthStatusWidget")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self.name_label = QLabel(f"<b>{system_name}:</b>")
        self.status_indicator = QLabel("●") # Indikator lingkaran
        self.status_label = QLabel("Belum Terhubung")

        layout.addWidget(self.name_label)
        layout.addWidget(self.status_indicator)
        layout.addWidget(self.status_label)
        layout.addStretch()
        
        self.set_status("disconnected")

    def set_status(self, status):
        """Mengubah warna dan teks berdasarkan status."""
        self.setProperty("status", status)
        self.style().polish(self)
        
        if status == "connected":
            self.status_label.setText("Terhubung & Menerima Data")
        elif status == "warning":
            self.status_label.setText("Peringatan: Sinyal Hilang")
        else: # disconnected
            self.status_label.setText("Terputus")

class OverviewCard(QWidget):
    """Widget kustom yang menggabungkan nilai parameter dengan grafik mini (sparkline)."""
    def __init__(self, title, icon, unit=""):
        super().__init__()
        self.unit = unit
        self.setObjectName("OverviewCard")

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(5)

        top_layout = QHBoxLayout()
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setObjectName("cardTitle")
        self.value_label = QLabel("-")
        self.value_label.setObjectName("cardValue")
        self.value_label.setAlignment(Qt.AlignRight)

        top_layout.addWidget(self.title_label)
        top_layout.addWidget(self.value_label)
        
        self.sparkline = pg.PlotWidget()
        self.sparkline.setFixedHeight(60)
        self.sparkline.setObjectName("sparkline")
        self.sparkline.getPlotItem().hideAxis('bottom')
        self.sparkline.getPlotItem().hideAxis('left')
        self.sparkline.setMouseEnabled(x=False, y=False)
        self.sparkline_curve = self.sparkline.plot(pen=pg.mkPen('#5dade2', width=2))

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.sparkline)

        self.data_series = deque(maxlen=50)

    def update_data(self, value):
        if isinstance(value, (int, float)):
            self.value_label.setText(f"{value:.1f}{self.unit}")
        else:
            self.value_label.setText(str(value))

        if isinstance(value, (int, float)): # Hanya tambahkan angka ke grafik
            self.data_series.append(value)
            self.sparkline_curve.setData(list(self.data_series))
            
    def set_status(self, status):
        """Mengatur properti status untuk styling dinamis."""
        self.setProperty("status", status)
        self.style().polish(self)