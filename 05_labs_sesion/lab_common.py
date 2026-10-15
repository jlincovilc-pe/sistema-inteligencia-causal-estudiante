"""Utilidades compartidas por los labs canónicos del curso.

Los notebooks consumen el benchmark local del monorepo mediante ``lab_data``.
Los frames observados y los archivos de evaluación con ground truth permanecen
separados. El modo stand-in está desactivado por defecto y solo se habilita
explícitamente con ``LAB_STAND_IN=1``.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from lab_data import data_root as local_data_root
from lab_data import load_local_bundle

BENCH_REL = Path("data_benchmark_causal") / "causal_benchmark_synthetic" / "datasets"

SEED = 42
FULL = os.environ.get("LAB_FULL", "0") == "1"


def R(rapido: int, completo: int) -> int:
    """Número de réplicas Monte Carlo: reducido por defecto; LAB_FULL=1 usa el completo."""
    return completo if FULL else rapido


def setup(seed: int = SEED):
    warnings.filterwarnings("ignore")
    np.random.seed(seed)
    try:
        import matplotlib
        matplotlib.rcParams.update({"figure.figsize": (6.5, 3.6), "axes.grid": True, "grid.alpha": .25})
    except Exception:
        pass
    print(f"Python {platform.python_version()} · numpy {np.__version__} · pandas {pd.__version__} · "
          f"carpeta: {Path.cwd().name} · semilla {seed}")
    return np.random.default_rng(seed)


def show(obj):
    """display() de Jupyter si existe; si no, imprime."""
    try:
        from IPython.display import display
        display(obj)
    except Exception:
        print(obj.to_string() if hasattr(obj, "to_string") else obj)


# ---------------------------------------------------------------- escenarios
def find_bench():
    """Return the local benchmark root, or ``None`` when it is unavailable."""
    return local_data_root(required=False)


@dataclass
class Scenario:
    name: str
    source: str                       # 'benchmark' | 'stand-in'
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    treatment: str | None
    outcome: str | None
    covariates: list
    meta: dict = field(default_factory=dict)
    _truth: dict = field(default_factory=dict)   # split -> DataFrame (SOLO evaluación)
    true_ate: float | None = None
    full: pd.DataFrame | None = None  # datos con variables latentes (solo evaluación)
    adj: np.ndarray | None = None     # matriz de adyacencia verdadera (solo evaluación)

    def split(self, which="train"):
        return {"train": self.train, "val": self.val, "validation": self.val, "test": self.test}[which]

    def xyt(self, which="train"):
        d = self.split(which)
        return d[self.covariates].to_numpy(float), d[self.outcome].to_numpy(float), d[self.treatment].to_numpy(float)

    def truth(self, which="train"):
        """EVALUACIÓN: ground truth. Úsalo solo en celdas marcadas # EVALUATION-CELL."""
        return self._truth.get(which)

    def tau(self, which="train"):
        """EVALUACIÓN: efecto individual verdadero, si el benchmark lo trae."""
        t = self._truth.get(which)
        if t is None:
            return None
        for c in ("tau", "ite", "cate", "true_ite", "true_cate", "tau_true", "effect", "true_effect"):
            if c in t.columns:
                return t[c].to_numpy(float)
        for a, b in (("y1", "y0"), ("mu1", "mu0"), ("Y1", "Y0"), ("y_1", "y_0"), ("y1_true", "y0_true")):
            if a in t.columns and b in t.columns:
                return (t[a] - t[b]).to_numpy(float)
        return None

    def card(self):
        d = self.train
        print("┌─ FICHA DEL ESCENARIO ─────────────────────────────────────────")
        print(f"│ {self.name}  [{self.source.upper()}]")
        print(f"│ filas train/val/test: {len(self.train)}/{len(self.val)}/{len(self.test)} · covariables: {len(self.covariates)}")
        if self.treatment:
            print(f"│ tratamiento: {self.treatment} · resultado: {self.outcome}")
            tt = d[self.treatment]
            if tt.nunique() == 2:
                print(f"│ tasa de tratamiento (train): {tt.mean():.4f}")
        origin = self.meta.get("data_origin", "SINTÉTICO")
        print(f"│ origen de los datos: {str(origin)[:90]}")
        if self.source == "stand-in":
            print("│ ⚠ MODO STAND-IN: no se encontró el benchmark; datos generados con la misma")
            print("│   estructura. Las cifras NO son las de tu repositorio. Define LAB_BENCH_ROOT.")
        print("└────────────────────────────────────────────────────────────────")


def _read(path):
    return pd.read_csv(path) if path.exists() else None


def _infer_roles(df, meta, name):
    drop = {"row_id", "id", "index", "unit_id"}
    t = meta.get("treatment_var") or next((c for c in ("treatment", "T", "t", "D", "w") if c in df.columns), None)
    y = meta.get("outcome_var") or next((c for c in ("outcome", "Y", "y", "re78") if c in df.columns), None)
    if name.endswith("latent_confounder"):
        t, y = meta.get("treatment_var", "X8"), meta.get("outcome_var", "X9")
    if "10_vars" in name:
        t = y = None
    cov = [c for c in df.columns if c not in drop | {t, y} and not c.startswith("truth_")]
    return t, y, cov


def load_scenario(name: str, allow_stand_in: bool = False) -> Scenario:
    """Load a repository scenario and keep ground truth evaluation-only.

    ``LAB_STAND_IN=1`` is the only implicit opt-in to the old synthetic
    fixtures. Normal course execution must use the local benchmark.
    """
    root = find_bench()
    if root is not None and (root / name).is_dir():
        bundle = load_local_bundle(name)
        sc = Scenario(
            bundle["name"], bundle["source"], bundle["train"], bundle["val"], bundle["test"],
            bundle["treatment"], bundle["outcome"], bundle["covariates"],
            {
                **bundle["meta"],
                "scenario_id": bundle["meta"].get("scenario_id", name.replace("/", "_")),
                "data_origin": bundle["meta"].get("data_origin", "BENCHMARK LOCAL DEL MONOREPO"),
                "identification": bundle["identification"],
                "scorecard": bundle["scorecard"],
                "splits": bundle["splits"],
                "data_root": str(root),
            },
            bundle["truth"], bundle["true_ate"], bundle["full"], bundle["adj"],
        )
        if sc.true_ate is None and sc.tau("train") is not None:
            sc.true_ate = float(np.mean(sc.tau("train")))
        return sc
    if allow_stand_in or os.environ.get("LAB_STAND_IN") == "1":
        return _stand_in(name)
    raise FileNotFoundError(
        f"No se encontró el escenario local {name!r}. "
        "Ejecuta desde la raíz del repositorio o define CAUSAL_REPO_ROOT/CAUSAL_DATA_ROOT. "
        "Para una demostración sin benchmark usa LAB_STAND_IN=1 explícitamente."
    )


# ---------------------------------------------------------------- stand-ins
def _sig(z):
    return 1 / (1 + np.exp(-z))


def _split_frames(df, truth, sizes, rng):
    idx = rng.permutation(len(df))
    out, tout, s = [], {}, 0
    for k, n in zip(("train", "val", "test"), sizes):
        ii = idx[s:s + n]; s += n
        out.append(df.iloc[ii].reset_index(drop=True))
        if truth is not None:
            tout[k] = truth.iloc[ii].reset_index(drop=True)
    return out, tout


def _stand_in(name):
    rng = np.random.default_rng(20261014)
    if name == "real/jobs":
        n = 1722
        age = rng.integers(18, 56, n).astype(float); educ = rng.integers(5, 18, n).astype(float)
        black = rng.binomial(1, .4, n); hisp = rng.binomial(1, .1, n); married = rng.binomial(1, .3, n)
        nodeg = (educ < 12).astype(int)
        re74 = np.clip(rng.normal(5000, 3000, n), 0, None); re75 = np.clip(0.6 * re74 + rng.normal(2000, 2500, n), 0, None)
        z = -1.2 - 0.00006 * re75 + 0.25 * nodeg + 0.2 * black - 0.01 * (age - 30)
        T = rng.binomial(1, _sig(z))
        y0 = 4500 + 0.5 * re75 + 120 * educ + rng.normal(0, 3500, n)
        tau = np.full(n, 1600.26)
        Y = y0 + T * tau
        df = pd.DataFrame(dict(row_id=np.arange(n), age=age, educ=educ, black=black, hispan=hisp, married=married,
                               nodegree=nodeg, re74=re74, re75=re75, treatment=T, re78=Y))
        tr = pd.DataFrame(dict(y0=y0, y1=y0 + tau, tau=tau))
        (a, b, c), tt = _split_frames(df, tr, (1033, 344, 345), rng)
        cov = [x for x in df.columns if x not in ("row_id", "treatment", "re78")]
        return Scenario(name, "stand-in", a, b, c, "treatment", "re78", cov,
                        {"data_origin": "STAND-IN sintético estilo LaLonde"}, tt, 1600.2576)
    if name in ("real/ihdp", "synthetic/inference/ihdp_medium"):
        medium = name.endswith("medium")
        n = 2000 if medium else 747
        sizes = (1200, 400, 400) if medium else (448, 149, 150)
        cont = ["bw", "b.head", "preterm", "birth.o", "nnhealth", "momage"]
        binar = ["sex", "twin", "b.marr", "mom.lths", "mom.hs", "mom.scoll", "cig", "first", "booze", "drugs",
                 "work.dur", "prenatal", "ark", "ein", "har", "mia", "pen", "tex", "was"]
        names = [f"x{i}" for i in range(25)] if medium else cont + binar
        Xc = rng.normal(size=(n, 6)); Xb = rng.binomial(1, rng.uniform(.2, .6, 19), size=(n, 19))
        X = np.column_stack([Xc, Xb]); df = pd.DataFrame(X, columns=names)
        z = 0.6 * Xc[:, 0] - 0.5 * Xc[:, 2] + 0.4 * Xb[:, 2] + 0.3 * Xc[:, 5] - 0.2
        T = rng.binomial(1, _sig(z - (0.0 if medium else .3)))
        mu0 = 2 + 0.9 * Xc[:, 0] + 0.5 * Xc[:, 5] + 0.6 * Xb[:, 4] + 0.4 * np.sin(Xc[:, 1] * 2)
        base = 3.5277 if medium else 3.918
        tau = base + 1.2 * Xc[:, 0] - 0.9 * (Xb[:, 0] - .5) + 0.6 * Xc[:, 2] * (Xb[:, 3])
        tau = tau - tau.mean() + base
        Y = mu0 + T * tau + rng.normal(0, 1, n)
        df["treatment"], df["outcome"] = T, Y
        df.insert(0, "row_id", np.arange(n))
        tr = pd.DataFrame(dict(y0=mu0, y1=mu0 + tau, tau=tau))
        (a, b, c), tt = _split_frames(df, tr, sizes, rng)
        return Scenario(name, "stand-in", a, b, c, "treatment", "outcome", names,
                        {"data_origin": "STAND-IN sintético estilo IHDP"}, tt, float(tau.mean()))
    if name.endswith("latent_confounder"):
        n = 2000
        X0 = rng.normal(size=n); Xo = rng.normal(size=(n, 7))
        X8 = 1.2 * X0 + 0.5 * Xo[:, 1] + rng.normal(0, .7, n)
        X9 = -1.8189 * X8 + 1.5 * X0 + 0.3 * Xo[:, 2] + rng.normal(0, .5, n)
        full = pd.DataFrame(np.column_stack([X0, Xo, X8, X9]), columns=[f"X{i}" for i in range(10)])
        full.insert(0, "row_id", np.arange(n))
        obs = full.drop(columns="X0")
        (a, b, c), _ = _split_frames(obs, None, (1200, 400, 400), rng)
        cov = [f"X{i}" for i in range(1, 8)]
        return Scenario(name, "stand-in", a, b, c, "X8", "X9", cov,
                        {"data_origin": "STAND-IN sintético lineal gaussiano con confusor latente X0",
                         "treatment_var": "X8", "outcome_var": "X9"}, {}, -1.8189, full=full)
    if "10_vars_10_edges" in name:
        d = 10; r2 = np.random.default_rng(7)
        order = r2.permutation(d)
        pairs = [(order[i], order[j]) for i in range(d) for j in range(i + 1, d)]
        pick = r2.choice(len(pairs), 10, replace=False)
        A = np.zeros((d, d))
        for k in pick:
            i, j = pairs[k]; A[i, j] = r2.choice([-1, 1]) * r2.uniform(.6, 1.4)
        n = 1000; E = rng.normal(size=(n, d))
        Xs = E @ np.linalg.inv(np.eye(d) - A)
        df = pd.DataFrame(Xs, columns=[f"X{i}" for i in range(d)]); df.insert(0, "row_id", np.arange(n))
        (a, b, c), _ = _split_frames(df, None, (600, 200, 200), rng)
        cov = [f"X{i}" for i in range(d)]
        return Scenario(name, "stand-in", a, b, c, None, None, cov,
                        {"data_origin": "STAND-IN lineal gaussiano, 10 nodos y 10 aristas"}, {}, None, adj=(A != 0).astype(float))
    raise KeyError(name)


# ---------------------------------------------------------------- estadística básica
def ols(y, X, const=True):
    """OLS con error estándar robusto HC1. Devuelve dict(coef, se, resid, names no incluidos)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    if X.ndim == 1: X = X[:, None]
    if const: X = np.column_stack([np.ones(len(X)), X])
    XtXi = np.linalg.pinv(X.T @ X)
    b = XtXi @ X.T @ y
    e = y - X @ b
    n, k = X.shape
    meat = (X * e[:, None]).T @ (X * e[:, None])
    V = XtXi @ meat @ XtXi * n / max(n - k, 1)
    return {"coef": b, "se": np.sqrt(np.diag(V)), "resid": e}


def diff_in_means(y, t):
    y = np.asarray(y, float); t = np.asarray(t)
    a, b = y[t == 1], y[t == 0]
    est = a.mean() - b.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return est, se


def ci95(est, se):
    return est - 1.96 * se, est + 1.96 * se


def fmt_ci(est, se, d=3):
    lo, hi = ci95(est, se)
    return f"{est:.{d}f} (IC95% [{lo:.{d}f}; {hi:.{d}f}])"


def kfold(n, K=5, seed=SEED):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(n)
    return [idx[i::K] for i in range(K)]


def bootstrap_se(fn, n, B=200, seed=SEED):
    rng = np.random.default_rng(seed)
    vals = np.array([fn(rng.integers(0, n, n)) for _ in range(B)])
    return vals.std(ddof=1), vals


def sha256_bytes(b: bytes) -> str:
    return "sha256:" + hashlib.sha256(b).hexdigest()


def sha256_df(df: pd.DataFrame) -> str:
    return sha256_bytes(df.to_csv(index=False).encode())


# ---------------------------------------------------------------- bitácora
TIPOS = ("observable", "falsificable", "no observable")
TRATOS = ("medido", "contrastado", "declarado y acotado")
DECISIONES = ("continuar", "alertar", "abstenerse", "revisar identificación", "reentrenar")
CAMPOS = ("pregunta", "metodo", "estimando", "numero_ic", "supuesto", "decision")


def supuesto(tipo: str, trato: str, resultado: str) -> str:
    assert tipo in TIPOS, f"tipo debe ser uno de {TIPOS}"
    assert trato in TRATOS, f"cómo se trató debe ser uno de {TRATOS}"
    assert len(resultado.strip()) >= 5, "describe el resultado"
    return f"{tipo} · {trato} · {resultado.strip()}"


def bitacora(pregunta, metodo, estimando, numero_ic, supuesto, decision, lab=""):
    """Valida y muestra la fila de bitácora (6 campos). Escribe bitacora_causal.md salvo LAB_NO_WRITE=1."""
    fila = dict(zip(CAMPOS, (pregunta, metodo, estimando, numero_ic, supuesto, decision)))
    for k, v in fila.items():
        assert isinstance(v, str) and v.strip(), f"Falta el campo «{k}»"
    parts = [p.strip() for p in supuesto.split("·")]
    assert len(parts) >= 3 and parts[0] in TIPOS and parts[1] in TRATOS, \
        "Supuesto clave = «tipo · cómo se trató · resultado» (usa supuesto())"
    assert decision in DECISIONES, f"decisión ∈ {DECISIONES}"
    md = f"\n### {lab}\n" + "\n".join(f"- **{k}:** {v}" for k, v in fila.items()) + "\n"
    log_path = Path(__file__).resolve().parent / "artefactos" / "bitacora_causal.md"
    if os.environ.get("LAB_NO_WRITE") != "1":
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(md)
    print("✔ Fila de bitácora válida" + ("" if os.environ.get("LAB_NO_WRITE") == "1" else f" y guardada en {log_path}"))
    for k, v in fila.items():
        print(f"  {k:10s}: {v}")
    return fila


def lab_check(nombre, fn, casos):
    """Comprobación ligera de una función del estudiante.
    casos: lista de (args(tuple), esperado, tol). Mensajes accionables; sin clave impresa."""
    mal = []
    for i, (args, esperado, tol) in enumerate(casos, 1):
        try:
            got = fn(*args)
            ok = np.allclose(got, esperado, atol=tol, rtol=tol, equal_nan=False)
        except NotImplementedError:
            raise
        except Exception as e:
            mal.append(f"caso {i}: error {type(e).__name__}: {e}"); continue
        if not ok:
            mal.append(f"caso {i}: el resultado no coincide con lo esperado")
    if mal:
        print(f"✘ {nombre}: " + " | ".join(mal))
        return
    print(f"✔ {nombre}: {len(casos)} caso(s) correcto(s)")


# ---------------------------------------------------------------- grafos (infraestructura; sin networkx)
def parents(adj, j):
    return [i for i in range(len(adj)) if adj[i][j] != 0]


def ancestors(adj, nodes):
    seen, stack = set(nodes), list(nodes)
    while stack:
        j = stack.pop()
        for i in parents(adj, j):
            if i not in seen:
                seen.add(i); stack.append(i)
    return seen


def dsep(adj, xs, ys, zs=()):
    """¿xs ⟂ ys | zs en el DAG `adj` (adj[i][j]≠0 ⇒ i→j)? Método de la moralización del grafo ancestral."""
    xs, ys, zs = set(xs), set(ys), set(zs)
    keep = ancestors(adj, xs | ys | zs)
    und = {v: set() for v in keep}
    for j in keep:
        ps = [p for p in parents(adj, j) if p in keep]
        for p in ps:
            und[p].add(j); und[j].add(p)
        for a in ps:
            for b in ps:
                if a != b:
                    und[a].add(b)
    seen, stack = set(), [v for v in xs if v not in zs]
    seen.update(stack)
    while stack:
        v = stack.pop()
        if v in ys:
            return False
        for w in und[v]:
            if w not in seen and w not in zs:
                seen.add(w); stack.append(w)
    return True


TRUTH_NAMES = {"y0", "y1", "tau", "ite", "cate", "mu0", "mu1", "true_ite", "true_cate", "tau_true", "propensity_true"}


def assert_no_truth(df, contexto=""):
    """Falla si el DataFrame contiene columnas de verdad (contrafactuales/efectos verdaderos)."""
    bad = [c for c in df.columns if str(c).startswith("truth_") or str(c).lower() in TRUTH_NAMES]
    assert not bad, f"{contexto}: columnas de verdad en las covariables: {bad}"


# ---------------------------------------------------------------- A2 (estimación reutilizable por los labs 11, 12, 17, 28)
def a2_fit(save: bool = False, outdir: str = "artefactos") -> dict:
    """Estimación A2 del curso: DML-PLR (K=5, ExtraTrees) sobre ihdp_medium (train).
    Devuelve el 'artefacto' (dict serializable). Con save=True lo escribe en ../<outdir>/a2.json
    (carpeta compartida por todos los labs; salvo LAB_NO_WRITE=1). Si ya existe, lo lee."""
    from sklearn.ensemble import ExtraTreesRegressor
    root_artifacts = Path(__file__).resolve().parent / outdir
    p = root_artifacts / "a2.json"
    for q in (p, Path(outdir) / "a2.json", Path("..") / outdir / "a2.json"):
        if q.exists():
            return json.loads(q.read_text(encoding="utf-8"))
    sc = load_scenario("synthetic/inference/ihdp_medium")
    X, y, t = sc.xyt("train")
    n = len(y); ry = np.zeros(n); rd = np.zeros(n)
    mk = lambda: ExtraTreesRegressor(n_estimators=60, min_samples_leaf=5, max_features=0.8, random_state=0)
    for te in kfold(n, 5, SEED):
        tr = np.setdiff1d(np.arange(n), te)
        ry[te] = y[te] - mk().fit(X[tr], y[tr]).predict(X[te])
        rd[te] = t[te] - mk().fit(X[tr], t[tr]).predict(X[te])
    th = float((rd * ry).sum() / (rd * rd).sum())
    psi_ = (ry - th * rd) * rd / np.mean(rd ** 2)
    se = float(np.sqrt(np.mean(psi_ ** 2) / n))
    cols = list(sc.covariates)
    art = {"version": "1.0", "scenario": sc.name, "origen_datos": sc.source, "estimando": "ATE (coeficiente PLR)",
           "metodo": "DML-PLR, K=5, ExtraTrees", "theta": th, "se": se, "ic95": [th - 1.96 * se, th + 1.96 * se],
           "n_train": n, "covariables": cols,
           "soporte": {c: [float(sc.train[c].min()), float(sc.train[c].max())] for c in cols},
           "hash_datos_entrenamiento": sha256_df(sc.train[cols + [sc.treatment, sc.outcome]]), "semilla": SEED}
    if save and os.environ.get("LAB_NO_WRITE") != "1":
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(art, ensure_ascii=False, indent=1), encoding="utf-8")
    return art
