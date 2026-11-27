import sys
import os
import numpy as np

# TODO:
# Have Radio buttons for different conditions
# Make it prettier

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, 
                             QCheckBox, QGroupBox, QFormLayout, QGridLayout)
from PyQt6.QtCore import Qt
from model import ClassicalHillModel
from visualizer import MuscleVisualizer

class MuscleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hill-Type Muscle Contraction Simulator")
        self.resize(1200, 650)
        
        self.model = ClassicalHillModel()
        
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)
        
        self.setup_ui()
        self.update_simulation()
        
    def setup_ui(self):
        # 1. Left Panel (Controls)
        control_panel = QVBoxLayout()
        group_params = QGroupBox("Hill Parameters & Controls")
        form_params = QFormLayout()
        
        # Helper to create linked Slider + SpinBox (supports fractional steps)
        def create_control(min_v, max_v, default, step=1.0, decimals=1):
            spin = QDoubleSpinBox()
            spin.setRange(min_v, max_v)
            spin.setDecimals(decimals)
            spin.setSingleStep(step)
            spin.setValue(default)

            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(int(round(min_v / step)), int(round(max_v / step)))
            slider.setValue(int(round(default / step)))

            def on_slider_changed(tick):
                val = round(tick * step, decimals)
                if not np.isclose(spin.value(), val):
                    spin.setValue(val)

            def on_spin_changed(val):
                tick = int(round(val / step))
                if slider.value() != tick:
                    slider.blockSignals(True)
                    slider.setValue(tick)
                    slider.blockSignals(False)
                self.update_simulation()

            slider.valueChanged.connect(on_slider_changed)
            spin.valueChanged.connect(on_spin_changed)

            hl = QHBoxLayout()
            hl.addWidget(slider)
            hl.addWidget(spin)
            return spin, slider, hl

        self.spin_F0, self.slider_F0, hl_F0 = create_control(10.0, 500.0, 100.0, step=1.0, decimals=1)
        self.spin_Vmax, self.slider_Vmax, hl_Vmax = create_control(10.0, 500.0, 160.0, step=1.0, decimals=1)
        self.spin_k, self.slider_k, hl_k = create_control(0.05, 1.00, 0.25, step=0.01, decimals=2)

        # Velocity operating point is bound to a percentage (0-100%) to safely scale when Vmax changes
        self.spin_v, self.slider_v, hl_v = create_control(0.0, 100.0, 20.0, step=1.0, decimals=1)
        self.spin_v.setSuffix(" % of Vmax")

        self.check_power = QCheckBox("Overlay Mechanical Power")
        self.check_power.setChecked(True)
        self.check_power.stateChanged.connect(self.update_simulation)

        form_params.addRow("Isometric Force (F0) [N]:", hl_F0)
        form_params.addRow("Max Shortening Velocity (Vmax) [mm/s]:", hl_Vmax)
        form_params.addRow("Curvature Constant (k = a/F0):", hl_k)
        form_params.addRow("Operating Velocity (v):", hl_v)
        form_params.addRow("", self.check_power)
        
        group_params.setLayout(form_params)
        control_panel.addWidget(group_params)
        
        # 2. Live Readouts Group
        group_readouts = QGroupBox("Instantaneous Mechanics Readout")
        layout_readouts = QGridLayout()
        
        self.lbl_vmax = QLabel()
        self.lbl_F = QLabel()
        self.lbl_v = QLabel()
        self.lbl_P = QLabel()
        self.lbl_ratio = QLabel()
        
        for lbl in (self.lbl_vmax, self.lbl_F, self.lbl_v, self.lbl_P, self.lbl_ratio):
            lbl.setStyleSheet("font-weight: bold; color: #333; font-size: 14px;")
            
        layout_readouts.addWidget(self.lbl_vmax, 0, 0)
        layout_readouts.addWidget(self.lbl_ratio, 0, 1)
        layout_readouts.addWidget(self.lbl_F, 1, 0)
        layout_readouts.addWidget(self.lbl_v, 1, 1)
        layout_readouts.addWidget(self.lbl_P, 2, 0, 1, 2)
        
        group_readouts.setLayout(layout_readouts)
        control_panel.addWidget(group_readouts)
        control_panel.addStretch()
        
        # 3. Right Panel (Matplotlib Canvas)
        self.canvas = MuscleVisualizer(self, width=8, height=5)
        
        self.layout.addLayout(control_panel, 1)
        self.layout.addWidget(self.canvas, 2)
        
    def update_simulation(self):
        """Gathers parameters, evaluates model, updates readouts and plots."""
        params = {
            'F0': self.spin_F0.value(),
            'Vmax': self.spin_Vmax.value(),
            'k': self.spin_k.value()
        }

        v_max = self.model.get_vmax(params)
        v_op = (self.spin_v.value() / 100.0) * v_max

        F_op = self.model.evaluate_force(np.array([v_op]), params)[0]
        P_op = F_op * v_op

        # Update text readouts (a and b remain derived internally)
        self.lbl_vmax.setText(f"V_max: {v_max:.1f} mm/s")
        self.lbl_ratio.setText(f"Curvature (k): {params['k']:.2f}")
        self.lbl_F.setText(f"Force (F): {F_op:.1f} N")
        self.lbl_v.setText(f"Velocity (v): {v_op:.1f} mm/s")
        self.lbl_P.setText(f"Power (P): {P_op:.1f} mW")

        # Trigger canvas redraw
        self.canvas.update_plot(self.model, params, v_op, self.check_power.isChecked())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MuscleApp()
    window.show()
    sys.exit(app.exec())