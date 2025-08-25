# file: tabs/overview_tab.py

from PyQt5.QtWidgets import QWidget, QGridLayout, QGroupBox
from custom_widgets import OverviewCard # Pastikan Anda punya OverviewCard di custom_widgets.py

class OverviewTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QGridLayout(self)
        main_layout.setSpacing(20)

        sys1_box = QGroupBox("Lisimeter 1")
        sys2_box = QGroupBox("Lisimeter 2")
        
        main_layout.addWidget(sys1_box, 0, 0)
        main_layout.addWidget(sys2_box, 0, 1)

        self.cards = {
            'Lisimeter_1': self.create_cards_for_system(sys1_box),
            'Lisimeter_2': self.create_cards_for_system(sys2_box)
        }

    def create_cards_for_system(self, parent_box):
        """Membuat dan menata kartu hibrida di dalam grupnya."""
        layout = QGridLayout(parent_box)
        layout.setSpacing(15)
        
        # Tampilkan 8 parameter utama di overview
        cards = {
            'temperature': OverviewCard("Temperature", "🌡️", " °C"),
            'humidity': OverviewCard("Humidity", "💧", " %"),
            'moisture': OverviewCard("Moisture", "🌿", " %"),
            'ph': OverviewCard("pH Level", "🧪", ""),
            'ec': OverviewCard("EC", "⚡", " µS/cm"),
            'cps': OverviewCard("CPS", "⚛️", " CPS"),
            'nitrogen': OverviewCard("Nitrogen", "🌱", " mg/kg"),
            'potassium': OverviewCard("Potassium", "🌱", " mg/kg")
        }
        
        # Susun kartu dalam grid 4 baris x 2 kolom yang rapi
        positions = [(i, j) for i in range(4) for j in range(2)]
        for (param, card), pos in zip(cards.items(), positions):
            layout.addWidget(card, pos[0], pos[1])
        
        return cards

    def update_data(self, system_id, data, thresholds):
        """Memperbarui nilai dan status visual semua kartu."""
        target_cards = self.cards[system_id]
        
        for param, card_widget in target_cards.items():
            if param in data:
                value = data[param]
                status = "normal"
                
                if param == 'temperature':
                    if value > thresholds.get('temp_danger', 999): status = "danger"
                    elif value > thresholds.get('temp_warn', 999): status = "warning"
                elif param == 'moisture':
                    if value < thresholds.get('moisture_danger', 0): status = "danger"
                    elif value < thresholds.get('moisture_warn', 0): status = "warning"
                elif param == 'cps':
                    if value > thresholds.get('cps_danger', 9999): status = "danger"
                    elif value > thresholds.get('cps_warn', 9999): status = "warning"

                card_widget.set_status(status)
                card_widget.update_data(value)