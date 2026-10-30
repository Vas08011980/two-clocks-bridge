"""Simulated inputs for the Two-Clocks Bridge (no real data).

Generates three ingredients, each with known true values so the bridge can be checked:
  1. Slow clock: yearly panel waves for ages 18-25 in three cohorts/panels
     (LSAC, Understanding Society, HILDA), with a shared distress instrument (K6 items)
     and life satisfaction (0-10).
  2. Fast clock: an Australian measurement-burst study (4 bursts x 14 days) in 18-25-year-olds.
  3. Same-youth donors: young people in TESS (Norway) and the new AStRA cohort (Greece)
     whose donated digital histories are linked to their survey waves.
True within-person effects are set per exposure-outcome pair and age band so that the
bridge meets every verdict it can return (agree, same direction/different size, diverge,
undetermined).
"""
import numpy as np, pandas as pd

AGE_BANDS = ["18-19", "20-21", "22-23", "24-25"]
PAIRS = [  # exposure, outcome, label
    ("social_media", "life_satisfaction", "Social media use → life satisfaction"),
    ("gaming", "distress", "Gaming → distress"),
    ("ai_companion", "loneliness", "AI companionship → loneliness"),
    ("night_use", "low_mood", "Night-time use → low mood"),
]
# True standardised within-person effects: [daily (fast clock), yearly (slow clock)] per age band
TRUE = {
    "social_media":  {"daily": [-.08, -.08, -.07, -.07], "yearly": [-.07, -.07, -.07, -.06]},
    "gaming":        {"daily": [.05, .05, .04, .04],      "yearly": [.16, .15, .14, .13]},
    "ai_companion":  {"daily": [-.12, -.10, -.08, -.06],  "yearly": [.12, .10, .08, .05]},
    "night_use":     {"daily": [.06, .05, .05, .04],      "yearly": [.04, .04, .03, .03]},
}
# Which slow-clock sources measure each pair (loneliness and AI companionship are rare in cohorts)
SOURCES = {
    "social_media": ["LSAC", "Understanding Society", "HILDA"],
    "gaming": ["LSAC", "Understanding Society", "HILDA"],
    "ai_companion": ["Understanding Society"],
    "night_use": ["LSAC"],
}
SLOW_N = {"LSAC": 700, "Understanding Society": 900, "HILDA": 350}   # persons per age band with >=3 waves
FAST_N = {"18-19": 90, "20-21": 80, "22-23": 70, "24-25": 60}       # completers per age band
DONORS = {"TESS (Norway)": 420, "AStRA new cohort (Greece)": 300}


def panel(rng, n, t, beta, ar=.3):
    """Within-person panel: n persons x t occasions; returns standardised x, y and person ids."""
    a = rng.normal(0, 1, n)[:, None]
    x = rng.normal(0, 1, (n, t)) + .5 * a
    e = rng.normal(0, 1, (n, t))
    xw = x - x.mean(1, keepdims=True)
    y = a + beta / xw.std() * xw + e
    return x, y


def slow_clock(rng):
    rows = []
    for exp, out, _ in PAIRS:
        for b, band in enumerate(AGE_BANDS):
            for src in SOURCES[exp]:
                x, y = panel(rng, SLOW_N[src], 4, TRUE[exp]["yearly"][b])
                rows.append({"exposure": exp, "outcome": out, "age_band": band, "source": src,
                             "x": x, "y": y})
    return rows


def fast_clock(rng):
    rows = []
    for exp, out, _ in PAIRS:
        for b, band in enumerate(AGE_BANDS):
            x, y = panel(rng, FAST_N[band], 36, TRUE[exp]["daily"][b])  # ~36 usable days (4 x 14 at 65%)
            rows.append({"exposure": exp, "outcome": out, "age_band": band, "x": x, "y": y})
    return rows


def placement_inputs(rng):
    """Shared-instrument scores: cohort reference distributions by age and year, and fast-clock baseline."""
    ref = []
    years = {"LSAC": range(2017, 2025, 2), "Understanding Society": range(2017, 2025), "HILDA": range(2017, 2025)}
    for src, yrs in years.items():
        for yr in yrs:
            for age in range(18, 26):
                n = {"LSAC": 380, "Understanding Society": 260, "HILDA": 120}[src]
                shift = .06 * (yr - 2017) - .04 * (age - 18)          # distress rising by year, easing with age
                k6 = np.clip(np.round(rng.gamma(2.2 + shift, 2.6, n)), 0, 24)
                ls = np.clip(np.round(rng.normal(7.3 - .08 * (yr - 2017), 1.6, n)), 0, 10)
                ref.append(pd.DataFrame({"source": src, "year": yr, "age": age, "k6": k6, "life_satisfaction": ls}))
    ref = pd.concat(ref, ignore_index=True)
    n = sum(FAST_N.values())
    age = rng.integers(18, 26, n)
    # service-linked recruitment: a somewhat more distressed sample than the population panels
    fast = pd.DataFrame({"pid": [f"F{i+1:03d}" for i in range(n)], "age": age, "year": 2029,
                         "k6": np.clip(np.round(rng.gamma(3.0, 2.8, n)), 0, 24),
                         "life_satisfaction": np.clip(np.round(rng.normal(6.6, 1.8, n)), 0, 10)})
    return ref, fast


def donors(rng):
    """Same-youth replication: daily process (donated data) at a wave predicting the next survey wave."""
    out = []
    true_bridge = {"ai_companion": .14, "social_media": .10}   # person's daily reactivity -> later wellbeing decline
    for site, n in DONORS.items():
        for exp, beta in true_bridge.items():
            slope_true = rng.normal(0, 1, n)
            reliab = .55 if site.startswith("TESS") else .5                 # donated histories are noisier than EMA
            slope_obs = np.sqrt(reliab) * slope_true + np.sqrt(1 - reliab) * rng.normal(0, 1, n)
            w0 = rng.normal(0, 1, n)
            w1 = .6 * w0 + beta * slope_true + rng.normal(0, np.sqrt(1 - .36 - beta**2), n)
            out.append({"site": site, "exposure": exp, "slope": slope_obs, "w0": w0, "w1": w1})
    # Australian fast-clock estimate of the same bridge (from the measurement-burst study)
    for exp, beta in true_bridge.items():
        n = 300
        s = rng.normal(0, 1, n); so = np.sqrt(.7) * s + np.sqrt(.3) * rng.normal(0, 1, n)
        w0 = rng.normal(0, 1, n); w1 = .6 * w0 + beta * s + rng.normal(0, np.sqrt(1 - .36 - beta**2), n)
        out.append({"site": "Australia (measurement bursts)", "exposure": exp, "slope": so, "w0": w0, "w1": w1})
    return out
