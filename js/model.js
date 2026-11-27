// Hill-type muscle model: a direct port of model.py from the Python version.
(function (HillSim) {
  "use strict";

  HillSim.CONDITION_PRESETS = {
    average: {
      label: "Average",
      F0: 100.0,
      Vmax: 160.0,
      k: 0.25,
      tooltip: "Average adult skeletal muscle (F0=100 N, Vmax=160 mm/s, k=0.25)",
    },
    trained: {
      label: "Trained",
      F0: 200.0,
      Vmax: 240.0,
      k: 0.35,
      tooltip:
        "Strength/power-trained muscle with greater cross-sectional area and fast-twitch output (F0=200 N, Vmax=240 mm/s, k=0.35)",
    },
    atrophied: {
      label: "Muscle Atrophied",
      F0: 50.0,
      Vmax: 100.0,
      k: 0.15,
      tooltip:
        "Atrophied muscle with reduced cross-sectional area and slower shortening velocity (F0=50 N, Vmax=100 mm/s, k=0.15)",
    },
  };

  const clip = (x, lo, hi) => Math.min(Math.max(x, lo), hi);

  /**
   * Classical Hill-type hyperbolic force-velocity model.
   *   F(v) = [(F0 + a) * b / (v + b)] - a
   * With curvature k = a / F0 = b / Vmax, a = k * F0 and b = k * Vmax.
   * params: { F0, Vmax, k } (or legacy { F0, a, b }).
   */
  class ClassicalHillModel {
    static deriveHillConstants(F0, Vmax, k) {
      if (k <= 0) throw new RangeError("Curvature parameter k must be strictly positive.");
      return { a: k * F0, b: k * Vmax };
    }

    resolveParams(params) {
      const F0 = params.F0;
      if (params.Vmax !== undefined && params.k !== undefined) {
        const { a, b } = ClassicalHillModel.deriveHillConstants(F0, params.Vmax, params.k);
        return { F0, a, b };
      }
      if (params.a !== undefined && params.b !== undefined) {
        return { F0, a: params.a, b: params.b };
      }
      throw new Error("params must contain either (Vmax, k) or (a, b).");
    }

    /** Maximum shortening velocity (F = 0). */
    getVmax(params) {
      if (params.Vmax !== undefined) return Number(params.Vmax);
      const { F0, a, b } = this.resolveParams(params);
      return a === 0 ? 0 : (b * F0) / a;
    }

    /** Force at shortening velocity v (number). */
    evaluateForce(v, params) {
      const { F0, a, b } = this.resolveParams(params);
      const vMax = this.getVmax(params);
      const vSafe = clip(v, 0, vMax); // no unphysical negative forces past Vmax
      const denom = vSafe + b === 0 ? 1e-6 : vSafe + b;
      return Math.max(((F0 + a) * b) / denom - a, 0);
    }

    /** Shortening velocity at force F (number). */
    evaluateVelocity(F, params) {
      const { F0, a, b } = this.resolveParams(params);
      const FSafe = clip(F, 0, F0);
      const denom = FSafe + a === 0 ? 1e-6 : FSafe + a;
      return Math.max(((F0 + a) * b) / denom - b, 0);
    }
  }

  HillSim.ClassicalHillModel = ClassicalHillModel;
  HillSim.clip = clip;
})((window.HillSim = window.HillSim || {}));
