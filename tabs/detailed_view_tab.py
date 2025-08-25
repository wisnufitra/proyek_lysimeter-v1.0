# file: tabs/detailed_view_tab.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QComboBox, QSplitter, QGridLayout
from PyQt5.QtCore import Qt
import pyqtgraph as pg
from collections import deque
import numpy as np


class DetailedViewTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)

        # --- selector sistem ---
        self.system_selector = QComboBox()
        self.system_selector.addItems(["Lisimeter_1", "Lisimeter_2"])
        self.system_selector.currentTextChanged.connect(self.reset_all_graphs)
        main_layout.addWidget(self.system_selector)

        # --- splitter (sparklines kiri, main plot kanan) ---
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # container sparklines
        sparklines_container = QWidget()
        self.sparklines_layout = QGridLayout(sparklines_container)
        splitter.addWidget(sparklines_container)

        # plot utama
        self.main_plot = pg.PlotWidget()
        self.main_plot.setBackground(None)
        splitter.addWidget(self.main_plot)
        splitter.setSizes([450, 850])

        # crosshair + label
        self.crosshair_v = pg.InfiniteLine(angle=90, movable=False)
        self.crosshair_h = pg.InfiniteLine(angle=0, movable=False)
        self.label = pg.TextItem(anchor=(0, 1))
        self.main_plot.addItem(self.crosshair_v, ignoreBounds=True)
        self.main_plot.addItem(self.crosshair_h, ignoreBounds=True)
        self.main_plot.addItem(self.label, ignoreBounds=True)

        # titik highlight
        self.highlight_point = pg.ScatterPlotItem(size=12, brush=pg.mkBrush('#FACC15'))
        self.main_plot.addItem(self.highlight_point)

        # signal mouse
        self.proxy = pg.SignalProxy(
            self.main_plot.scene().sigMouseMoved,
            rateLimit=60,
            slot=self.mouse_moved
        )

        # --- daftar parameter ---
        self.parameters = [
            'temperature', 'humidity', 'moisture', 'ph', 'ec', 'nitrogen',
            'phosphorus', 'potassium', 'energy', 'cps', 'activity'
        ]

        self.sparklines, self.data_series = {}, {}

        # generate layout otomatis (3 kolom per baris)
        for idx, param in enumerate(self.parameters):
            plot_item = pg.PlotWidget()
            plot_item.setTitle(param.replace('_', ' ').capitalize())
            plot_item.getPlotItem().hideAxis('bottom')
            plot_item.getPlotItem().hideAxis('left')
            plot_item.setMouseEnabled(x=False, y=False)

            curve = plot_item.plot(pen=pg.mkPen('#38BDF8', width=2))

            self.sparklines[param] = {'widget': plot_item, 'curve': curve}
            self.data_series[param] = deque(maxlen=50)

            row, col = divmod(idx, 3)
            self.sparklines_layout.addWidget(plot_item, row, col)

            # klik sparklines → tampilkan ke plot utama
            plot_item.mousePressEvent = lambda event, p=param: self.show_in_main_plot(p)

        # variabel untuk main curve
        self.current_param = None
        self.main_curve = None

    def show_in_main_plot(self, param_name):
        self.main_plot.clear()
        self.main_plot.addItem(self.crosshair_v, ignoreBounds=True)
        self.main_plot.addItem(self.crosshair_h, ignoreBounds=True)
        self.main_plot.addItem(self.label, ignoreBounds=True)
        self.main_plot.addItem(self.highlight_point)

        self.main_plot.setTitle(param_name.replace('_', ' ').capitalize(), color="#ecf0f1", size="20pt")
        self.main_plot.getPlotItem().showAxis('bottom')
        self.main_plot.getPlotItem().showAxis('left')
        self.main_plot.setLabel('left', param_name.capitalize(), color="#ecf0f1")
        self.main_plot.setLabel('bottom', "Waktu (sampel)", color="#ecf0f1")

        self.current_param = param_name
        data_y = list(self.data_series[param_name])
        data_x = list(range(len(data_y)))

        self.main_curve = self.main_plot.plot(data_x, data_y, pen=pg.mkPen('#A78BFA', width=3))
        self.main_plot.plot(data_x, data_y, fillLevel=0, fillBrush=(56, 189, 248, 80))

    def mouse_moved(self, event):
        pos = event[0]
        if self.main_plot.sceneBoundingRect().contains(pos) and self.main_curve is not None:
            mouse_point = self.main_plot.getPlotItem().vb.mapSceneToView(pos)

            x_data = np.array(self.main_curve.xData)
            y_data = np.array(self.main_curve.yData)
            if len(x_data) == 0:
                return

            idx = (np.abs(x_data - mouse_point.x())).argmin()
            closest_x, closest_y = x_data[idx], y_data[idx]

            self.crosshair_v.setPos(closest_x)
            self.crosshair_h.setPos(closest_y)
            self.label.setText(f"x={closest_x:.0f}, y={closest_y:.2f}", color="#E5E7EB")
            self.label.setPos(closest_x, closest_y)
            self.highlight_point.setData([closest_x], [closest_y])

    def update_data(self, system_id, data):
        if system_id == self.system_selector.currentText():
            for param, series in self.data_series.items():
                if param in data:
                    series.append(data[param])
                    self.sparklines[param]['curve'].setData(list(series))

    def reset_all_graphs(self):
        for param in self.parameters:
            self.data_series[param].clear()
            self.sparklines[param]['curve'].clear()
        self.main_plot.clear()
        self.current_param = None
        self.main_curve = None
