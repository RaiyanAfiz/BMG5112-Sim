// Shared canvas helpers used by the three views.
(function (HillSim) {
  "use strict";

  HillSim.FONT = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

  /** Sizes the canvas backing store to its CSS box (sharp on HiDPI) and clears it. */
  HillSim.prepareCanvas = function (canvas) {
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth;
    const H = canvas.clientHeight;
    const bw = Math.max(1, Math.round(W * dpr));
    const bh = Math.max(1, Math.round(H * dpr));
    if (canvas.width !== bw || canvas.height !== bh) {
      canvas.width = bw;
      canvas.height = bh;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    ctx.lineCap = "butt";
    ctx.lineJoin = "round";
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    return { ctx, W, H };
  };

  /** Reads the drawing colours from CSS custom properties (so dark mode works). */
  HillSim.readTheme = function () {
    const cs = getComputedStyle(document.documentElement);
    const v = (name) => cs.getPropertyValue(name).trim();
    return {
      fg: v("--fg"),
      muted: v("--muted"),
      grid: v("--grid"),
      axis: v("--axis"),
      fv: v("--c-fv"),
      power: v("--c-power"),
      op: v("--c-op"),
      zdisc: v("--c-zdisc"),
      actin: v("--c-actin"),
      myosin: v("--c-myosin"),
      headBound: v("--c-head-bound"),
      headFree: v("--c-head-free"),
    };
  };

  /** "Nice" tick values from 0 up to max (about `target` of them). */
  HillSim.niceTicks = function (max, target) {
    target = target || 5;
    if (!(max > 0)) return [0];
    const rough = max / target;
    const mag = Math.pow(10, Math.floor(Math.log10(rough)));
    const norm = rough / mag;
    const step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
    const ticks = [];
    for (let t = 0; t <= max * (1 + 1e-9); t += step) ticks.push(Number(t.toPrecision(12)));
    const decimals = Math.max(0, -Math.floor(Math.log10(step) + 1e-9));
    ticks.decimals = decimals;
    return ticks;
  };

  /** Strokes a polyline given as [[x, y], ...]. */
  HillSim.polyline = function (ctx, pts) {
    if (!pts.length) return;
    ctx.beginPath();
    ctx.moveTo(pts[0][0], pts[0][1]);
    for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
    ctx.stroke();
  };

  HillSim.circle = function (ctx, x, y, r, fill, stroke, lw) {
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    if (fill) {
      ctx.fillStyle = fill;
      ctx.fill();
    }
    if (stroke && lw > 0) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = lw;
      ctx.stroke();
    }
  };

  /**
   * Formats like Python's f"{x:.{d}f}". toFixed rounds exact ties up (166.25 -> "166.3");
   * Python rounds them to even ("166.2"). Only exact binary ties differ.
   */
  HillSim.fmt = function (x, d) {
    const s = x.toFixed(d);
    const exact = Math.abs(x).toFixed(100);              // exact decimal expansion
    const tail = exact.slice(exact.indexOf(".") + 1 + d);
    if (/^50*$/.test(tail)) {
      const scale = Math.pow(10, d);
      const down = ((x < 0 ? -1 : 1) * Math.floor(Math.abs(x) * scale)) / scale;
      const downStr = down.toFixed(d);
      if (Number(downStr.slice(-1)) % 2 === 0) return downStr;
    }
    return s;
  };

  HillSim.linspace = function (a, b, n) {
    if (n === 1) return [a];
    const out = new Array(n);
    for (let i = 0; i < n; i++) out[i] = a + ((b - a) * i) / (n - 1);
    return out;
  };
})((window.HillSim = window.HillSim || {}));
