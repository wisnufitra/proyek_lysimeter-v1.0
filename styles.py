# file: styles.py

# 🎨 Palet Warna Dark
DARK_PALETTE = {
    "bg_main": "#1F2937",      # biru gelap pekat
    "bg_secondary": "#374151", # abu gelap
    "accent": "#38BDF8",       # biru terang
    "accent2": "#A78BFA",      # ungu lavender
    "text": "#E5E7EB",         # abu terang
    "text_secondary": "#9CA3AF",
    "danger": "#F43F5E",       # merah muda terang
    "warning": "#FBBF24",      # kuning amber
    "success": "#34D399",      # hijau terang
    "border": "#4B5563"
}

# 🎨 Palet Warna Light
LIGHT_PALETTE = {
    "bg_main": "#F9FAFB",      # putih abu terang
    "bg_secondary": "#E5E7EB",
    "accent": "#2563EB",       # biru terang
    "accent2": "#9333EA",      # ungu terang
    "text": "#111827",         # hampir hitam
    "text_secondary": "#374151",
    "danger": "#DC2626",       # merah
    "warning": "#F59E0B",      # amber
    "success": "#059669",      # hijau emerald
    "border": "#D1D5DB"
}


def build_stylesheet(palette):
    """
    Membuat stylesheet berbasis palet warna yang diberikan.
    """
    return f"""
    QWidget {{
        background-color: {palette['bg_main']};
        color: {palette['text']};
        font-family: "Poppins";
        font-size: 14px;
    }}
    QMainWindow {{
        background-color: {palette['bg_main']};
    }}

    /* --- Kartu Parameter --- */
    QWidget#ParameterCard {{
        background-color: {palette['bg_secondary']};
        border-radius: 10px;
        border: 1px solid {palette['border']};
    }}
    QWidget#ParameterCard[status="warning"] {{ border: 2px solid {palette['warning']}; }}
    QWidget#ParameterCard[status="danger"]  {{ border: 2px solid {palette['danger']}; }}
    
    QLabel#cardTitle {{ font-size: 13px; color: {palette['text_secondary']}; font-weight: normal; }}
    QLabel#cardIcon  {{ font-size: 15px; }}
    QLabel#cardValue {{ font-size: 26px; font-weight: bold; color: {palette['text']}; }}

    /* --- Sistem Tab --- */
    QTabWidget::pane {{ border-top: 3px solid {palette['accent']}; }}
    QTabBar::tab {{
        padding: 10px 24px; background: transparent; border: none;
        border-top-left-radius: 6px; border-top-right-radius: 6px;
        color: {palette['text_secondary']}; font-weight: bold;
    }}
    QTabBar::tab:hover {{ background: {palette['bg_secondary']}; color: {palette['text']}; }}
    QTabBar::tab:selected {{ background: {palette['accent']}; color: {palette['bg_main']}; }}

    /* --- Tombol & Kontrol Interaktif --- */
    QPushButton {{
        background-color: {palette['accent']}; color: {palette['bg_main']};
        font-weight: bold; border: none;
        padding: 8px 16px; font-size: 14px; border-radius: 6px;
    }}
    QPushButton:hover {{ background-color: {palette['accent2']}; color: {palette['text']}; }}
    QPushButton:disabled {{ background-color: {palette['border']}; color: {palette['text_secondary']}; }}
    
    QComboBox, QDoubleSpinBox, QSpinBox, QDateTimeEdit {{
        padding: 6px; font-size: 14px;
        background-color: {palette['bg_secondary']};
        border: 1px solid {palette['border']}; border-radius: 5px;
    }}
    QComboBox::drop-down {{ border: none; }}

    /* --- Tabel & Scrollbar --- */
    QTableWidget {{ background-color: {palette['bg_secondary']}; gridline-color: {palette['border']}; }}
    QHeaderView::section {{
        background-color: {palette['bg_main']}; color: {palette['text_secondary']}; font-weight: bold;
        padding: 6px; border: 1px solid {palette['border']};
    }}
    QScrollBar:vertical {{ border: none; background: {palette['bg_main']}; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {palette['border']}; min-height: 20px; border-radius: 5px; }}
    QScrollBar::handle:vertical:hover {{ background: {palette['accent']}; }}
    
    /* --- GroupBox --- */
    QGroupBox {{
        border: 1px solid {palette['border']}; border-radius: 5px;
        margin-top: 10px; font-size: 14px; font-weight: bold;
    }}
    QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; padding: 0 6px; }}

    /* --- StatusBar & Splitter --- */
    QStatusBar {{ font-size: 12px; }}
    QSplitter::handle {{ background-color: {palette['border']}; }}
    QSplitter::handle:hover {{ background-color: {palette['accent']}; }}

    /* --- Panel Kesehatan Sistem --- */
    QWidget#HealthStatusWidget QLabel {{ font-size: 14px; font-weight: bold; }}
    QWidget#HealthStatusWidget[status="disconnected"] QLabel {{ color: {palette['text_secondary']}; }}
    QWidget#HealthStatusWidget[status="connected"] QLabel    {{ color: {palette['success']}; }}
    QWidget#HealthStatusWidget[status="warning"] QLabel      {{ color: {palette['warning']}; }}
    QWidget#HealthStatusWidget[status="danger"] QLabel       {{ color: {palette['danger']}; }}
    """


# 🎨 Export dua tema siap pakai
DARK_STYLE = build_stylesheet(DARK_PALETTE)
LIGHT_STYLE = build_stylesheet(LIGHT_PALETTE)
