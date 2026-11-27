import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class MuscleVisualizer(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=10, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        
        # Setup Dual Panes
        self.ax_fv = self.fig.add_subplot(121)
        self.ax_sarc = self.fig.add_subplot(122)
        self.ax_power = self.ax_fv.twinx()
        
        super().__init__(self.fig)

    def update_plot(self, model, params, v_op, show_power=True):
        self.ax_fv.clear()
        self.ax_power.clear()
        self.ax_sarc.clear()

        F0 = params['F0']
        v_max = model.get_vmax(params)
        
        # Generate F-v domain array
        v_arr = np.linspace(0, max(v_max, 1), 200)
        F_arr = model.evaluate_force(v_arr, params)
        
        # 1. Plot Force-Velocity Curve
        self.ax_fv.plot(v_arr, F_arr, 'b-', linewidth=2, label='F-v Curve')
        self.ax_fv.set_xlabel('Shortening Velocity (mm/s)')
        self.ax_fv.set_ylabel('Force (N)', color='b')
        self.ax_fv.tick_params(axis='y', labelcolor='b')
        self.ax_fv.set_xlim(0, max(v_max * 1.1, 1))
        self.ax_fv.set_ylim(0, max(F0 * 1.1, 1))
        self.ax_fv.grid(True, linestyle='--', alpha=0.6)

        # Plot Operating Point
        F_op = model.evaluate_force(np.array([v_op]), params)[0]
        self.ax_fv.plot(v_op, F_op, 'ro', markersize=9, zorder=5, label='Operating Point')
        
        # 2. Plot Power Overlay
        if show_power:
            P_arr = F_arr * v_arr
            self.ax_power.plot(v_arr, P_arr, 'g--', linewidth=2, alpha=0.7, label='Power')
            self.ax_power.set_ylabel('Power (N·mm/s or mW)', color='g')
            self.ax_power.tick_params(axis='y', labelcolor='g')
            max_P = np.max(P_arr) if len(P_arr) > 0 else 1
            self.ax_power.set_ylim(0, max(max_P * 1.1, 1))
        else:
            self.ax_power.set_yticks([])

        self.ax_fv.set_title('Dynamics: Force-Velocity & Power')

        # 3. Dynamic 2D Sarcomere Model
        # Visual length shrinks as velocity approaches Vmax to signify active shortening
        contraction_ratio = v_op / v_max if v_max > 0 else 0
        sarc_length = 3.0 - (1.5 * contraction_ratio)
        
        self._draw_sarcomere(self.ax_sarc, sarc_length, F_op, F0)
        
        self.ax_sarc.set_title('Mechanical Schematic (Sarcomere)')
        self.ax_sarc.set_xlim(-2.0, 2.0)
        self.ax_sarc.set_ylim(-1, 1)
        self.ax_sarc.axis('off')

        self.fig.tight_layout()
        self.draw()

    def _draw_sarcomere(self, ax, length, F_op, F0):
        """Draws a stylized sarcomere where length reacts to velocity, and thickness to force."""
        half_L = length / 2.0
        
        # Draw Z-discs (bounds)
        ax.plot([-half_L, -half_L], [-0.5, 0.5], 'k-', lw=4)
        ax.plot([half_L, half_L], [-0.5, 0.5], 'k-', lw=4)
        
        # Draw Actin (thin filaments attached to Z-discs)
        actin_len = 1.0
        y_offsets = [-0.3, -0.1, 0.1, 0.3]
        for y in y_offsets:
            ax.plot([-half_L, -half_L + actin_len], [y, y], 'r-', lw=2)  # Left
            ax.plot([half_L, half_L - actin_len], [y, y], 'r-', lw=2)    # Right
        
        # Draw Myosin (thick central filaments)
        myo_half = 0.8
        myo_y = [-0.2, 0.0, 0.2]
        
        # Morphing visual: High force makes the central bellies visually thicker
        force_ratio = F_op / F0 if F0 > 0 else 0
        myo_lw = 3 + 7 * force_ratio

        for y in myo_y:
            ax.plot([-myo_half, myo_half], [y, y], 'b-', lw=myo_lw)
            # Cross-bridge indicators
            ax.plot([-myo_half, -myo_half + 0.15], [y, y + 0.1], 'b-', lw=1.5)
            ax.plot([myo_half, myo_half - 0.15], [y, y + 0.1], 'b-', lw=1.5)