from abc import ABC, abstractmethod
import numpy as np

CONDITION_PRESETS = {
    "average": {
        "label": "Average",
        "F0": 100.0,
        "Vmax": 160.0,
        "k": 0.25,
        "tooltip": "Average adult skeletal muscle (F0=100 N, Vmax=160 mm/s, k=0.25)",
    },
    "trained": {
        "label": "Trained",
        "F0": 200.0,
        "Vmax": 240.0,
        "k": 0.35,
        "tooltip": "Strength/power-trained muscle with greater cross-sectional area and fast-twitch output (F0=200 N, Vmax=240 mm/s, k=0.35)",
    },
    "atrophied": {
        "label": "Muscle Atrophied",
        "F0": 50.0,
        "Vmax": 100.0,
        "k": 0.15,
        "tooltip": "Atrophied muscle with reduced cross-sectional area and slower shortening velocity (F0=50 N, Vmax=100 mm/s, k=0.15)",
    },
}


class MuscleModel(ABC):
    """Abstract base class for skeletal muscle contraction models."""
    
    @abstractmethod
    def evaluate_force(self, v, params):
        pass

    @abstractmethod
    def evaluate_velocity(self, F, params):
        pass

class ClassicalHillModel(MuscleModel):
    """
    Classical Hill-type hyperbolic force-velocity model.
    Equation: F(v) = [(F0 + a) * b / (v + b)] - a
    With curvature k = a / F0 = b / Vmax, a = k * F0 and b = k * Vmax.
    """

    @staticmethod
    def derive_hill_constants(F0, Vmax, k):
        """Derive Hill asymptote constants (a, b) from (F0, Vmax, k)."""
        if k <= 0:
            raise ValueError("Curvature parameter k must be strictly positive.")
        a = k * F0
        b = k * Vmax
        return a, b

    def _resolve_params(self, params):
        """Resolve (F0, a, b) from either {F0, Vmax, k} or legacy {F0, a, b}."""
        F0 = params['F0']
        if 'Vmax' in params and 'k' in params:
            a, b = self.derive_hill_constants(F0, params['Vmax'], params['k'])
        elif 'a' in params and 'b' in params:
            a, b = params['a'], params['b']
        else:
            raise KeyError("params must contain either ('Vmax', 'k') or ('a', 'b').")
        return F0, a, b

    def evaluate_force(self, v, params):
        F0, a, b = self._resolve_params(params)

        # Determine maximum unloaded shortening velocity
        v_max = self.get_vmax(params)

        # Safeguard: cap velocity to v_max to prevent unphysical negative forces
        v_safe = np.clip(v, 0, v_max)

        # Safeguard: prevent divide-by-zero (though b is naturally constrained > 0)
        denominator = v_safe + b
        denominator = np.where(denominator == 0, 1e-6, denominator)

        F = ((F0 + a) * b / denominator) - a
        return np.maximum(F, 0.0)

    def evaluate_velocity(self, F, params):
        F0, a, b = self._resolve_params(params)

        # Safeguard: force cannot exceed max isometric force
        F_safe = np.clip(F, 0, F0)

        denominator = F_safe + a
        denominator = np.where(denominator == 0, 1e-6, denominator)

        v = ((F0 + a) * b / denominator) - b
        return np.maximum(v, 0.0)

    def get_vmax(self, params):
        """Helper to compute maximum shortening velocity (F = 0)."""
        if 'Vmax' in params:
            return float(params['Vmax'])
        F0, a, b = self._resolve_params(params)
        if a == 0:
            return 0.0
        return (b * F0) / a