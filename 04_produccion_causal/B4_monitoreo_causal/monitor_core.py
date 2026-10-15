"""Monitoring core for the local causal production path.

The module is deliberately independent of a UI. It returns auditable rows and
an operational action for each window: continue, alert, review identification,
abstain or retrain.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from scipy import stats

B4 = Path(__file__).resolve().parent
REPO = B4.parents[1]
DATA_ROOT = REPO / "data_benchmark_causal" / "causal_benchmark_synthetic" / "datasets"
SCENARIO = DATA_ROOT / "synthetic" / "inference" / "ihdp_medium"


@dataclass(frozen=True)
class MonitorThresholds:
    psi_alert: float = 0.12
    psi_large: float = 0.25
    z_effect: float = 3.0
    nc_z: float = 3.0
    frac_ps_fail: float = 0.10
    ess_alert: float = 0.30
    ess_fail: float = 0.15
    smd_alert: float = 0.10
    smd_fail: float = 0.25


def load_baseline_train():
    frame = pd.read_csv(SCENARIO / "observed_train.csv")
    features = [c for c in frame.columns if c not in {"row_id", "treatment", "outcome"}]
    return frame[features].copy(), frame["treatment"].copy(), frame["outcome"].copy()


def ks_drift_report(
    X_base: np.ndarray,
    X_window: np.ndarray,
    feature_idx: Tuple[int, ...] = (0, 1, 2),
) -> Dict[str, float]:
    out = {}
    for j in feature_idx:
        out[f"ks_f{j}"] = float(stats.ks_2samp(X_base[:, j], X_window[:, j]).statistic)
    out["ks_max"] = float(max(out.values()))
    return out


def _difference_in_means(y: np.ndarray, t: np.ndarray) -> float:
    treated = y[t == 1]
    control = y[t == 0]
    if len(treated) == 0 or len(control) == 0:
        return float("nan")
    return float(treated.mean() - control.mean())


def _simple_support_metrics(X: np.ndarray, t: np.ndarray) -> tuple[float, float, float]:
    """Approximate overlap, ESS and weighted SMD without using truth."""
    from sklearn.linear_model import LogisticRegression

    # Binary logistic regression does not need the L-BFGS path here.  The
    # liblinear solver avoids the deprecated SciPy ``disp`` route while
    # preserving the support diagnostic used by the monitor.
    ps = LogisticRegression(max_iter=500, random_state=42, solver="liblinear").fit(X, t).predict_proba(X)[:, 1]
    ps = np.clip(ps, 1e-4, 1 - 1e-4)
    extreme = float(np.mean((ps < 0.05) | (ps > 0.95)))
    wt, wc = 1.0 / ps[t == 1], 1.0 / (1.0 - ps[t == 0])
    ess = min((wt.sum() ** 2 / (wt**2).sum()) / max(len(wt), 1), (wc.sum() ** 2 / (wc**2).sum()) / max(len(wc), 1))
    smd = []
    for j in range(X.shape[1]):
        pooled = float(np.std(X[:, j], ddof=1)) or 1.0
        smd.append(abs(float(np.average(X[t == 1, j], weights=wt) - np.average(X[t == 0, j], weights=wc))) / pooled)
    return extreme, float(ess), float(max(smd))


def decide_action(metrics: dict, thresholds: MonitorThresholds = MonitorThresholds()) -> dict:
    """Apply the production precedence rule to one monitoring window."""
    if metrics.get("frac_ps_extremo", 0.0) >= thresholds.frac_ps_fail:
        return {"accion": "abstenerse", "motivo": "positividad fuera de límite"}
    if metrics.get("ess_rel_min", 1.0) <= thresholds.ess_fail or metrics.get("smd_pond_max", 0.0) >= thresholds.smd_fail:
        return {"accion": "abstenerse", "motivo": "solapamiento o balance fuera de límite"}
    if abs(metrics.get("nc_abs_z", 0.0)) >= thresholds.nc_z:
        return {"accion": "revisar_identificacion", "motivo": "el control negativo rechaza"}
    effect_changed = abs(metrics.get("z_efecto", 0.0)) >= thresholds.z_effect
    drift_large = metrics.get("psi_max", 0.0) >= thresholds.psi_large
    if effect_changed and not drift_large:
        return {"accion": "revisar_identificacion", "motivo": "cambió el efecto sin drift grande"}
    if effect_changed and drift_large:
        return {"accion": "reentrenar", "motivo": "drift grande y cambio del efecto"}
    if drift_large or metrics.get("psi_max", 0.0) >= thresholds.psi_alert:
        return {"accion": "alertar", "motivo": "drift de covariables; revisar soporte"}
    if metrics.get("ess_rel_min", 1.0) <= thresholds.ess_alert or metrics.get("smd_pond_max", 0.0) >= thresholds.smd_alert:
        return {"accion": "alertar", "motivo": "la puerta de overlap/balance está en alerta"}
    return {"accion": "continuar", "motivo": "sin señales"}


def simulate_monitor_table(
    *,
    n_windows: int = 12,
    window_size: int = 200,
    drift_start: int = 6,
    drift_strength: float = 0.8,
    effect_shift: float = 0.25,
    ks_threshold: float = 0.15,
    seed: int = 42,
) -> pd.DataFrame:
    """Create a deterministic teaching table from observed data only."""
    X_base, t_base, y_base = load_baseline_train()
    X = X_base.to_numpy(dtype=float)
    t = t_base.to_numpy(dtype=int)
    y = y_base.to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    n = len(X)
    baseline_proxy = _difference_in_means(y, t)
    rows = []
    for w in range(n_windows):
        idx = rng.integers(0, n, size=window_size)
        Xw, tw, yw = X[idx].copy(), t[idx].copy(), y[idx].copy()
        in_drift = w >= drift_start
        step = w - drift_start + 1 if in_drift else 0
        if in_drift:
            Xw[:, :3] += drift_strength * step
            p = np.clip(float(t.mean()) + 0.04 * step, 0.02, 0.98)
            tw = rng.binomial(1, p, size=window_size)
            yw = yw + effect_shift * step * tw
        base_idx = rng.integers(0, n, size=window_size)
        ks = ks_drift_report(X[base_idx], Xw, tuple(range(min(3, X.shape[1]))))
        proxy = _difference_in_means(yw, tw)
        extreme, ess, smd = _simple_support_metrics(Xw, tw)
        z_effect = (proxy - baseline_proxy) / max(float(np.std(yw)) / math.sqrt(max(window_size, 1)), 1e-6)
        metrics = {
            "psi_max": ks["ks_max"],
            "frac_ps_extremo": extreme,
            "ess_rel_min": ess,
            "smd_pond_max": smd,
            "z_efecto": float(z_effect),
            "nc_abs_z": 0.0,
        }
        decision = decide_action(metrics, MonitorThresholds(psi_alert=ks_threshold))
        rows.append({
            "window": w, "ks_max": ks["ks_max"], "psi_max": ks["ks_max"],
            "treatment_rate": float(tw.mean()), "effect_proxy": proxy,
            "effect_proxy_delta": abs(proxy - baseline_proxy), "drift_injected": in_drift,
            **metrics, **decision, "alert": bool(ks["ks_max"] >= ks_threshold),
        })
    return pd.DataFrame(rows)


def simulate_and_count_alerts(
    *, n_windows: int = 12, window_size: int = 200, drift_start: int = 6,
    drift_strength: float = 0.8, ks_threshold: float = 0.15, seed: int = 42,
) -> Dict[str, float]:
    table = simulate_monitor_table(
        n_windows=n_windows, window_size=window_size, drift_start=drift_start,
        drift_strength=drift_strength, ks_threshold=ks_threshold, seed=seed,
    )
    after = table[table["window"] >= drift_start]
    return {
        "n_alerts": float(table["alert"].sum()),
        "max_ks_after_drift": float(after["ks_max"].max()) if len(after) else 0.0,
        "ks_threshold": ks_threshold,
    }
