// Whole-muscle view: an elbow flexor lifting a load at the current operating point.
// Port of ArmVisualizer._draw_arm (visualizer.py).
(function (HillSim) {
  "use strict";

  // Geometry in arbitrary units; the elbow joint sits at the origin.
  const SHOULDER = [0.0, 1.0];
  const ELBOW = [0.0, 0.0];
  const FOREARM_LEN = 0.95;
  const MAX_FLEXION_DEG = 60.0;          // extra elbow flexion (above horizontal) at v = Vmax
  const ORIGIN_OFFSET = [0.07, -0.12];   // muscle origin, relative to shoulder
  const INSERTION_DIST = 0.2;            // insertion distance along forearm from elbow
  const INSERTION_LIFT = 0.05;           // insertion sits on the top surface of the forearm
  const TENDON_ORIGIN = 0.1;
  const TENDON_INSERTION = 0.08;
  const BELLY_HALF_WIDTH = 0.09;         // belly half-width at resting length
  const X_MIN = -0.35, X_MAX = 1.45, Y_MIN = -0.65, Y_MAX = 1.4;

  const add = (a, b) => [a[0] + b[0], a[1] + b[1]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
  const mul = (a, s) => [a[0] * s, a[1] * s];
  const norm = (a) => Math.hypot(a[0], a[1]);

  /** Origin and insertion of the muscle for a forearm angle alpha (rad above horizontal). */
  function muscleEndpoints(alpha) {
    const u = [Math.cos(alpha), Math.sin(alpha)];    // along the forearm
    const n = [-Math.sin(alpha), Math.cos(alpha)];   // forearm's upper surface normal
    const origin = add(SHOULDER, ORIGIN_OFFSET);
    const insertion = add(add(ELBOW, mul(u, INSERTION_DIST)), mul(n, INSERTION_LIFT));
    return { origin, insertion };
  }

  const toCss = (rgb) =>
    `rgb(${rgb.map((c) => Math.round(HillSim.clip(c, 0, 1) * 255)).join(",")})`;

  /**
   * Elbow flexor lifting a load, driven by the current operating point.
   *  - Tension in the muscle = load in the hand = F (steady shortening, as in Hill's
   *    afterloaded experiments), so the weight's size scales with F/F0.
   *  - Muscle colour intensity scales with F/F0 (force output).
   *  - Elbow flexion uses the same v/Vmax ratio as the sarcomere panel.
   *  - The belly keeps constant volume: width ~ 1/sqrt(length).
   */
  HillSim.drawArm = function (canvas, contractionRatio, FOp, F0, vOp) {
    const { ctx, W, H } = HillSim.prepareCanvas(canvas);
    const th = HillSim.readTheme();

    // Equal-aspect fit of the data box into the canvas
    const pad = 6;
    const s = Math.min((W - 2 * pad) / (X_MAX - X_MIN), (H - 2 * pad) / (Y_MAX - Y_MIN));
    const ox = (W - s * (X_MAX - X_MIN)) / 2 - s * X_MIN;
    const oy = (H - s * (Y_MAX - Y_MIN)) / 2 + s * Y_MAX;
    const P = (p) => [ox + p[0] * s, oy - p[1] * s];
    const pt = s / 115;   // px per matplotlib point at the Python app's size

    const forceRatio = F0 > 0 ? HillSim.clip(FOp / F0, 0, 1) : 0;
    const r = HillSim.clip(contractionRatio, 0, 1);

    const alpha = (MAX_FLEXION_DEG * r * Math.PI) / 180;
    const u = [Math.cos(alpha), Math.sin(alpha)];
    const hand = add(ELBOW, mul(u, FOREARM_LEN));

    // --- Bones (outline + fill) and elbow joint ---
    const boneFill = "#f3ead8", boneEdge = "#5a4a3a";
    ctx.lineCap = "round";
    [[SHOULDER, ELBOW], [ELBOW, hand]].forEach(([p, q]) => {
      ctx.strokeStyle = boneEdge;
      ctx.lineWidth = 13 * pt;
      HillSim.polyline(ctx, [P(p), P(q)]);
      ctx.strokeStyle = boneFill;
      ctx.lineWidth = 10 * pt;
      HillSim.polyline(ctx, [P(p), P(q)]);
    });
    HillSim.circle(ctx, ...P(ELBOW), 0.06 * s, boneFill, boneEdge, 1.5 * pt);

    // --- Muscle geometry: tendons + spindle-shaped belly ---
    const { origin, insertion } = muscleEndpoints(alpha);
    const axisVec = sub(insertion, origin);
    const length = norm(axisVec);
    const d = mul(axisVec, 1 / length);
    let p = [-d[1], d[0]];
    if (p[0] < 0) p = mul(p, -1);   // point to the front of the arm (away from humerus)

    const bellyStart = add(origin, mul(d, TENDON_ORIGIN));
    const bellyEnd = sub(insertion, mul(d, TENDON_INSERTION));
    const bellyLen = length - TENDON_ORIGIN - TENDON_INSERTION;

    const rest = muscleEndpoints(0);
    const bellyRest = norm(sub(rest.insertion, rest.origin)) - TENDON_ORIGIN - TENDON_INSERTION;
    const halfW = BELLY_HALF_WIDTH * Math.sqrt(bellyRest / bellyLen);

    // Tendons (under the belly)
    ctx.strokeStyle = "#e8dcc0";
    ctx.lineWidth = 4 * pt;
    HillSim.polyline(ctx, [P(origin), P(bellyStart)]);
    HillSim.polyline(ctx, [P(bellyEnd), P(insertion)]);

    // --- Movement arrow around the elbow (length ~ v/Vmax) ---
    if (r > 0.005) {
      const sweep = ((15 + 30 * r) * Math.PI) / 180;
      const R = 1.25;
      const angles = HillSim.linspace(alpha - 0.3 * sweep, alpha + 0.7 * sweep, 40);
      const arc = angles.map((a) => P([R * Math.cos(a), R * Math.sin(a)]));
      ctx.strokeStyle = th.fg;
      ctx.lineWidth = 1.5 * pt;
      ctx.lineCap = "butt";
      HillSim.polyline(ctx, arc.slice(0, -1));
      // Arrowhead pointing along the arc's end
      const tip = arc[arc.length - 1], from = arc[arc.length - 3];
      const ang = Math.atan2(tip[1] - from[1], tip[0] - from[0]);
      const hl = 11 * pt, hw = 4.5 * pt;
      ctx.fillStyle = th.fg;
      ctx.beginPath();
      ctx.moveTo(tip[0], tip[1]);
      ctx.lineTo(tip[0] - hl * Math.cos(ang) + hw * Math.sin(ang), tip[1] - hl * Math.sin(ang) - hw * Math.cos(ang));
      ctx.lineTo(tip[0] - hl * Math.cos(ang) - hw * Math.sin(ang), tip[1] - hl * Math.sin(ang) + hw * Math.cos(ang));
      ctx.closePath();
      ctx.fill();
    }

    // Belly outline: bulges mostly to the front
    const front = [], back = [];
    HillSim.linspace(0, 1, 60).forEach((t) => {
      const centre = add(bellyStart, mul(sub(bellyEnd, bellyStart), t));
      const prof = halfW * Math.pow(Math.sin(Math.PI * t), 0.8);
      front.push(add(centre, mul(p, 1.4 * prof)));
      back.push(sub(centre, mul(p, 0.6 * prof)));
    });
    const outline = front.concat(back.reverse()).map(P);

    const relaxed = [0.96, 0.8, 0.74];   // pale (no force)
    const active = [0.75, 0.16, 0.12];   // deep red (F = F0)
    const colour = relaxed.map((c, i) => c + forceRatio * (active[i] - c));
    ctx.beginPath();
    outline.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1]) : ctx.moveTo(q[0], q[1])));
    ctx.closePath();
    ctx.fillStyle = toCss(colour);
    ctx.fill();
    ctx.strokeStyle = toCss(colour.map((c) => c * 0.7));
    ctx.lineWidth = 1.2 * pt;
    ctx.stroke();

    // --- Load in the hand (size ~ F/F0) ---
    const hp = P(hand);
    if (forceRatio > 0.005) {
      const plateR = 0.05 + 0.11 * forceRatio;
      HillSim.circle(ctx, hp[0], hp[1], plateR * s, "#7f8c8d", "#2c3e50", 1.5 * pt);
      HillSim.circle(ctx, hp[0], hp[1], plateR * 0.35 * s, "#bdc3c7", "#2c3e50", 1 * pt);
    }
    HillSim.circle(ctx, hp[0], hp[1], 0.055 * s, "#f1c27d", "#8d5524", 1.2 * pt);

    // --- Labels ---
    let mode, motion;
    if (r <= 0.005) {
      mode = "Isometric contraction";
      motion = "no movement";
    } else if (forceRatio <= 0.005) {
      mode = "Unloaded shortening (V = Vmax)";
      motion = `movement: v = ${HillSim.fmt(vOp, 1)} mm/s`;
    } else {
      mode = "Concentric contraction";
      motion = `movement: v = ${HillSim.fmt(vOp, 1)} mm/s`;
    }
    const big = HillSim.clip(11 * pt, 12, 15), small = HillSim.clip(9 * pt, 11, 13);
    const lp = P([0.55, -0.3]);
    ctx.fillStyle = th.fg;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = `700 ${big}px ${HillSim.FONT}`;
    ctx.fillText(mode, lp[0], lp[1]);
    ctx.font = `400 ${small}px ${HillSim.FONT}`;
    ctx.textBaseline = "top";
    const mp = P([0.55, -0.43]);
    ctx.fillText(motion, mp[0], mp[1]);
    ctx.fillText(`tension = load = ${HillSim.fmt(FOp, 1)} N`, mp[0], mp[1] + small * 1.25);

    return { alpha, forceRatio, colour };
  };
})((window.HillSim = window.HillSim || {}));
