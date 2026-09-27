"""
Phase 4 -- Comparative Evaluation & Business Impact
=====================================================
Evaluates THREE pricing policies through the SAME demand-response model
(built in Phase 3) so the comparison is apples-to-apples:

  1. Static pricing       -- P = 1.0x always (no dynamic pricing at all)
  2. Rule-based surge     -- the "as-is" heuristic from Phase 1's generator
                             (surge scales linearly with demand-supply gap)
  3. OR-optimized (SciPy) -- Phase 3a's continuous NLP solution
  4. OR-optimized (PuLP)  -- Phase 3b's discrete-tier MILP solution

For every policy, completed_trips(P) = min(D*BETA*P^EPS, CAP) and
revenue(P) = P * base_fare * completed_trips(P) -- the identical formula
used to fit and validate the optimizers in Phase 3. This isolates the
effect of the PRICING POLICY itself, holding the underlying demand model
fixed across all four.
"""

import numpy as np
import pandas as pd
from phase3_scenario_params import build_scenario_params, churn_risk

DRIVER_TAKE_RATE = 0.75
N_HOURS = 24


def rule_based_surge(demand, supply):
    """Exact replica of the Phase 1 generator's heuristic policy."""
    gap_ratio = (demand - supply) / np.maximum(supply, 1)
    raw_surge = 1.0 + 0.6 * np.maximum(gap_ratio, 0)
    return np.clip(raw_surge, 0.8, 3.0)


def evaluate_policy(P, D, CAP, BETA, EPS, base_fare):
    """Given a price-multiplier vector, return all downstream metrics."""
    demand_side = D * BETA * np.power(P, EPS)
    completed = np.minimum(demand_side, CAP)
    revenue = P * base_fare * completed
    fulfillment = completed / np.maximum(D, 1e-6)
    utilization = completed / np.maximum(CAP, 1e-6)
    churn = churn_risk(P)
    payout = P * base_fare * DRIVER_TAKE_RATE
    return {
        "revenue": revenue, "completed": completed, "fulfillment": fulfillment,
        "utilization": utilization, "churn": churn, "payout": payout, "surge": P,
    }


def main():
    params = build_scenario_params()
    scipy_opt = pd.read_csv("phase3_scipy_optimal_pricing.csv")
    pulp_opt = pd.read_csv("phase3_pulp_optimal_pricing.csv")

    scenario_rows = []
    hourly_detail_rows = []

    for zone in params["zone_id"].unique():
        for day_type in ["Weekday", "Weekend"]:
            scen = params[(params["zone_id"] == zone) &
                          (params["day_type"] == day_type)].sort_values("hour").reset_index(drop=True)
            if len(scen) != N_HOURS:
                continue

            D = scen["demand_base"].values
            CAP = scen["capacity"].values
            BETA = scen["beta_conv"].values
            EPS = scen["elasticity"].values
            base_fare = scen["base_fare"].iloc[0]
            SUPPLY = CAP / 1.3   # recover raw driver supply from capacity

            # --- Policy 1: Static ---
            P_static = np.ones(N_HOURS)

            # --- Policy 2: Rule-based (as-is) ---
            P_rule = rule_based_surge(D, SUPPLY)

            # --- Policy 3: SciPy NLP ---
            scipy_scen = scipy_opt[(scipy_opt["zone_id"] == zone) &
                                   (scipy_opt["day_type"] == day_type)].sort_values("hour")
            P_scipy = scipy_scen["optimal_surge"].values

            # --- Policy 4: PuLP MILP ---
            pulp_scen = pulp_opt[(pulp_opt["zone_id"] == zone) &
                                 (pulp_opt["day_type"] == day_type)].sort_values("hour")
            P_pulp = pulp_scen["optimal_surge_tier"].values

            policies = {
                "Static": P_static,
                "Rule-Based (as-is)": P_rule,
                "OR-Optimized (SciPy NLP)": P_scipy,
                "OR-Optimized (PuLP MILP)": P_pulp,
            }

            for policy_name, P in policies.items():
                m = evaluate_policy(P, D, CAP, BETA, EPS, base_fare)
                scenario_rows.append({
                    "zone_id": zone, "day_type": day_type, "policy": policy_name,
                    "total_revenue": m["revenue"].sum(),
                    "avg_surge": m["surge"].mean(),
                    "avg_fulfillment": m["fulfillment"].mean(),
                    "avg_utilization": m["utilization"].mean(),
                    "avg_churn_risk": m["churn"].mean(),
                    "total_completed_trips": m["completed"].sum(),
                })
                for h in range(N_HOURS):
                    hourly_detail_rows.append({
                        "zone_id": zone, "day_type": day_type, "policy": policy_name,
                        "hour": h, "surge": m["surge"][h], "revenue": m["revenue"][h],
                        "completed_trips": m["completed"][h],
                    })

    scenario_df = pd.DataFrame(scenario_rows)
    hourly_df = pd.DataFrame(hourly_detail_rows)

    scenario_df.to_csv("phase4_scenario_comparison.csv", index=False)
    hourly_df.to_csv("phase4_hourly_comparison.csv", index=False)

    # ------------------------------------------------------------------
    # Aggregate KPIs across all 6 scenarios (equal-weighted daily totals)
    # ------------------------------------------------------------------
    agg = scenario_df.groupby("policy").agg(
        total_daily_revenue=("total_revenue", "sum"),
        avg_surge=("avg_surge", "mean"),
        avg_fulfillment=("avg_fulfillment", "mean"),
        avg_utilization=("avg_utilization", "mean"),
        avg_churn_risk=("avg_churn_risk", "mean"),
        total_completed_trips=("total_completed_trips", "sum"),
    ).reset_index()

    static_rev = agg.loc[agg["policy"] == "Static", "total_daily_revenue"].iloc[0]
    rule_rev = agg.loc[agg["policy"] == "Rule-Based (as-is)", "total_daily_revenue"].iloc[0]
    agg["pct_uplift_vs_static"] = round(100 * (agg["total_daily_revenue"] - static_rev) / static_rev, 2)
    agg["pct_uplift_vs_rulebased"] = round(100 * (agg["total_daily_revenue"] - rule_rev) / rule_rev, 2)

    print("=" * 110)
    print("PHASE 4: AGGREGATE POLICY COMPARISON (across all 3 zones x 2 day-types, per-day totals)")
    print("=" * 110)
    print(agg.round(4).to_string(index=False))

    agg.to_csv("phase4_aggregate_comparison.csv", index=False)

    print("\n" + "=" * 110)
    print("PER-SCENARIO BREAKDOWN")
    print("=" * 110)
    pivot_rev = scenario_df.pivot_table(index=["zone_id", "day_type"], columns="policy",
                                         values="total_revenue").round(0)
    print(pivot_rev.to_string())

    return scenario_df, hourly_df, agg


if __name__ == "__main__":
    main()
