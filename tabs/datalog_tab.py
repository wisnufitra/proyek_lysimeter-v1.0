# file: tabs/datalog_tab.py

import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QTableWidget, QPushButton, QComboBox, QFileDialog,
                             QTableWidgetItem, QHeaderView, QDateTimeEdit, QMessageBox)
from PyQt5.QtCore import QDateTime

class DataLogTab(QWidget):
    """Tab untuk menampilkan semua data historis dan mengekspornya."""
    def __init__(self, data_file):
        super().__init__()
        self.data_file = data_file
        self.df = pd.DataFrame()
        self.initUI()
    
    def initUI(self):
        main_layout = QVBoxLayout(self)
        
        control_panel = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tampilkan Semua", "Lisimeter_1", "Lisimeter_2"])
        self.filter_combo.currentTextChanged.connect(self.load_data)
        
        refresh_btn = QPushButton("🔄 Muat Ulang Data")
        refresh_btn.clicked.connect(self.load_data)
        
        control_panel.addWidget(QLabel("Filter:"))
        control_panel.addWidget(self.filter_combo)
        control_panel.addWidget(refresh_btn)
        control_panel.addStretch()
        
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        export_box = QGroupBox("Modul Ekspor Lanjutan")
        export_layout = QHBoxLayout(export_box)
        
        self.start_dt_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.end_dt_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_dt_edit.setCalendarPopup(True)
        self.end_dt_edit.setCalendarPopup(True)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["Excel (*.xlsx)", "CSV (*.csv)"])
        
        export_btn = QPushButton("🚀 Ekspor Data")
        export_btn.clicked.connect(self.export_data)
        
        export_layout.addWidget(QLabel("Dari:"))
        export_layout.addWidget(self.start_dt_edit)
        export_layout.addWidget(QLabel("Hingga:"))
        export_layout.addWidget(self.end_dt_edit)
        export_layout.addStretch()
        export_layout.addWidget(QLabel("Format:"))
        export_layout.addWidget(self.format_combo)
        export_layout.addWidget(export_btn)
        
        main_layout.addLayout(control_panel)
        main_layout.addWidget(self.table)
        main_layout.addWidget(export_box)
        
        self.load_data()

    def load_data(self):
        """Memuat data dari file CSV ke dalam tabel, menerapkan filter."""
        try:
            self.df = pd.read_csv(self.data_file, parse_dates=['timestamp'])
            filter_text = self.filter_combo.currentText()
            
            if "Lisimeter" in filter_text:
                display_df = self.df[self.df['system_id'] == filter_text].tail(2000)
            else:
                display_df = self.df.tail(2000)
            
            self.table.setRowCount(len(display_df))
            self.table.setColumnCount(len(display_df.columns))
            self.table.setHorizontalHeaderLabels(display_df.columns)
            
            for i, row in enumerate(display_df.itertuples(index=False)):
                for j, val in enumerate(row):
                    self.table.setItem(i, j, QTableWidgetItem(str(val)))
        except FileNotFoundError:
            self.table.clear()

    def export_data(self):
        """Mengekspor data berdasarkan rentang waktu dan format."""
        if self.df.empty: return
        start_dt = self.start_dt_edit.dateTime().toPyDateTime()
        end_dt = self.end_dt_edit.dateTime().toPyDateTime()
        
        export_df = self.df[(self.df['timestamp'] >= start_dt) & (self.df['timestamp'] <= end_dt)]
        
        if export_df.empty:
            QMessageBox.information(self, "Info", "Tidak ada data pada rentang waktu ini.")
            return
            
        file_format = self.format_combo.currentText()
        suffix = ".xlsx" if "Excel" in file_format else ".csv"
        file_filter = f"Files (*{suffix})"
            
        default_name = f"export_{start_dt.strftime('%Y%m%d')}_{end_dt.strftime('%Y%m%d')}{suffix}"
        filename, _ = QFileDialog.getSaveFileName(self, "Simpan File", default_name, file_filter)
        
        if filename:
            try:
                if suffix == ".xlsx":
                    export_df.to_excel(filename, index=False)
                else:
                    export_df.to_csv(filename, index=False)
                QMessageBox.information(self, "Sukses", f"Data berhasil diekspor ke {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Gagal mengekspor: {e}")