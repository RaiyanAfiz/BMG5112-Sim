import sys
import os
import numpy as np

# TODO: 
# Add Sliders: V_max, k, f0
# a & b are derived 
# Have Radio buttons for different conditions
# Make it prettier 

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, 
                             QCheckBox, QGroupBox, QFormLayout, QGridLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from model import ClassicalHillModel
from visualizer import MuscleVisualizer, ArmVisualizer

class MuscleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hill-Type Muscle Contraction Simulator")
        self.resize(1150, 780)
        
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
        
        # Helper to create linked Slider + SpinBox
        def create_control(min_v, max_v, default):
            spin = QDoubleSpinBox()
            spin.setRange(min_v, max_v)
            spin.setValue(default)
            spin.setDecimals(1)
            
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(int(min_v), int(max_v))
            slider.setValue(int(default))
            
            # Sync bindings without infinite loops
            slider.valueChanged.connect(lambda v: spin.setValue(float(v)))
            spin.valueChanged.connect(lambda v: slider.setValue(int(v)) if slider.value() != int(v) else None)
            spin.valueChanged.connect(self.update_simulation)
            
            hl = QHBoxLayout()
            hl.addWidget(slider)
            hl.addWidget(spin)
            return spin, slider, hl

        self.spin_F0, _, hl_F0 = create_control(10, 500, 100)
        self.spin_a, _, hl_a = create_control(1, 100, 25)
        self.spin_b, _, hl_b = create_control(1, 150, 40)
        
        # Velocity operating point is bound to a percentage (0-100%) to safely scale when Vmax changes
        self.spin_v, _, hl_v = create_control(0, 100, 20)
        self.spin_v.setSuffix(" % of Vmax")
        
        self.check_power = QCheckBox("Overlay Mechanical Power")
        self.check_power.setChecked(True)
        self.check_power.stateChanged.connect(self.update_simulation)
        
        form_params.addRow("Isometric Force (F0) [N]:", hl_F0)
        form_params.addRow("Force Asymptote (a) [N]:", hl_a)
        form_params.addRow("Velocity Asymptote (b) [mm/s]:", hl_b)
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

        # 3. Whole-muscle graphic, under the controls and readouts
        self.arm_canvas = ArmVisualizer(self, width=4.2, height=3.6)
        self.arm_canvas.setMinimumHeight(300)
        control_panel.addWidget(self.arm_canvas, 1)

        # 4. Right Panel: F-v graph with the sarcomere schematic underneath
        self.canvas = MuscleVisualizer(self, width=7, height=7)
        
        self.layout.addLayout(control_panel, 1)
        self.layout.addWidget(self.canvas, 2)
        
    def update_simulation(self):
        """Gathers parameters, evaluates model, updates readouts and plots."""
        params = {
            'F0': self.spin_F0.value(),
            'a': self.spin_a.value(),
            'b': self.spin_b.value()
        }
        
        v_max = self.model.get_vmax(params)
        v_op = (self.spin_v.value() / 100.0) * v_max
        
        F_op = self.model.evaluate_force(np.array([v_op]), params)[0]
        P_op = F_op * v_op
        ratio = params['a'] / params['F0'] if params['F0'] > 0 else 0
        
        # Update text readouts
        self.lbl_vmax.setText(f"V_max: {v_max:.1f} mm/s")
        self.lbl_ratio.setText(f"Curvature (a/F0): {ratio:.3f}")
        self.lbl_F.setText(f"Force (F): {F_op:.1f} N")
        self.lbl_v.setText(f"Velocity (v): {v_op:.1f} mm/s")
        self.lbl_P.setText(f"Power (P): {P_op:.1f} mW")
        
        # Trigger canvas redraw
        self.canvas.update_plot(self.model, params, v_op, self.check_power.isChecked())
        contraction_ratio = v_op / v_max if v_max > 0 else 0
        self.arm_canvas.update_plot(contraction_ratio, F_op, params['F0'], v_op)

def apply_light_theme(app):
    """Force a light theme regardless of the OS dark-mode setting."""
    # Qt 6.8+: tell Qt (and the Windows title bar) to use the light scheme
    hints = app.styleHints()
    if hasattr(hints, "setColorScheme"):
        hints.setColorScheme(Qt.ColorScheme.Light)

    # Fusion style respects our palette on every OS
    app.setStyle("Fusion")

    white = QColor(255, 255, 255)
    black = QColor(0, 0, 0)
    light_gray = QColor(240, 240, 240)

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, white)
    palette.setColor(QPalette.ColorRole.WindowText, black)
    palette.setColor(QPalette.ColorRole.Base, white)
    palette.setColor(QPalette.ColorRole.AlternateBase, light_gray)
    palette.setColor(QPalette.ColorRole.Text, black)
    palette.setColor(QPalette.ColorRole.Button, light_gray)
    palette.setColor(QPalette.ColorRole.ButtonText, black)
    palette.setColor(QPalette.ColorRole.ToolTipBase, white)
    palette.setColor(QPalette.ColorRole.ToolTipText, black)
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(120, 120, 120))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(0, 120, 215))
    palette.setColor(QPalette.ColorRole.HighlightedText, white)
    app.setPalette(palette)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    apply_light_theme(app)
    window = MuscleApp()
    window.show()
    sys.exit(app.exec())