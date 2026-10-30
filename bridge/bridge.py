"""The Two-Clocks Bridge: do yearly (slow-clock) and daily (fast-clock) evidence agree?

Three steps, run on whatever inputs are supplied (here: simulate.py):
  1. Placement   - where each fast-clock participant sits on cohort distributions of a shared
                   instrument for the same age and year (is the burst sample typical?).
  2. Concordance - for each exposure-outcome pair and age band, the standardised within-person
                   effect from yearly cohort waves is compared with the one from daily data, and a
                   preregistered evidence rule returns a verdict on whether yearly evidence can
                   stand in for daily processes.
  3. Same-youth replication - where young people's donated digital histories are linked to their
                   cohort waves, the same daily indicator is tested as a predictor of later
                   wellbeing outside Australia.
Usage: python bridge/bridge.py --seed 2026 --out results
"""
import argparse, json, os
import numpy as np, pandas as pd
from scipy import stats
import simulate as sim

DELTA = .05       # equivalence margin for standardised within-person effects
MAX_HALF = .10    # an estimate whose 95% CI half-width exceeds this is too imprecise to judge


# ---------- estimation ------------------------------------------------------------------------
def within_effect(x, y):
    """Standardised within-person effect with person-cluster-robust SE (x, y: persons x occasions)."""
    xw = x - x.mean(1, keepdims=True); yw = y - y.mean(1, keepdims=True)
    xw, yw = xw / xw.std(), yw / yw.std()
    b = (xw * yw).sum() / (xw ** 2).sum()
    u = (xw * (yw - b * xw)).sum(1)                      # person-level scores
    n = x.shape[0]
    se = np.sqrt((u ** 2).sum() * n / (n - 1)) / (xw ** 2).sum()
    return b, se


def pool(est):
    """DerSimonian-Laird random-effects pooling of (b, se) pairs."""
    b = np.array([e[0] for e in est]); v = np.array([e[1] ** 2 for e in est])
    if len(b) == 1:
        return b[0], np.sqrt(v[0]), 0.0
    w = 1 / v; bf = (w * b).sum() / w.sum(); q = (w * (b - bf) ** 2).sum()
    tau2 = max(0, (q - (len(b) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    ws = 1 / (v + tau2)
    return (ws * b).sum() / ws.sum(), np.sqrt(1 / ws.sum()), tau2


# ---------- evidence rule -----------------------------------------------------------------------
def verdict(bd, sd, by, sy):
    """Preregistered rule comparing daily (bd, sd) with yearly (by, sy) evidence."""
    diff, sdiff = by - bd, np.hypot(sd, sy)
    z90, z95 = stats.norm.ppf(.95), stats.norm.ppf(.975)
    lo90, hi90 = diff - z90 * sdiff, diff + z90 * sdiff
    lo95, hi95 = diff - z95 * sdiff, diff + z95 * sdiff
    sig_d = abs(bd) > z95 * sd; sig_y = abs(by) > z95 * sy
    if z95 * max(sd, sy) > MAX_HALF:
        v = "undetermined"
    elif -DELTA < lo90 and hi90 < DELTA:
        v = "agree"
    elif sig_d and sig_y and np.sign(bd) != np.sign(by):
        v = "diverge"
    elif (lo95 > 0 or hi95 < 0) and np.sign(bd) == np.sign(by) and sig_d and sig_y:
        v = "same_direction"
    elif (lo95 > 0 or hi95 < 0):
        v = "diverge"
    else:
        v = "undetermined"
    return v, diff, lo95, hi95


GUIDANCE = {
    "agree": "Yearly cohort evidence can stand in for daily processes.",
    "same_direction": "Yearly evidence gives the direction; use daily evidence for the size.",
    "diverge": "Rely on daily evidence; yearly evidence may mislead.",
    "undetermined": "Not enough precision to decide; collect more data before using either.",
}


# ---------- steps -------------------------------------------------------------------------------
def concordance(rng):
    slow, fast = sim.slow_clock(rng), sim.fast_clock(rng)
    cells = []
    for exp, out, label in sim.PAIRS:
        for band in sim.AGE_BANDS:
            ys = [r for r in slow if r["exposure"] == exp and r["age_band"] == band]
            per_src = {r["source"]: within_effect(r["x"], r["y"]) for r in ys}
            by, sy, tau2 = pool(list(per_src.values()))
            f = next(r for r in fast if r["exposure"] == exp and r["age_band"] == band)
            bd, sd = within_effect(f["x"], f["y"])
            v, diff, lo, hi = verdict(bd, sd, by, sy)
            cells.append({"pair": label, "exposure": exp, "outcome": out, "age_band": band,
                          "daily": round(bd, 3), "daily_se": round(sd, 3),
                          "yearly": round(by, 3), "yearly_se": round(sy, 3), "tau2": round(tau2, 4),
                          "yearly_sources": {k: [round(b, 3), round(s, 3)] for k, (b, s) in per_src.items()},
                          "n_fast": sim.FAST_N[band],
                          "diff": round(diff, 3), "diff_lo": round(lo, 3), "diff_hi": round(hi, 3),
                          "verdict": v, "guidance": GUIDANCE[v],
                          "true_daily": sim.TRUE[exp]["daily"][sim.AGE_BANDS.index(band)],
                          "true_yearly": sim.TRUE[exp]["yearly"][sim.AGE_BANDS.index(band)]})
    return cells


def placement(rng):
    ref, fast = sim.placement_inputs(rng)
    rows, summ = [], []
    for src in ref.source.unique():
        r = ref[ref.source == src]; last = r.year.max()
        for inst in ["k6", "life_satisfaction"]:
            pct = []
            for _, p in fast.iterrows():
                yr = min(p.year, last)                                  # nearest available year
                d = r[(r.age == p.age) & (r.year == yr)][inst].values
                pct.append(stats.percentileofscore(d, p[inst], kind="mean"))
            pct = np.array(pct)
            ks = stats.ks_2samp(fast[inst], r[r.year == last][inst]).statistic
            summ.append({"source": src, "instrument": inst, "reference_year": int(last),
                         "years_carried_forward": int(fast.year.max() - last),
                         "median_percentile": round(float(np.median(pct)), 1),
                         "share_above_p90": round(float((pct > 90).mean()), 3),
                         "share_below_p10": round(float((pct < 10).mean()), 3),
                         "ks_distance": round(float(ks), 3),
                         "hist": np.histogram(pct, bins=10, range=(0, 100))[0].tolist()})
    return summ


def replication(rng):
    res = []
    for d in sim.donors(rng):
        s = (d["slope"] - d["slope"].mean()) / d["slope"].std()
        X = np.column_stack([np.ones_like(s), d["w0"], s])
        beta, *_ = np.linalg.lstsq(X, d["w1"], rcond=None)
        resid = d["w1"] - X @ beta
        cov = np.linalg.inv(X.T @ X) * (resid ** 2).sum() / (len(s) - 3)
        res.append({"site": d["site"], "exposure": d["exposure"], "n": int(len(s)),
                    "b": round(float(beta[2]), 3), "se": round(float(np.sqrt(cov[2, 2])), 3)})
    out = []
    for exp in sorted({r["exposure"] for r in res}):
        rr = [r for r in res if r["exposure"] == exp]
        au = next(r for r in rr if r["site"].startswith("Australia"))
        others = [r for r in rr if r is not au]
        b = np.array([r["b"] for r in rr]); w = 1 / np.array([r["se"] for r in rr]) ** 2
        q = float((w * (b - (w * b).sum() / w.sum()) ** 2).sum()); p_q = float(1 - stats.chi2.cdf(q, len(b) - 1))
        for r in others:   # does the overseas estimate fall inside the Australian 95% prediction range?
            r["within_australian_range"] = bool(abs(r["b"] - au["b"]) < 1.96 * np.hypot(r["se"], au["se"]))
        out.append({"exposure": exp, "estimates": rr, "Q": round(q, 2), "p_heterogeneity": round(p_q, 3),
                    "replicates": all(r["within_australian_range"] and r["b"] - 1.96 * r["se"] > 0 for r in others)})
    return out


def main(seed=2026, out="results"):
    rng = np.random.default_rng(seed)
    res = {"seed": seed, "rule": {"delta": DELTA, "max_ci_half_width": MAX_HALF, "guidance": GUIDANCE},
           "age_bands": sim.AGE_BANDS, "concordance": concordance(rng),
           "placement": placement(rng), "replication": replication(rng)}
    os.makedirs(out, exist_ok=True)
    json.dump(res, open(f"{out}/bridge_results.json", "w"), separators=(",", ":"))
    pd.DataFrame([{k: v for k, v in c.items() if k != "yearly_sources"} for c in res["concordance"]]) \
        .to_csv(f"{out}/concordance.csv", index=False)
    pd.DataFrame([{k: v for k, v in p.items() if k != "hist"} for p in res["placement"]]).to_csv(f"{out}/placement.csv", index=False)
    pd.DataFrame([dict(e, exposure=r["exposure"]) for r in res["replication"] for e in r["estimates"]]) \
        .to_csv(f"{out}/replication.csv", index=False)
    v = pd.Series([c["verdict"] for c in res["concordance"]]).value_counts().to_dict()
    print("verdicts:", v)


if __name__ == "__main__":
    a = argparse.ArgumentParser(); a.add_argument("--seed", type=int, default=2026); a.add_argument("--out", default="results")
    main(**vars(a.parse_args()))
