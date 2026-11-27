import sys
import os
import numpy as np

# TODO:
# Make it prettier

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QSlider, QDoubleSpinBox, 
                             QCheckBox, QGroupBox, QFormLayout, QGridLayout,
                             QRadioButton, QButtonGroup)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPalette
from model import ClassicalHillModel, CONDITION_PRESETS
from visualizer import MuscleVisualizer, ArmVisualizer

class MuscleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Hill-Type Muscle Contraction Simulator")
        self.resize(1150, 780)
        
        self.model = ClassicalHillModel()
        self._updating_preset = False
        
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)
        
        self.setup_ui()
        self.update_simulation()
        
    def setup_ui(self):
        # 1. Left Panel (Controls)
        self.control_panel = QVBoxLayout()

        # 1a. Muscle Condition Presets (above Hill Parameters & Controls)
        self.group_condition = QGroupBox("Muscle Condition")
        condition_layout = QHBoxLayout()
        self.condition_group = QButtonGroup(self)
        self.condition_radios = {}

        for key, preset in CONDITION_PRESETS.items():
            radio = QRadioButton(preset["label"])
            radio.setToolTip(preset["tooltip"])
            self.condition_group.addButton(radio)
            condition_layout.addWidget(radio)
            self.condition_radios[key] = radio

        self.condition_radios["average"].setChecked(True)
        self.group_condition.setLayout(condition_layout)
        self.control_panel.addWidget(self.group_condition)

        # 1b. Hill Parameters & Controls
        self.group_params = QGroupBox("Hill Parameters && Controls")
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
                if not self._updating_preset:
                    self.update_simulation()

            slider.valueChanged.connect(on_slider_changed)
            spin.valueChanged.connect(on_spin_changed)

            hl = QHBoxLayout()
            hl.addWidget(slider)
            hl.addWidget(spin)
            return spin, slider, hl

        default_preset = CONDITION_PRESETS["average"]
        self.spin_F0, self.slider_F0, hl_F0 = create_control(10.0, 500.0, default_preset["F0"], step=1.0, decimals=1)
        self.spin_Vmax, self.slider_Vmax, hl_Vmax = create_control(10.0, 500.0, default_preset["Vmax"], step=1.0, decimals=1)
        self.spin_k, self.slider_k, hl_k = create_control(0.05, 1.00, default_preset["k"], step=0.01, decimals=2)

        for key, radio in self.condition_radios.items():
            radio.toggled.connect(lambda checked, k=key: self.apply_condition(k) if checked else None)
            radio.clicked.connect(lambda _checked=False, k=key: self._reapply_if_modified(k))

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
        
        self.group_params.setLayout(form_params)
        self.control_panel.addWidget(self.group_params)
        
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
        self.control_panel.addWidget(group_readouts)

        # 3. Whole-muscle graphic, under the controls and readouts
        self.arm_canvas = ArmVisualizer(self, width=4.2, height=3.6)
        self.arm_canvas.setMinimumHeight(300)
        self.control_panel.addWidget(self.arm_canvas, 1)

        # 4. Right Panel: F-v graph with the sarcomere schematic underneath
        self.canvas = MuscleVisualizer(self, width=7, height=7)
        
        self.layout.addLayout(self.control_panel, 1)
        self.layout.addWidget(self.canvas, 2)

    def apply_condition(self, condition_key):
        """Sets the Hill parameter controls to the default values for a muscle condition."""
        preset = CONDITION_PRESETS[condition_key]
        self._updating_preset = True
        try:
            self.spin_F0.setValue(preset["F0"])
            self.spin_Vmax.setValue(preset["Vmax"])
            self.spin_k.setValue(preset["k"])
        finally:
            self._updating_preset = False
        self.update_simulation()

    def _reapply_if_modified(self, condition_key):
        """Resets sliders if the user re-clicks the already selected condition after manual edits."""
        preset = CONDITION_PRESETS[condition_key]
        if not (
            np.isclose(self.spin_F0.value(), preset["F0"])
            and np.isclose(self.spin_Vmax.value(), preset["Vmax"])
            and np.isclose(self.spin_k.value(), preset["k"])
        ):
            self.apply_condition(condition_key)
        
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