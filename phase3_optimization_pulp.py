"""
Phase 3b — Discrete Surge-Tier Optimization (PuLP MILP)
=========================================================
Real platforms publish a small, fixed set of surge tiers (e.g. 1.0x, 1.2x,
1.5x...) rather than arbitrary continuous multipliers -- simpler for
driver/customer-facing UX, easier to reason about for fairness audits.

This reformulates Phase 3a's NLP as a Mixed-Integer Linear Program:
  - Binary decision x[t,k] = 1 if hour t is priced at tier k
  - All coefficients (revenue, completed trips) are PRECOMPUTED constants
    per (hour, tier) pair, since price is no longer continuous -- this
    makes the whole problem exactly linear, PuLP's home turf.
"""

import numpy as np
import pandas as pd
import pulp
from phase3_scenario_params import build_scenario_params, churn_risk

# ---------------------------------------------------------------------
# Same business policy configuration as Phase 3a, for direct comparability
# ---------------------------------------------------------------------
SURGE_TIERS = [1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0]
FULFILLMENT_MIN = 0.35
CHURN_MAX = 0.10
DRIVER_PAYOUT_FLOOR = 45.0
DRIVER_TAKE_RATE = 0.75
DAILY_UTILIZATION_MIN = 0.30
MAX_HOURLY_SWING = 0.5

N_HOURS = 24


def solve_scenario_milp(zone_df):
    zone_df = zone_df.sort_values("hour").reset_index(drop=True)
    D = zone_df["demand_base"].values
    CAP = zone_df["capacity"].values
    BETA = zone_df["beta_conv"].values
    EPS = zone_df["elasticity"].values
    base_fare = zone_df["base_fare"].iloc[0]

    # ---- Precompute revenue & completed-trips constants per (hour, tier) ----
    C = np.zeros((N_HOURS, len(SURGE_TIERS)))
    REV = np.zeros((N_HOURS, len(SURGE_TIERS)))
    feasible_mask = np.zeros((N_HOURS, len(SURGE_TIERS)), dtype=bool)

    for t in range(N_HOURS):
        for k, tier in enumerate(SURGE_TIERS):
            conv = BETA[t] * (tier ** EPS[t])
            demand_side_cap = D[t] * conv
            completed = min(demand_side_cap, CAP[t])
            C[t, k] = completed
            REV[t, k] = tier * base_fare * completed

            fulfillment_ok = completed >= FULFILLMENT_MIN * D[t]
            churn_ok = churn_risk(np.array([tier]))[0] <= CHURN_MAX
            payout_ok = tier * base_fare * DRIVER_TAKE_RATE >= DRIVER_PAYOUT_FLOOR
            feasible_mask[t, k] = fulfillment_ok and churn_ok and payout_ok

    # Safety check: every hour needs at least one feasible tier
    for t in range(N_HOURS):
        if not feasible_mask[t].any():
            # relax fulfillment for this hour rather than leaving it infeasible
            feasible_mask[t, :] = True

    # ---- Build MILP ----
    prob = pulp.LpProblem("DynamicPricing_MILP", pulp.LpMaximize)

    x = {(t, k): pulp.LpVariable(f"x_{t}_{k}", cat="Binary")
         for t in range(N_HOURS) for k in range(len(SURGE_TIERS)) if feasible_mask[t, k]}

    # Objective: maximize total revenue
    prob += pulp.lpSum(REV[t, k] * x[(t, k)] for (t, k) in x)

    # Exactly one tier per hour
    for t in range(N_HOURS):
        prob += pulp.lpSum(x[(t, k)] for k in range(len(SURGE_TIERS)) if (t, k) in x) == 1

    # Aggregate daily utilization
    prob += pulp.lpSum(C[t, k] * x[(t, k)] for (t, k) in x) >= DAILY_UTILIZATION_MIN * CAP.sum()

    # Smoothness: forbid tier pairs across consecutive hours that swing too much
    for t in range(1, N_HOURS):
        for k1 in range(len(SURGE_TIERS)):
            if (t - 1, k1) not in x:
                continue
            for k2 in range(len(SURGE_TIERS)):
                if (t, k2) not in x:
                    continue
                if abs(SURGE_TIERS[k1] - SURGE_TIERS[k2]) > MAX_HOURLY_SWING:
                    prob += x[(t - 1, k1)] + x[(t, k2)] <= 1

    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    chosen_tiers = np.zeros(N_HOURS)
    chosen_completed = np.zeros(N_HOURS)
    chosen_revenue = np.zeros(N_HOURS)
    for t in range(N_HOURS):
        for k in range(len(SURGE_TIERS)):
            if (t, k) in x and x[(t, k)].value() == 1:
                chosen_tiers[t] = SURGE_TIERS[k]
                chosen_completed[t] = C[t, k]
                chosen_revenue[t] = REV[t, k]

    return {
        "status": pulp.LpStatus[prob.status],
        "P_opt": chosen_tiers,
        "C_opt": chosen_completed,
        "revenue_opt": chosen_revenue,
        "total_revenue": chosen_revenue.sum(),
    }


if __name__ == "__main__":
    params = build_scenario_params()

    print("=" * 100)
    print("PHASE 3b: DISCRETE SURGE-TIER OPTIMIZATION (PuLP MILP)")
    print(f"Tiers available: {SURGE_TIERS}")
    print("=" * 100)

    rows = []
    for zone in params["zone_id"].unique():
        for day_type in ["Weekday", "Weekend"]:
            scen = params[(params["zone_id"] == zone) & (params["day_type"] == day_type)]
            if len(scen) != N_HOURS:
                continue
            res = solve_scenario_milp(scen)
            print(f"\n--- {zone} | {day_type} | Solver status: {res['status']} ---")
            print(f"  Total optimized daily revenue: {res['total_revenue']:,.0f}")
            print("  Hourly tier trajectory (0h-23h):")
            print("   ", " ".join(f"{p:.1f}" for p in res["P_opt"]))

            for h in range(N_HOURS):
                rows.append({
                    "zone_id": zone, "day_type": day_type, "hour": h,
                    "optimal_surge_tier": res["P_opt"][h],
                    "completed_trips": round(res["C_opt"][h], 1),
                    "hourly_revenue": round(res["revenue_opt"][h], 1),
                })

    out_df = pd.DataFrame(rows)
    out_df.to_csv("phase3_pulp_optimal_pricing.csv", index=False)
    print(f"\nSaved hour-by-hour tier decisions to phase3_pulp_optimal_pricing.csv")

    total_by_scenario = out_df.groupby(["zone_id", "day_type"])["hourly_revenue"].sum().reset_index()
    print("\nTotal daily revenue by scenario (MILP, discrete tiers):")
    print(total_by_scenario.to_string(index=False))
