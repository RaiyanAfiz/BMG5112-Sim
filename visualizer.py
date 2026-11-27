import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, Polygon

class MuscleVisualizer(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=10, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        
        # Layout: F-v curve (top) above the sarcomere schematic (bottom).
        # Fixed margins (no tight_layout on each redraw, which made the panels
        # shrink a little more every time a slider moved).
        gs = self.fig.add_gridspec(2, 1, height_ratios=[1.2, 1.0],
                                   left=0.10, right=0.89, bottom=0.02, top=0.95,
                                   hspace=0.28)
        self.ax_fv = self.fig.add_subplot(gs[0, 0])
        self.ax_sarc = self.fig.add_subplot(gs[1, 0])
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
        # clear() on a twin axis resets its label/ticks to the left side; put them back
        self.ax_power.yaxis.tick_right()
        self.ax_power.yaxis.set_label_position('right')
        if show_power:
            P_arr = F_arr * v_arr
            self.ax_power.plot(v_arr, P_arr, 'g--', linewidth=2, alpha=0.7, label='Power')
            self.ax_power.set_ylabel('Power (N·mm/s or mW)', color='g')
            self.ax_power.tick_params(axis='y', labelcolor='g')
            max_P = np.max(P_arr) if len(P_arr) > 0 else 1
            self.ax_power.set_ylim(0, max(max_P * 1.1, 1))
        else:
            self.ax_power.set_yticks([])
            self.ax_power.set_ylabel('')

        self.ax_fv.set_title('Dynamics: Force-Velocity & Power')

        # 3. Dynamic 2D Sarcomere Model
        # Visual length shrinks as velocity approaches Vmax to signify active shortening
        contraction_ratio = v_op / v_max if v_max > 0 else 0
        sarc_length = 3.0 - (1.2 * contraction_ratio)
        
        self._draw_sarcomere(self.ax_sarc, sarc_length, F_op, F0)
        
        self.ax_sarc.set_title('Mechanical Schematic (Sarcomere)')
        self.ax_sarc.set_xlim(-2.0, 2.0)
        self.ax_sarc.set_ylim(-1.3, 0.62)
        self.ax_sarc.axis('off')
        self._add_sarcomere_legend(self.ax_sarc)

        self.draw()

    def _add_sarcomere_legend(self, ax):
        """Legend below the sarcomere schematic, built from stand-in line samples."""
        handles = [
            Line2D([], [], color='k', lw=4, label='Z-disc'),
            Line2D([], [], color='r', lw=2, label='Actin (thin filament)'),
            Line2D([], [], color='b', lw=5, label='Myosin (thick filament)'),
            Line2D([], [], color='darkorange', lw=2, marker='o', markersize=4,
                   label='Myosin head (bound)'),
            Line2D([], [], color='gray', lw=1.5, alpha=0.7, label='Myosin head (free)'),
        ]
        # Kept inside the (axis-off) panel's bottom strip so it never spills out
        ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, 0.0),
                  ncol=3, frameon=False, fontsize=8, handlelength=1.5, columnspacing=1.0)

    def _draw_sarcomere(self, ax, length, F_op, F0):
        """Draws a stylized sarcomere where length reacts to velocity, and thickness to force."""
        half_L = length / 2.0
        
        # Draw Z-discs (bounds)
        ax.plot([-half_L, -half_L], [-0.5, 0.5], 'k-', lw=4)
        ax.plot([half_L, half_L], [-0.5, 0.5], 'k-', lw=4)
        
        # Draw Actin (thin filaments attached to Z-discs)
        actin_len = 0.9
        y_offsets = [-0.3, -0.1, 0.1, 0.3]
        for y in y_offsets:
            ax.plot([-half_L, -half_L + actin_len], [y, y], 'r-', lw=2)  # Left
            ax.plot([half_L, half_L - actin_len], [y, y], 'r-', lw=2)    # Right
        
        # Draw Myosin (thick central filaments)
        myo_half = 0.8
        myo_y = [-0.2, 0.0, 0.2]
        
        # Morphing visual: High force makes the central bellies visually thicker
        force_ratio = F_op / F0 if F0 > 0 else 0
        myo_lw = 2 + 5 * force_ratio

        for y in myo_y:
            ax.plot([-myo_half, myo_half], [y, y], 'b-', lw=myo_lw, zorder=2)

        self._draw_myosin_heads(ax, half_L, actin_len, myo_half, myo_y, force_ratio)

    def _draw_myosin_heads(self, ax, half_L, actin_len, myo_half, myo_y, bound_fraction):
        """
        Draws myosin heads (cross-bridges) on each thick filament.
        A head can only bind where the thick filament overlaps actin. Of those,
        the fraction bound equals F/F0: attached cross-bridges generate the force,
        so the faster the muscle shortens, the fewer heads stay bound.
        """
        heads_per_half = 6
        bare_zone = 0.15            # central M-line region has no heads
        head_reach = 0.1            # vertical gap between myosin and actin rows
        x_left = np.linspace(-myo_half, -bare_zone, heads_per_half)
        head_x = np.concatenate([x_left, -x_left[::-1]])

        # Fixed per-head thresholds so the same heads stay bound between redraws
        # (no flicker); a head binds when its threshold < bound_fraction.
        n_rows = len(myo_y) * 2     # each thick filament has heads above and below
        thresholds = np.random.default_rng(42).random((n_rows, head_x.size))

        bound_segs, free_segs = [], []
        n_bound, n_available = 0, 0
        for i, y in enumerate(myo_y):
            for j, side in enumerate((1, -1)):          # 1 = up, -1 = down
                row = thresholds[2 * i + j]
                for k, x in enumerate(head_x):
                    tilt = -1 if x < 0 else 1           # heads lean toward their Z-disc
                    # Is there actin above/below this head to grab?
                    overlaps = (-half_L <= x <= -half_L + actin_len) or \
                               (half_L - actin_len <= x <= half_L)
                    y0 = y + side * 0.03
                    if overlaps:
                        n_available += 1
                    if overlaps and row[k] < bound_fraction:
                        n_bound += 1
                        bound_segs.append([(x, y0), (x + tilt * 0.06, y + side * head_reach)])
                    else:
                        free_segs.append([(x, y0), (x + tilt * 0.04, y + side * 0.055)])

        if bound_segs:
            ax.add_collection(LineCollection(bound_segs, colors='darkorange', linewidths=2, zorder=3))
            tips = np.array([seg[1] for seg in bound_segs])
            ax.plot(tips[:, 0], tips[:, 1], 'o', color='darkorange', markersize=4, zorder=4)
        if free_segs:
            ax.add_collection(LineCollection(free_segs, colors='gray', linewidths=1.5, alpha=0.7, zorder=3))

        ax.text(0, -0.68, f"Bound cross-bridges: {n_bound} / {n_available} in overlap zone",
                ha='center', va='center', fontsize=10)


class ArmVisualizer(FigureCanvasQTAgg):
    """Whole-muscle view: an elbow flexor lifting a load at the current operating point."""

    def __init__(self, parent=None, width=4.2, height=3.6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.92)
        super().__init__(self.fig)

    def update_plot(self, contraction_ratio, F_op, F0, v_op):
        self.ax.clear()
        self._draw_arm(self.ax, contraction_ratio, F_op, F0, v_op)
        self.draw()

    # ------------------------------------------------------------------
    # Whole-muscle (arm) schematic
    # ------------------------------------------------------------------
    # Geometry in arbitrary units; the elbow joint sits at the origin.
    _SHOULDER = np.array([0.0, 1.0])
    _ELBOW = np.array([0.0, 0.0])
    _FOREARM_LEN = 0.95
    _MAX_FLEXION_DEG = 60.0     # extra elbow flexion (above horizontal) at v = Vmax
    _ORIGIN_OFFSET = np.array([0.07, -0.12])   # muscle origin, relative to shoulder
    _INSERTION_DIST = 0.20      # insertion distance along forearm from elbow
    _INSERTION_LIFT = 0.05      # insertion sits on the top surface of the forearm
    _TENDON_ORIGIN = 0.10
    _TENDON_INSERTION = 0.08
    _BELLY_HALF_WIDTH = 0.09    # belly half-width at resting length

    def _muscle_endpoints(self, alpha):
        """Origin and insertion of the muscle for a forearm angle alpha (rad above horizontal)."""
        u = np.array([np.cos(alpha), np.sin(alpha)])    # along the forearm
        n = np.array([-np.sin(alpha), np.cos(alpha)])   # forearm's upper surface normal
        origin = self._SHOULDER + self._ORIGIN_OFFSET
        insertion = self._ELBOW + self._INSERTION_DIST * u + self._INSERTION_LIFT * n
        return origin, insertion

    def _draw_arm(self, ax, contraction_ratio, F_op, F0, v_op):
        """
        Elbow flexor lifting a load, driven by the current operating point.
          - Tension in the muscle = load in the hand = F (steady shortening, as in
            Hill's afterloaded experiments), so the weight's size scales with F/F0.
          - Muscle colour intensity scales with F/F0 (force output).
          - Elbow flexion uses the same v/Vmax ratio as the sarcomere panel, so the
            whole muscle shortens and bulges exactly when the sarcomere shortens.
          - The belly keeps constant volume: width ~ 1/sqrt(length).
        """
        force_ratio = float(np.clip(F_op / F0, 0.0, 1.0)) if F0 > 0 else 0.0
        r = float(np.clip(contraction_ratio, 0.0, 1.0))

        alpha = np.radians(self._MAX_FLEXION_DEG * r)
        u = np.array([np.cos(alpha), np.sin(alpha)])
        elbow = self._ELBOW
        hand = elbow + self._FOREARM_LEN * u

        # --- Bones (outline + fill) and elbow joint ---
        bone_fill, bone_edge = '#f3ead8', '#5a4a3a'
        for p, q in ((self._SHOULDER, elbow), (elbow, hand)):
            ax.plot([p[0], q[0]], [p[1], q[1]], color=bone_edge, lw=13,
                    solid_capstyle='round', zorder=1)
            ax.plot([p[0], q[0]], [p[1], q[1]], color=bone_fill, lw=10,
                    solid_capstyle='round', zorder=1)
        ax.add_patch(Circle(elbow, 0.06, fc=bone_fill, ec=bone_edge, lw=1.5, zorder=2))

        # --- Muscle: tendons + spindle-shaped belly ---
        origin, insertion = self._muscle_endpoints(alpha)
        axis_vec = insertion - origin
        length = np.linalg.norm(axis_vec)
        d = axis_vec / length
        p = np.array([-d[1], d[0]])
        if p[0] < 0:                 # make p point to the front of the arm (away from humerus)
            p = -p

        belly_start = origin + self._TENDON_ORIGIN * d
        belly_end = insertion - self._TENDON_INSERTION * d
        belly_len = length - self._TENDON_ORIGIN - self._TENDON_INSERTION

        o_rest, i_rest = self._muscle_endpoints(0.0)
        belly_rest = np.linalg.norm(i_rest - o_rest) - self._TENDON_ORIGIN - self._TENDON_INSERTION
        half_w = self._BELLY_HALF_WIDTH * np.sqrt(belly_rest / belly_len)

        t = np.linspace(0.0, 1.0, 60)
        centre = belly_start[None, :] + t[:, None] * (belly_end - belly_start)[None, :]
        profile = half_w * np.sin(np.pi * t) ** 0.8
        front = centre + 1.4 * profile[:, None] * p      # bulge mostly to the front
        back = centre - 0.6 * profile[:, None] * p
        outline = np.vstack([front, back[::-1]])

        relaxed = np.array([0.96, 0.80, 0.74])   # pale (no force)
        active = np.array([0.75, 0.16, 0.12])    # deep red (F = F0)
        muscle_colour = relaxed + force_ratio * (active - relaxed)
        ax.add_patch(Polygon(outline, closed=True, fc=muscle_colour,
                             ec=muscle_colour * 0.7, lw=1.2, zorder=4))

        tendon = '#e8dcc0'
        ax.plot([origin[0], belly_start[0]], [origin[1], belly_start[1]],
                color=tendon, lw=4, solid_capstyle='round', zorder=3)
        ax.plot([belly_end[0], insertion[0]], [belly_end[1], insertion[1]],
                color=tendon, lw=4, solid_capstyle='round', zorder=3)

        # --- Load in the hand (size ~ F/F0) ---
        if force_ratio > 0.005:
            plate_r = 0.05 + 0.11 * force_ratio
            ax.add_patch(Circle(hand, plate_r, fc='#7f8c8d', ec='#2c3e50', lw=1.5, zorder=5))
            ax.add_patch(Circle(hand, plate_r * 0.35, fc='#bdc3c7', ec='#2c3e50', lw=1, zorder=5))
        ax.add_patch(Circle(hand, 0.055, fc='#f1c27d', ec='#8d5524', lw=1.2, zorder=6))

        # --- Movement arrow around the elbow (length ~ v/Vmax) ---
        if r > 0.005:
            sweep = np.radians(15.0 + 30.0 * r)
            R = 1.25
            angles = np.linspace(alpha - 0.3 * sweep, alpha + 0.7 * sweep, 40)
            arc = np.column_stack([R * np.cos(angles), R * np.sin(angles)])
            ax.plot(arc[:-1, 0], arc[:-1, 1], 'k-', lw=1.5, zorder=3)
            ax.annotate('', xy=arc[-1], xytext=arc[-3],
                        arrowprops=dict(arrowstyle='-|>', color='k', lw=1.5, mutation_scale=15))

        # --- Labels ---
        if r <= 0.005:
            mode, motion = 'Isometric contraction', 'no movement'
        elif force_ratio <= 0.005:
            mode, motion = 'Unloaded shortening (V = Vmax)', f'movement: v = {v_op:.1f} mm/s'
        else:
            mode, motion = 'Concentric contraction', f'movement: v = {v_op:.1f} mm/s'
        ax.text(0.55, -0.30, mode, ha='center', va='center', fontsize=11, fontweight='bold')
        ax.text(0.55, -0.43, f'{motion}\ntension = load = {F_op:.1f} N',
                ha='center', va='top', fontsize=9)

        ax.set_title('Whole Muscle (Elbow Flexor)')
        ax.set_xlim(-0.35, 1.45)
        ax.set_ylim(-0.65, 1.40)
        ax.set_aspect('equal')
        ax.axis('off')
