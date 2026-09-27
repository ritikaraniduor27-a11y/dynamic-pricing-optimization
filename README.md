# Dynamic Pricing & Revenue Management Optimization for On-Demand Platforms

An end-to-end Operations Research + Data Science project simulating and solving the dynamic (surge) pricing problem faced by ride-hailing / delivery platforms (Uber, Ola, Swiggy-style marketplaces). The project spans synthetic data engineering, SQL analytics, causal price-elasticity estimation, constrained mathematical optimization, policy evaluation, and an executive Power BI dashboard.

---

## Business Problem

On-demand platforms must set a price multiplier for every (zone, hour) that balances two competing forces:

- **Underpricing** → demand outstrips supply, wait times rise, drivers idle out and churn.
- **Overpricing** → revenue per trip rises but conversion drops, customers churn, and the platform loses share.

**Goal:** Determine the price multiplier `P(z,t)` that maximizes net platform revenue, subject to fairness, churn, driver-payout, and supply-retention constraints — replacing the naive "raise price whenever demand > supply" heuristic most rule-based systems use.

---

## Project Structure (5 Phases)

| Phase | Deliverable |
|---|---|
| 1. Problem Definition & Data Generation | Synthetic dataset generator with realistic, ground-truth price elasticity baked in |
| 2. SQL Analytics & Elasticity Estimation | Analytical SQL layer + naive vs. fixed-effects (causal) elasticity regression |
| 3. Mathematical Optimization | Constrained NLP (SciPy) and discrete-tier MILP (PuLP) formulations |
| 4. Comparative Evaluation | Static vs. Rule-Based vs. OR-Optimized policy simulation and business impact |
| 5. Executive Dashboard | 4-page Power BI dashboard + resume-ready impact metrics |

---

## Phase 1 — Data Generation

Since real platform pricing data is proprietary, a config-driven synthetic simulator was built to generate **6,480 hourly records** across:

- 3 zones (`Downtown_CBD`, `Airport_Corridor`, `Suburban_Residential`) × 90 days × 24 hours
- Weekday/weekend and time-of-day demand-supply seasonality
- Weather/traffic shocks with daily persistence
- 3 customer segments blended into a single observable `conversion_rate`, with distinct **ground-truth elasticities**: business (-0.45), leisure (-1.10), price-sensitive (-1.85)
- A rule-based surge baseline (`1.0 + 0.6 × gap_ratio`, floored at 1.0x) already applied — this is the "as-is" policy later phases beat

**Design intent:** elasticity is deliberately not labeled in the output, so Phase 2's estimation is a genuine recovery exercise, not a lookup.

---

## Phase 2 — SQL Analytics & Price Elasticity

### SQL Findings (SQLite/MySQL)
- Surge-priced hours are only **~46%** of all hours but generate **77%** of total revenue (Pareto pattern).
- Surge pricing costs **28–37% conversion** depending on zone (Downtown/Airport lose more than Suburban).
- Rain simultaneously raises the demand-supply gap ratio (0.425 vs. 0.243 in clear weather) and suppresses conversion — a compounding-risk period.

### Elasticity Estimation — Naive vs. Fixed-Effects (Causal)
Because surge was set *based on* the demand-supply gap, price and demand are jointly determined — a naive regression is endogenous and biases elasticity toward zero. A fixed-effects correction was used to isolate the causal effect.

| Method | Estimated Elasticity |
|---|---|
| Naive OLS | -1.031 |
| Fixed-Effects (causal) | -1.016 |
| **True (ground-truth)** | **-1.00 to -1.85 (segment-blended)** |

**Documented limitation:** the peak vs. off-peak elasticity split came back nearly flat (-0.99 to -1.05 across all zones/periods) because segment mix was held constant across hours in the generator — "peak hour" wasn't actually a valid proxy for "more business travelers" in this dataset. Flagged and kept as an honest finding rather than patched retroactively.

---

## Phase 3 — Mathematical Optimization

**Objective:** `max Σ P(z,t) · base_fare · C(z,t)`

**Decision variables:** `P(z,t)` (price multiplier), `C(z,t)` (completed trips, introduced as its own variable bounded by both demand-side and supply-side caps to avoid a non-differentiable `min()` kink).

**Constraints:** fairness bounds (0.8x–3.0x), demand-side and supply-side caps, minimum fulfillment, maximum churn tolerance, driver payout floor, minimum daily supply retention, and price smoothness (bounded hour-to-hour change).

Two independent solvers were built and cross-validated:
- **Continuous NLP** (SciPy `trust-constr`)
- **Discrete-tier MILP** (PuLP/CBC, 7 fixed surge tiers — matching how real platforms publish surge levels)

**Result:** both formulations agree on total revenue to within **0.15%** — strong evidence both are correctly implemented.

**Debugging story worth noting:** the first SLSQP solver run failed to converge everywhere. Root cause: `Suburban_Residential`'s near-unit elasticity (~-1.02) makes revenue essentially flat in price — a genuine economic finding, not a bug. Fixed via a tie-breaker regularization (prefer lower price when revenue is indifferent) and a feasibility check that doesn't blindly trust the solver's raw success flag.

---

## Phase 4 — Policy Comparison & Business Impact

All three policies were evaluated through the *same* demand-response model for a fair comparison (rather than comparing against raw historical data reflecting a different pricing regime).

| Policy | Total Daily Revenue | Avg Surge | Fulfillment | Driver Utilization | Churn Risk |
|---|---|---|---|---|---|
| Static (1.0x always) | ₹588,766 | 1.00x | 63.2% | 62.3% | 2.00% |
| Rule-Based Surge (as-is) | ₹643,073 | 1.29x | 54.5% | 49.0% | 2.76% |
| **OR-Optimized (SciPy NLP)** | **₹645,666** | **1.06x** | **63.1%** | **62.2%** | **2.08%** |
| OR-Optimized (PuLP MILP) | ₹645,654 | 1.18x | 58.7% | 56.0% | 2.44% |

### Headline Result
- **+9.7% revenue vs. static pricing**
- **+0.4% revenue vs. the already-competent rule-based baseline** — a small, credible number consistent with pricing literature (most theoretical value of dynamic pricing is captured by a reasonable heuristic)

### The Real Story: Operational Health, Not Just Revenue
At near-identical revenue to rule-based, the OR-optimized policy delivers:
- **+8.6pp fulfillment rate** (more interested customers served)
- **+13pp driver utilization** (49% → 62%, directly reducing driver idle-time churn)
- **-0.7pp churn risk**

**Notable finding:** in `Suburban_Residential` (Weekday), the rule-based policy actually *destroys value* relative to doing nothing (₹58,268 vs. ₹58,519 static) — it surges on any demand-supply gap, even in an oversupplied zone. The optimizer correctly recognizes this and pulls price down, beating rule-based by +0.72% there. **This is the core value of optimization over heuristics: knowing when *not* to surge.**

### Caveats (documented, not hidden)
- Driver supply is modeled as price-independent; a true supply-elasticity model would likely amplify utilization gains further.
- Elasticity used is the Phase 2 blended-market estimate, not true per-segment personalization.
- The rule-based baseline was deliberately built to be competent, not a strawman — this is why the uplift is modest and credible.

---

## Phase 5 — Executive Dashboard (Power BI)

A 4-page interactive dashboard built on a star-schema data model (fact tables: raw hourly ops + policy comparison; shared dimensions: zone, hour, policy):

1. **Executive Summary** — headline KPI cards (Total Revenue, Revenue Uplift vs. Static/Rule-Based, Fulfillment, Utilization, Churn) + policy revenue comparison
2. **Demand-Supply Diagnostics** — zone × hour gap-ratio heatmap, surge frequency by zone, conversion-during-surge KPI
3. **Elasticity Model** — estimated elasticity by zone/period, conversion-rate decay curve vs. surge multiplier
4. **Policy Comparison** — hourly revenue by policy (interactive zone/day-type slicers), fulfillment/utilization/churn side-by-side

*(Insert dashboard screenshots here — e.g. `/screenshots/page1_executive_summary.png`, etc.)*

---

## Resume Bullets (XYZ Formula)

> Designed and deployed a dynamic pricing optimization system for a simulated ride-hailing marketplace, increasing revenue 9.7% over static pricing by building a constrained nonlinear optimization model (SciPy) driven by empirically-estimated price elasticity of demand across 3 geographic zones.

> Improved marketplace operational health without sacrificing revenue — raising driver utilization by 13 percentage points (49%→62%) and cutting customer churn risk by 0.7pp — by reformulating a heuristic surge-pricing policy as a fairness- and supply-constrained optimization problem, cross-validated across two independent solvers (SciPy NLP and PuLP MILP, agreeing within 0.15%).

> Quantified price elasticity of demand across zones and time periods using log-log fixed-effects regression on 6,480 hours of operational data, identifying a demand-driven pricing policy that was actively destroying value in one low-density zone — a finding that directly informed the optimization's constraint design.

---

## Tech Stack

`Python` (pandas, numpy, scipy, pulp) · `SQL` (SQLite / MySQL) · `Power BI` (DAX, star schema)

## Repository Structure

```
├── phase1_data_generation/
│   ├── generate_dynamic_pricing_data.py
│   └── dynamic_pricing_synthetic_data.csv
├── phase2_sql_elasticity/
│   ├── phase2_queries.sql
│   ├── run_phase2_sql.py
│   ├── phase2_price_elasticity.py
│   └── phase2_elasticity_estimates.csv
├── phase3_optimization/
│   ├── phase3_scenario_params.py
│   ├── phase3_optimization_scipy.py
│   ├── phase3_optimization_pulp.py
│   ├── phase3_scipy_optimal_pricing.csv
│   └── phase3_pulp_optimal_pricing.csv
├── phase4_evaluation/
│   ├── phase4_comparison.py
│   ├── phase4_scenario_comparison.csv
│   ├── phase4_hourly_comparison.csv
│   └── phase4_aggregate_comparison.csv
├── phase5_dashboard/
│   └── dynamic_pricing_dashboard.pbix
└── README.md
```

## How to Reproduce

```bash
pip install pandas numpy scipy pulp==2.8.0

python phase1_data_generation/generate_dynamic_pricing_data.py
python phase2_sql_elasticity/run_phase2_sql.py
python phase2_sql_elasticity/phase2_price_elasticity.py
python phase3_optimization/phase3_scenario_params.py
python phase3_optimization/phase3_optimization_scipy.py
python phase3_optimization/phase3_optimization_pulp.py
python phase4_evaluation/phase4_comparison.py
```

Open `phase5_dashboard/dynamic_pricing_dashboard.pbix` in Power BI Desktop for the interactive dashboard.
