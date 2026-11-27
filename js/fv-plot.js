// Force-velocity curve with optional power overlay and the operating point.
// Port of the top panel of MuscleVisualizer.update_plot (visualizer.py).
(function (HillSim) {
  "use strict";

  HillSim.drawForceVelocity = function (canvas, model, params, vOp, showPower) {
    const { ctx, W, H } = HillSim.prepareCanvas(canvas);
    const th = HillSim.readTheme();
    const font = (px, weight) => `${weight || 400} ${px}px ${HillSim.FONT}`;
    const fs = W < 420 ? 11 : 12;

    // Fixed margins (the right one stays even with power hidden, so the plot doesn't jump)
    const L = 62, R = 66, T = 14, B = 46;
    const pw = Math.max(10, W - L - R);
    const ph = Math.max(10, H - T - B);

    const F0 = params.F0;
    const vMax = model.getVmax(params);
    const xMax = Math.max(vMax * 1.1, 1);
    const yMax = Math.max(F0 * 1.1, 1);
    const sx = (v) => L + (v / xMax) * pw;
    const sy = (F) => T + ph - (F / yMax) * ph;

    // Curve samples
    const N = 200;
    const vArr = HillSim.linspace(0, Math.max(vMax, 1), N);
    const FArr = vArr.map((v) => model.evaluateForce(v, params));
    const PArr = vArr.map((v, i) => FArr[i] * v);
    const pMax = Math.max(Math.max.apply(null, PArr) * 1.1, 1);
    const sp = (P) => T + ph - (P / pMax) * ph;

    // Grid + ticks
    const xt = HillSim.niceTicks(xMax, W < 420 ? 4 : 6);
    const yt = HillSim.niceTicks(yMax, 5);
    ctx.save();
    ctx.strokeStyle = th.grid;
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    xt.forEach((t) => HillSim.polyline(ctx, [[sx(t), T], [sx(t), T + ph]]));
    yt.forEach((t) => HillSim.polyline(ctx, [[L, sy(t)], [L + pw, sy(t)]]));
    ctx.restore();

    ctx.font = font(fs);
    ctx.fillStyle = th.fg;
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    xt.forEach((t) => ctx.fillText(t.toFixed(xt.decimals), sx(t), T + ph + 5));

    ctx.fillStyle = th.fv;
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    yt.forEach((t) => ctx.fillText(t.toFixed(yt.decimals), L - 6, sy(t)));

    // Plot area clip for the curves
    ctx.save();
    ctx.beginPath();
    ctx.rect(L, T, pw, ph);
    ctx.clip();

    // Power overlay (dashed, drawn first so the F-v curve sits on top)
    if (showPower) {
      ctx.save();
      ctx.strokeStyle = th.power;
      ctx.globalAlpha = 0.75;
      ctx.lineWidth = 2.5;
      ctx.setLineDash([8, 5]);
      HillSim.polyline(ctx, vArr.map((v, i) => [sx(v), sp(PArr[i])]));
      ctx.restore();
    }

    // F-v curve
    ctx.strokeStyle = th.fv;
    ctx.lineWidth = 2.5;
    HillSim.polyline(ctx, vArr.map((v, i) => [sx(v), sy(FArr[i])]));

    // Operating point
    const FOp = model.evaluateForce(vOp, params);
    HillSim.circle(ctx, sx(vOp), sy(FOp), 6, th.op, null, 0);
    ctx.restore();

    // Axes box
    ctx.strokeStyle = th.axis;
    ctx.lineWidth = 1;
    ctx.strokeRect(L + 0.5, T + 0.5, pw, ph);

    // Power ticks on the right
    if (showPower) {
      const pt = HillSim.niceTicks(pMax, 5);
      ctx.font = font(fs);
      ctx.fillStyle = th.power;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      pt.forEach((t) => ctx.fillText(t.toFixed(pt.decimals), L + pw + 6, sp(t)));
    }

    // Axis labels
    ctx.font = font(fs + 1);
    ctx.fillStyle = th.fg;
    ctx.textAlign = "center";
    ctx.textBaseline = "bottom";
    ctx.fillText("Shortening Velocity (mm/s)", L + pw / 2, H - 4);

    const vlabel = (text, x, colour) => {
      ctx.save();
      ctx.translate(x, T + ph / 2);
      ctx.rotate(-Math.PI / 2);
      ctx.fillStyle = colour;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(text, 0, 0);
      ctx.restore();
    };
    vlabel("Force (N)", 14, th.fv);
    if (showPower) vlabel("Power (N·mm/s or mW)", W - 12, th.power);

    // Legend (top-right, where the hyperbola leaves empty space). Skipped on narrow
    // plots, where it would cover the curves; the coloured axis labels still identify them.
    if (pw < 340) return { FOp };
    const items = [
      { label: "F-v curve", draw: (x, y) => { ctx.strokeStyle = th.fv; ctx.lineWidth = 2.5; ctx.setLineDash([]); HillSim.polyline(ctx, [[x, y], [x + 22, y]]); } },
    ];
    if (showPower) {
      items.push({ label: "Power", draw: (x, y) => { ctx.save(); ctx.strokeStyle = th.power; ctx.lineWidth = 2.5; ctx.setLineDash([6, 4]); HillSim.polyline(ctx, [[x, y], [x + 22, y]]); ctx.restore(); } });
    }
    items.push({ label: "Operating point", draw: (x, y) => HillSim.circle(ctx, x + 11, y, 5, th.op, null, 0) });

    ctx.font = font(fs);
    const rowH = fs + 8;
    const textW = Math.max.apply(null, items.map((it) => ctx.measureText(it.label).width));
    const boxW = 22 + 8 + textW + 16;
    const boxH = items.length * rowH + 8;
    const bx = L + pw - boxW - 8;
    const by = T + 8;
    ctx.save();
    ctx.fillStyle = getComputedStyle(canvas).getPropertyValue("--legend-bg").trim() || "rgba(255,255,255,0.85)";
    ctx.strokeStyle = th.grid;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.rect(bx + 0.5, by + 0.5, boxW, boxH);
    ctx.fill();
    ctx.stroke();
    ctx.restore();
    items.forEach((it, i) => {
      const y = by + 4 + rowH * i + rowH / 2;
      it.draw(bx + 8, y);
      ctx.fillStyle = th.fg;
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(it.label, bx + 8 + 22 + 8, y);
    });

    return { FOp };
  };
})((window.HillSim = window.HillSim || {}));
