// Wires the controls to the model and the three views (port of app.py).
(function (H) {
  "use strict";

  const model = new H.ClassicalHillModel();
  const $ = (id) => document.getElementById(id);

  // Same ranges, steps and defaults as the Python app
  const CONTROLS = {
    F0:   { min: 10,   max: 500, step: 1,    decimals: 1 },
    Vmax: { min: 10,   max: 500, step: 1,    decimals: 1 },
    k:    { min: 0.05, max: 1.0, step: 0.01, decimals: 2 },
    v:    { min: 0,    max: 100, step: 1,    decimals: 1 },   // % of Vmax
  };

  const defaults = H.CONDITION_PRESETS.average;
  const state = { F0: defaults.F0, Vmax: defaults.Vmax, k: defaults.k, v: 20, showPower: true };

  const canvases = { fv: $("fv-canvas"), sarc: $("sarc-canvas"), arm: $("arm-canvas") };
  const readouts = { vmax: $("ro-vmax"), k: $("ro-k"), F: $("ro-F"), v: $("ro-v"), P: $("ro-P") };

  // ---- Linked slider + number box -------------------------------------------
  function showValue(key) {
    const c = CONTROLS[key];
    $(`${key}-range`).value = String(state[key]);
    $(`${key}-num`).value = state[key].toFixed(c.decimals);
  }

  function setValue(key, raw) {
    const c = CONTROLS[key];
    const val = Number(H.clip(Number(raw), c.min, c.max).toFixed(c.decimals));
    if (!Number.isFinite(val)) return false;
    state[key] = val;
    return true;
  }

  Object.keys(CONTROLS).forEach((key) => {
    const c = CONTROLS[key];
    const range = $(`${key}-range`);
    const num = $(`${key}-num`);
    [range, num].forEach((el) => {
      el.min = c.min;
      el.max = c.max;
      el.step = c.step;
    });

    range.addEventListener("input", () => {
      if (setValue(key, range.value)) {
        num.value = state[key].toFixed(c.decimals);
        scheduleUpdate();
      }
    });
    // While typing: apply only values that are already in range
    num.addEventListener("input", () => {
      const v = Number(num.value);
      if (num.value !== "" && Number.isFinite(v) && v >= c.min && v <= c.max && setValue(key, v)) {
        range.value = String(state[key]);
        scheduleUpdate();
      }
    });
    // On commit (Enter / blur / spinner): clamp and tidy the display
    num.addEventListener("change", () => {
      if (!setValue(key, num.value === "" ? state[key] : num.value)) return;
      num.value = state[key].toFixed(c.decimals);
      range.value = String(state[key]);
      scheduleUpdate();
    });
  });

  // ---- Muscle condition presets ---------------------------------------------
  const conditionBox = $("conditions");
  Object.entries(H.CONDITION_PRESETS).forEach(([key, preset]) => {
    const label = document.createElement("label");
    label.className = "radio";
    label.title = preset.tooltip;
    const input = document.createElement("input");
    input.type = "radio";
    input.name = "condition";
    input.value = key;
    input.checked = key === "average";
    // "click" also fires when re-clicking the selected option, which resets any
    // manual edits back to that preset (same as the Python app).
    input.addEventListener("click", () => applyCondition(key));
    label.append(input, document.createTextNode(" " + preset.label));
    conditionBox.append(label);
  });

  function applyCondition(key) {
    const p = H.CONDITION_PRESETS[key];
    setValue("F0", p.F0);
    setValue("Vmax", p.Vmax);
    setValue("k", p.k);
    ["F0", "Vmax", "k"].forEach(showValue);
    scheduleUpdate();
  }

  $("power-check").addEventListener("change", (e) => {
    state.showPower = e.target.checked;
    scheduleUpdate();
  });

  // ---- Simulation update -----------------------------------------------------
  function update() {
    const params = { F0: state.F0, Vmax: state.Vmax, k: state.k };
    const vMax = model.getVmax(params);
    const vOp = (state.v / 100) * vMax;
    const FOp = model.evaluateForce(vOp, params);
    const POp = FOp * vOp;
    const contractionRatio = vMax > 0 ? vOp / vMax : 0;

    readouts.vmax.textContent = `${H.fmt(vMax, 1)} mm/s`;
    readouts.k.textContent = H.fmt(params.k, 2);
    readouts.F.textContent = `${H.fmt(FOp, 1)} N`;
    readouts.v.textContent = `${H.fmt(vOp, 1)} mm/s`;
    readouts.P.textContent = `${H.fmt(POp, 1)} mW`;

    H.drawForceVelocity(canvases.fv, model, params, vOp, state.showPower);
    H.drawSarcomere(canvases.sarc, contractionRatio, FOp, params.F0);
    H.drawArm(canvases.arm, contractionRatio, FOp, params.F0, vOp);
  }

  let pending = false;
  function scheduleUpdate() {
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      update();
    });
  }

  // Redraw on resize and when the system light/dark theme changes
  if ("ResizeObserver" in window) {
    const ro = new ResizeObserver(scheduleUpdate);
    Object.values(canvases).forEach((c) => ro.observe(c));
  } else {
    window.addEventListener("resize", scheduleUpdate);
  }
  const mq = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");
  if (mq && mq.addEventListener) mq.addEventListener("change", scheduleUpdate);

  Object.keys(CONTROLS).forEach(showValue);
  $("power-check").checked = state.showPower;
  update();

  H.app = { state, update, applyCondition, model };
})(window.HillSim);
