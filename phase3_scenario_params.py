"""
Phase 3 — Shared Scenario Parameter Builder
============================================
Extracts per (zone, hour, day_type) demand/capacity/conversion parameters
from the Phase 1 synthetic dataset, and attaches the Phase 2 fixed-effects
elasticity estimates. Both the SciPy (continuous NLP) and PuLP (discrete
MILP) optimizers in Phase 3 consume this same parameter table, so results
are directly comparable.
"""

import pandas as pd
import numpy as np

PEAK_HOURS = {7, 8, 9, 17, 18, 19, 20}


def build_scenario_params(data_path="dynamic_pricing_synthetic_data.csv",
                           elasticity_path="phase2_elasticity_estimates.csv"):
    df = pd.read_csv(data_path, parse_dates=["timestamp"])
    elas = pd.read_csv(elasticity_path)

    df["day_type"] = np.where(df["is_weekend"], "Weekend", "Weekday")
    df["period"] = np.where(df["hour"].isin(PEAK_HOURS), "Peak (commute)", "Off-Peak")

    # --- Baseline demand & capacity: average by zone / hour / day_type ---
    base = (df.groupby(["zone_id", "hour", "day_type"])
              .agg(demand_base=("demand_requests", "mean"),
                   capacity=("available_drivers", lambda s: s.mean() * 1.3))
              .reset_index())

    # --- Baseline conversion (beta): avg conversion where surge ~ 1.0 ---
    near_base_price = df[df["surge_multiplier"] <= 1.05]
    beta = (near_base_price.groupby(["zone_id", "hour", "day_type"])
                           .agg(beta_conv=("conversion_rate", "mean"))
                           .reset_index())

    params = base.merge(beta, on=["zone_id", "hour", "day_type"], how="left")

    # Fallback: if an hour/day_type combo has no near-base-price observations,
    # use the zone-level average baseline conversion instead.
    zone_fallback = near_base_price.groupby("zone_id")["conversion_rate"].mean()
    params["beta_conv"] = params.apply(
        lambda r: r["beta_conv"] if pd.notna(r["beta_conv"]) else zone_fallback[r["zone_id"]],
        axis=1
    )

    # --- Attach elasticity (zone x period) from Phase 2 ---
    params["period"] = np.where(params["hour"].isin(PEAK_HOURS), "Peak (commute)", "Off-Peak")
    params = params.merge(elas[["zone_id", "period", "estimated_elasticity"]],
                           on=["zone_id", "period"], how="left")
    params = params.rename(columns={"estimated_elasticity": "elasticity"})

    base_fare_lookup = df.groupby("zone_id")["base_fare"].first()
    params["base_fare"] = params["zone_id"].map(base_fare_lookup)

    return params.sort_values(["zone_id", "day_type", "hour"]).reset_index(drop=True)


def churn_risk(surge, kink=1.3, slope=0.05, base=0.02, cap=0.5):
    """Same functional form used in the Phase 1 generator -- recovered/
    known here since it was deterministic; in a real system this would
    itself be estimated via regression on realized cancellation data."""
    return np.clip(base + slope * np.maximum(surge - kink, 0), 0, cap)


if __name__ == "__main__":
    p = build_scenario_params()
    print(f"Built parameter table: {len(p)} (zone x hour x day_type) rows")
    print(p.head(10).to_string(index=False))
    p.to_csv("phase3_scenario_params.csv", index=False)
