# The Two-Clocks Bridge

**Do the two clocks agree?** Most evidence on digital life and youth wellbeing comes from yearly cohort waves (the *slow clock*). Daily studies such as measurement bursts and ecological momentary assessment (the *fast clock*) capture what happens hour to hour and day to day. The two are rarely compared directly, yet parents, clinicians and policymakers act on both. The Two-Clocks Bridge places yearly and daily evidence side by side for ages 18–25 and applies a preregistered evidence rule that says when each can guide decisions.

**Interactive page:** https://vas08011980.github.io/two-clocks-bridge/
**Author:** Vasileios Stavropoulos, RMIT University · [ORCID 0000-0001-6964-4662](https://orcid.org/0000-0001-6964-4662)
**Project:** Years and Moments, which links cohort trajectories (years) with daily digital experience (moments) across adolescence and early adulthood.

> **Simulated data only.** This release runs on simulated inputs with known true effects (`bridge/simulate.py`). It shows how the bridge operates and lets the decision rule be checked against the truth. No cohort data are included.

---

## Aim

To test whether the within-person associations between digital engagement and wellbeing seen across yearly cohort waves match those seen across days in the same age range, and to give a transparent rule for when yearly evidence can stand in for daily processes and when it cannot.

## How it works

The bridge has three steps.

### 1. Placement: is the daily sample typical of its generation?

Daily studies usually recruit smaller, self-selected samples. Each burst participant is placed on the distribution of a shared instrument (here, K6 distress and 0–10 life satisfaction) in each cohort, matched on age and the nearest available survey year. The output is a percentile for every participant, the share above the 90th and below the 10th percentile, and the Kolmogorov–Smirnov distance to the cohort distribution. Reference cohorts in the demonstration: the Longitudinal Study of Australian Children (LSAC), Understanding Society (UK Household Longitudinal Study) and the Household, Income and Labour Dynamics in Australia Survey (HILDA). The number of years each reference is carried forward is reported, because a 2024 distribution may not describe a later sample.

### 2. Concordance: do the two clocks give the same within-person effect?

For each exposure–outcome pair and two-year age band (18–19, 20–21, 22–23, 24–25):

- **Slow clock.** The standardised within-person effect is estimated from yearly waves in each cohort (person-mean centring, person-clustered robust SEs) and pooled across cohorts with DerSimonian–Laird random effects.
- **Fast clock.** The same standardised within-person effect is estimated from daily data.
- **Evidence rule.** With *d* = yearly − daily:

| Verdict | Condition | Guidance |
|---|---|---|
| Undetermined | either 95% CI half-width > 0.10 | Not enough precision to decide; collect more data before using either. |
| Agree | 90% CI of *d* within ±0.05 (two one-sided tests) | Yearly cohort evidence can stand in for daily processes. |
| Diverge | both significant with opposite signs, or *d* significant otherwise | Rely on daily evidence; yearly evidence may mislead. |
| Same direction, different size | both significant, same sign, *d* significant | Yearly evidence gives the direction; use daily evidence for the size. |
| Undetermined | none of the above | Not enough precision to decide. |

The margin (±0.05 standardised units) and the precision threshold (0.10) are set in `bridge/bridge.py` and are meant to be fixed in a preregistration before real data are analysed.

### 3. Same-youth replication outside Australia

Where young people have donated their own digital histories and these are linked to their cohort survey waves, the person's daily reactivity (their within-person slope) is tested as a predictor of wellbeing at the next wave, adjusting for the previous wave. Estimates from the Trondheim Early Secure Study (TESS, Norway) and the new AStRA cohort (Greece) are compared with the Australian burst estimate (Cochran's Q, and whether each overseas estimate falls inside the Australian 95% range). A finding *replicates* when every overseas estimate is positive and within that range.

## What the simulation plants

| Pair | Daily truth | Yearly truth | Expected verdict |
|---|---|---|---|
| Social media use → life satisfaction | −.08 to −.07 | −.07 to −.06 | Agree (where precise enough) |
| Gaming → distress | .05 to .04 | .16 to .13 | Same direction, different size |
| AI companionship → loneliness | −.12 to −.06 | .12 to .05 | Diverge |
| Night-time use → low mood | .06 to .04 | .04 to .03 | Undetermined (effects too small for the daily samples to resolve) |

## Results with seed 2026

- **Concordance:** 2 agree, 4 same direction, 4 diverge, 6 undetermined (16 cells). The rule recovers the planted patterns. Social media becomes undetermined from age 22 as burst samples shrink; AI companionship diverges in every band (daily ≈ −.09 to −.12; yearly ≈ +.09 to +.13).
- **Placement:** the simulated burst sample is more distressed than the cohorts (median K6 percentile 68–71; 20–25% above the cohort 90th percentile, against 10% expected). Reference years are carried forward 5–6 years.
- **Replication:** AI companionship → loneliness replicates in TESS (.151, SE .036) and AStRA (.105, SE .047) against the Australian estimate (.064, SE .047). Social media does not yet replicate, because the TESS 95% CI includes zero.

Full outputs are in `results/` (`concordance.csv`, `placement.csv`, `replication.csv`, `bridge_results.json`).

## Run it

```bash
pip install -r requirements.txt
./run.sh 2026          # or: python bridge/bridge.py --seed 2026 && python bridge/build_page.py
```

`docs/index.html` is updated in place with the new results embedded, so the page works offline and on GitHub Pages.

## Repository layout

```
bridge/simulate.py     simulated slow-clock, fast-clock, placement and donor inputs (known truth)
bridge/bridge.py       estimation, evidence rule, placement and replication
bridge/build_page.py   embeds results into the interactive page
docs/                  interactive page (GitHub Pages)
results/               outputs for seed 2026
```

## Using it with real data

Replace the functions in `simulate.py` with loaders that return the same structures: person × occasion arrays of exposure and outcome for each source and age band, shared-instrument scores by source, age and year, and linked donor slopes with adjacent waves. Cohort data are accessed under each study's own data-use agreement and are never stored in this repository.

## Limitations of this release

- Inputs are simulated from a linear within-person model with normal errors, equal spacing of occasions and no missing data. Real yearly waves are unequally spaced and attrition is not random.
- The fast clock is simulated as about 36 usable days per person with independent occasions; autocorrelation, time-of-day effects and reactivity to measurement are not modelled.
- Yearly and daily effects are compared on a standardised scale. Equal standardised effects need not mean the same process, because yearly and daily variance differ in what they contain.
- Placement assumes the shared instrument is measured equivalently across cohorts, countries and years. In practice this needs measurement-invariance testing first.
- The replication step treats a person's donated daily slope as an observed predictor; its reliability is set at .50–.55 in the simulation and will need to be estimated from real data.
- None of the steps supports causal claims; each compares associations measured on two time scales.

## Citation

See `CITATION.cff`. Stavropoulos, V. (2026). *The Two-Clocks Bridge: do yearly and daily evidence on digital life and youth wellbeing agree?* (Version 0.1.0) [Software]. https://github.com/Vas08011980/two-clocks-bridge

## Licence

MIT © 2026 Vasileios Stavropoulos
