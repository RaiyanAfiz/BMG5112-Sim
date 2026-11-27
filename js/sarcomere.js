// Sarcomere schematic: port of MuscleVisualizer._draw_sarcomere /
// _draw_myosin_heads / _add_sarcomere_legend (visualizer.py).
(function (HillSim) {
  "use strict";

  // Fixed per-head binding thresholds, copied from the Python version's
  // np.random.default_rng(42).random((6, 12)), so exactly the same heads are
  // bound in both versions. A head binds when its threshold < F/F0.
  const THRESHOLDS = [
    [0.773956, 0.438878, 0.858598, 0.697368, 0.094177, 0.975622, 0.76114, 0.786064, 0.128114, 0.450386, 0.370798, 0.926765],
    [0.643865, 0.822762, 0.443414, 0.227239, 0.554585, 0.063817, 0.827631, 0.631664, 0.758088, 0.354526, 0.970698, 0.893121],
    [0.778383, 0.194639, 0.466721, 0.043804, 0.154289, 0.683049, 0.744762, 0.96751, 0.325825, 0.37046, 0.469556, 0.189471],
    [0.129922, 0.475705, 0.226909, 0.669814, 0.437152, 0.832678, 0.700265, 0.312367, 0.83226, 0.804764, 0.387478, 0.288328],
    [0.682496, 0.139752, 0.199908, 0.007362, 0.786924, 0.664851, 0.705165, 0.780729, 0.458916, 0.568741, 0.139797, 0.11453],
    [0.668403, 0.471096, 0.565236, 0.764999, 0.634718, 0.553579, 0.559207, 0.30395, 0.030818, 0.436717, 0.214585, 0.408529],
  ];

  // Geometry (same units as the Python schematic)
  const X_MIN = -2.0, X_MAX = 2.0, Y_MIN = -1.3, Y_MAX = 0.62;
  const ACTIN_LEN = 0.9;
  const ACTIN_Y = [-0.3, -0.1, 0.1, 0.3];
  const MYO_HALF = 0.8;
  const MYO_Y = [-0.2, 0.0, 0.2];
  const HEADS_PER_HALF = 6;
  const BARE_ZONE = 0.15;   // central M-line region has no heads
  const HEAD_REACH = 0.1;   // vertical gap between myosin and actin rows

  const xLeft = HillSim.linspace(-MYO_HALF, -BARE_ZONE, HEADS_PER_HALF);
  const HEAD_X = xLeft.concat(xLeft.slice().reverse().map((x) => -x));

  /**
   * Which heads are bound for a given sarcomere half-length and F/F0.
   * Pure geometry, no drawing (also used by the tests).
   */
  HillSim.computeCrossBridges = function (halfL, boundFraction) {
    const bound = [], free = [];
    let nAvailable = 0;
    MYO_Y.forEach((y, i) => {
      [1, -1].forEach((side, j) => {           // 1 = up, -1 = down
        const row = THRESHOLDS[2 * i + j];
        HEAD_X.forEach((x, k) => {
          const tilt = x < 0 ? -1 : 1;         // heads lean toward their Z-disc
          // Is there actin above/below this head to grab?
          const overlaps = (x >= -halfL && x <= -halfL + ACTIN_LEN) ||
                           (x >= halfL - ACTIN_LEN && x <= halfL);
          const y0 = y + side * 0.03;
          if (overlaps) nAvailable++;
          if (overlaps && row[k] < boundFraction) {
            bound.push([[x, y0], [x + tilt * 0.06, y + side * HEAD_REACH]]);
          } else {
            free.push([[x, y0], [x + tilt * 0.04, y + side * 0.055]]);
          }
        });
      });
    });
    return { bound, free, nBound: bound.length, nAvailable };
  };

  /** Visual sarcomere length shrinks as v approaches Vmax. */
  HillSim.sarcomereLength = (contractionRatio) => 3.0 - 1.2 * contractionRatio;

  HillSim.drawSarcomere = function (canvas, contractionRatio, FOp, F0) {
    const { ctx, W, H } = HillSim.prepareCanvas(canvas);
    const th = HillSim.readTheme();

    // Data -> pixels (auto aspect, like the matplotlib axes)
    const L = 6, R = 6, T = 4, B = 4;
    const pw = W - L - R, ph = H - T - B;
    const sx = (x) => L + ((x - X_MIN) / (X_MAX - X_MIN)) * pw;
    const sy = (y) => T + ((Y_MAX - y) / (Y_MAX - Y_MIN)) * ph;
    const pt = HillSim.clip(W / 560, 0.7, 1.4) * 1.39;   // px per matplotlib point
    const seg = (a, b) => HillSim.polyline(ctx, [[sx(a[0]), sy(a[1])], [sx(b[0]), sy(b[1])]]);

    const halfL = HillSim.sarcomereLength(contractionRatio) / 2;
    const forceRatio = F0 > 0 ? FOp / F0 : 0;

    // Z-discs
    ctx.strokeStyle = th.zdisc;
    ctx.lineWidth = 4 * pt;
    seg([-halfL, -0.5], [-halfL, 0.5]);
    seg([halfL, -0.5], [halfL, 0.5]);

    // Actin (thin filaments attached to the Z-discs)
    ctx.strokeStyle = th.actin;
    ctx.lineWidth = 2 * pt;
    ACTIN_Y.forEach((y) => {
      seg([-halfL, y], [-halfL + ACTIN_LEN, y]);
      seg([halfL, y], [halfL - ACTIN_LEN, y]);
    });

    // Myosin (thick filaments): thicker with more force
    ctx.strokeStyle = th.myosin;
    ctx.lineWidth = (2 + 5 * forceRatio) * pt;
    MYO_Y.forEach((y) => seg([-MYO_HALF, y], [MYO_HALF, y]));

    // Myosin heads
    const cb = HillSim.computeCrossBridges(halfL, forceRatio);
    ctx.save();
    ctx.strokeStyle = th.headFree;
    ctx.globalAlpha = 0.7;
    ctx.lineWidth = 1.5 * pt;
    cb.free.forEach((s) => seg(s[0], s[1]));
    ctx.restore();
    ctx.strokeStyle = th.headBound;
    ctx.lineWidth = 2 * pt;
    cb.bound.forEach((s) => seg(s[0], s[1]));
    cb.bound.forEach((s) => HillSim.circle(ctx, sx(s[1][0]), sy(s[1][1]), 2 * pt, th.headBound, null, 0));

    // Bound count
    const fs = HillSim.clip(Math.round(10 * pt), 12, 15);
    ctx.font = `400 ${fs}px ${HillSim.FONT}`;
    ctx.fillStyle = th.fg;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(`Bound cross-bridges: ${cb.nBound} / ${cb.nAvailable} in overlap zone`, sx(0), sy(-0.68));

    drawLegend(ctx, th, W, sy(Y_MIN) - 2, pt);
    return cb;
  };

  function drawLegend(ctx, th, W, bottom, pt) {
    const fs = HillSim.clip(Math.round(8.5 * pt), 11, 13);
    ctx.font = `400 ${fs}px ${HillSim.FONT}`;
    const handleW = 22, gap = 6, colGap = 18, rowH = fs + 8;
    const items = [
      { label: "Z-disc", draw: (x, y) => line(x, y, th.zdisc, 4 * pt) },
      { label: "Actin (thin filament)", draw: (x, y) => line(x, y, th.actin, 2 * pt) },
      { label: "Myosin (thick filament)", draw: (x, y) => line(x, y, th.myosin, 5 * pt) },
      { label: "Myosin head (bound)", draw: (x, y) => { line(x, y, th.headBound, 2 * pt); HillSim.circle(ctx, x + handleW / 2, y, 2 * pt, th.headBound, null, 0); } },
      { label: "Myosin head (free)", draw: (x, y) => { ctx.save(); ctx.globalAlpha = 0.7; line(x, y, th.headFree, 1.5 * pt); ctx.restore(); } },
    ];
    function line(x, y, colour, lw) {
      ctx.strokeStyle = colour;
      ctx.lineWidth = lw;
      HillSim.polyline(ctx, [[x, y], [x + handleW, y]]);
    }

    // Wrap items into centred rows that fit the width
    items.forEach((it) => (it.w = handleW + gap + ctx.measureText(it.label).width));
    const rows = [[]];
    let rowW = 0;
    items.forEach((it) => {
      const add = (rows[rows.length - 1].length ? colGap : 0) + it.w;
      if (rows[rows.length - 1].length && rowW + add > W - 12) {
        rows.push([it]);
        rowW = it.w;
      } else {
        rows[rows.length - 1].push(it);
        rowW += add;
      }
    });

    rows.forEach((row, r) => {
      const total = row.reduce((s, it, i) => s + it.w + (i ? colGap : 0), 0);
      let x = (W - total) / 2;
      const y = bottom - (rows.length - r - 0.5) * rowH;
      row.forEach((it) => {
        it.draw(x, y);
        ctx.fillStyle = th.fg;
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(it.label, x + handleW + gap, y);
        x += it.w + colGap;
      });
    });
  }
})((window.HillSim = window.HillSim || {}));
