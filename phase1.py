"""
Dynamic Pricing & Revenue Management — Synthetic Data Generator
================================================================
Phase 1 deliverable for: "Dynamic Pricing & Revenue Management Optimization
for On-Demand Delivery/Ride-Hailing Platforms"

This script simulates hour-by-hour, zone-level operational data for a
ride-hailing/delivery marketplace, with realistic, RECOVERABLE price
elasticity behavior baked in (so Phase 2's PED estimation has ground truth
to validate against).

Author: (your name) — OR / Decision Science Portfolio Project
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# ----------------------------------------------------------------------
# 1. CONFIGURATION
# ----------------------------------------------------------------------

@dataclass
class SimConfig:
    n_days: int = 90
    start_date: str = "2026-01-01"
    zones: tuple = ("Downtown_CBD", "Airport_Corridor", "Suburban_Residential")
    base_fare: float = 60.0          # currency units, e.g. INR/USD-equivalent
    random_seed: int = 42

    # Customer segments and their price elasticity of demand (PED).
    # PED is negative: % change in demand / % change in price.
    # |PED| < 1 => inelastic (business travelers, less price sensitive)
    # |PED| > 1 => elastic (price-sensitive leisure/budget segment)
    segments: dict = field(default_factory=lambda: {
        "business":       {"share": 0.25, "elasticity": -0.45, "base_conv": 0.82},
        "leisure":        {"share": 0.40, "elasticity": -1.10, "base_conv": 0.68},
        "price_sensitive":{"share": 0.35, "elasticity": -1.85, "base_conv": 0.55},
    })

    # Zone-level baseline demand (avg requests/hour at off-peak, multiplier=1.0)
    zone_base_demand: dict = field(default_factory=lambda: {
        "Downtown_CBD": 140,
        "Airport_Corridor": 90,
        "Suburban_Residential": 55,
    })

    # Zone-level baseline available driver supply (avg/hour)
    zone_base_supply: dict = field(default_factory=lambda: {
        "Downtown_CBD": 110,
        "Airport_Corridor": 70,
        "Suburban_Residential": 60,
    })

    surge_min: float = 0.8
    surge_max: float = 3.0
    driver_min_payout: float = 45.0   # currency floor per completed trip


CFG = SimConfig()
rng = np.random.default_rng(CFG.random_seed)


# ----------------------------------------------------------------------
# 2. TIME-OF-DAY / DAY-OF-WEEK DEMAND SHAPE
# ----------------------------------------------------------------------

def hourly_demand_multiplier(hour: int, is_weekend: bool) -> float:
    """Bimodal weekday commute peaks; smoother, later weekend curve."""
    if not is_weekend:
        morning_peak = 1.9 * np.exp(-((hour - 8.5) ** 2) / (2 * 1.6 ** 2))
        evening_peak = 2.3 * np.exp(-((hour - 18.5) ** 2) / (2 * 1.8 ** 2))
        base = 0.35
        return base + morning_peak + evening_peak
    else:
        midday_peak = 1.6 * np.exp(-((hour - 13.5) ** 2) / (2 * 3.0 ** 2))
        night_peak = 1.8 * np.exp(-((hour - 22.5) ** 2) / (2 * 2.2 ** 2))
        base = 0.45
        return base + midday_peak + night_peak


def hourly_supply_multiplier(hour: int, is_weekend: bool) -> float:
    """Driver supply is stickier than demand — shifts, not spikes."""
    if not is_weekend:
        return 0.6 + 0.5 * np.exp(-((hour - 9) ** 2) / (2 * 4.0 ** 2)) + \
               0.6 * np.exp(-((hour - 19) ** 2) / (2 * 4.0 ** 2))
    else:
        return 0.7 + 0.5 * np.exp(-((hour - 15) ** 2) / (2 * 5.0 ** 2))


# ----------------------------------------------------------------------
# 3. WEATHER / TRAFFIC SHOCK SIMULATION
# ----------------------------------------------------------------------

def simulate_weather_traffic(n_hours: int):
    """
    Weather: categorical daily state with hourly persistence (Markov-ish).
    Traffic index: 0 (free flow) to 1 (gridlock), correlated with hour + weather.
    """
    weather_states = ["Clear", "Rain", "Heavy_Rain", "Fog"]
    weather_probs_clear_day = [0.75, 0.15, 0.05, 0.05]

    weather = []
    current = "Clear"
    for h in range(n_hours):
        if h % 24 == 0:  # re-roll daily
            current = rng.choice(weather_states, p=weather_probs_clear_day)
        weather.append(current)
    return weather


def traffic_index(hour: int, weather: str, is_weekend: bool) -> float:
    base = hourly_demand_multiplier(hour, is_weekend) / 3.0  # correlated w/ demand
    weather_bump = {"Clear": 0.0, "Rain": 0.15, "Heavy_Rain": 0.30, "Fog": 0.20}[weather]
    noise = rng.normal(0, 0.03)
    return float(np.clip(base * 0.5 + weather_bump + noise, 0, 1))


# ----------------------------------------------------------------------
# 4. RULE-BASED SURGE (baseline pricing policy — to be beaten in Phase 3/4)
# ----------------------------------------------------------------------

def rule_based_surge(demand: float, supply: float) -> float:
    """Simple heuristic surge used by many real platforms today:
    surge scales with demand/supply gap ratio, clipped to bounds."""
    gap_ratio = (demand - supply) / max(supply, 1)
    raw_surge = 1.0 + 0.6 * max(gap_ratio, 0)
    return float(np.clip(raw_surge, CFG.surge_min, CFG.surge_max))


# ----------------------------------------------------------------------
# 5. ELASTICITY-DRIVEN CONVERSION MODEL
# ----------------------------------------------------------------------

def segment_conversion(base_conv: float, elasticity: float, surge: float,
                        weather_penalty: float) -> float:
    """
    Conversion rate falls as price rises above 1.0x, following a log-price
    elasticity curve:  conv = base_conv * (surge ** elasticity)
    This is the CES-style demand curve: log(Q) = log(A) + elasticity*log(P)
    -> recoverable via log-log OLS regression in Phase 2.
    """
    price_effect = surge ** elasticity          # elasticity is negative
    weather_effect = 1.0 + weather_penalty       # bad weather can RAISE willingness
    conv = base_conv * price_effect * weather_effect
    conv *= rng.normal(1.0, 0.03)                 # small stochastic noise
    return float(np.clip(conv, 0.02, 0.98))


# ----------------------------------------------------------------------
# 6. MAIN GENERATOR
# ----------------------------------------------------------------------

def generate_dataset(cfg: SimConfig = CFG) -> pd.DataFrame:
    n_hours = cfg.n_days * 24
    start = datetime.strptime(cfg.start_date, "%Y-%m-%d")
    timestamps = [start + timedelta(hours=h) for h in range(n_hours)]
    weather_seq = simulate_weather_traffic(n_hours)

    rows = []
    for zone in cfg.zones:
        base_d = cfg.zone_base_demand[zone]
        base_s = cfg.zone_base_supply[zone]

        for h in range(n_hours):
            ts = timestamps[h]
            hour, dow = ts.hour, ts.weekday()
            is_weekend = dow >= 5
            weather = weather_seq[h]
            traffic = traffic_index(hour, weather, is_weekend)

            # --- raw demand & supply before price response ---
            d_mult = hourly_demand_multiplier(hour, is_weekend)
            s_mult = hourly_supply_multiplier(hour, is_weekend)

            weather_demand_bump = {"Clear": 0.0, "Rain": 0.10,
                                    "Heavy_Rain": 0.05, "Fog": 0.08}[weather]
            weather_penalty_conv = {"Clear": 0.0, "Rain": -0.05,
                                     "Heavy_Rain": -0.15, "Fog": -0.08}[weather]

            raw_demand = base_d * d_mult * (1 + weather_demand_bump)
            raw_demand *= rng.normal(1.0, 0.08)          # Poisson-like noise
            raw_demand = max(raw_demand, 0)

            raw_supply = base_s * s_mult
            raw_supply *= rng.normal(1.0, 0.06)
            raw_supply = max(raw_supply, 1)

            # --- baseline rule-based surge decision (today's "as-is" policy) ---
            surge = rule_based_surge(raw_demand, raw_supply)
            price = round(cfg.base_fare * surge, 2)

            # --- segment-level demand response & conversion ---
            total_completed = 0.0
            total_requests = 0.0
            blended_conv_num, blended_conv_den = 0.0, 0.0

            for seg_name, seg_cfg in cfg.segments.items():
                seg_requests = raw_demand * seg_cfg["share"]
                conv = segment_conversion(seg_cfg["base_conv"], seg_cfg["elasticity"],
                                           surge, weather_penalty_conv)
                seg_completed = seg_requests * conv

                total_requests += seg_requests
                total_completed += seg_completed
                blended_conv_num += seg_completed
                blended_conv_den += seg_requests

            # supply-side cap: can't fulfill more trips than available drivers allow
            effective_capacity = raw_supply * 1.3   # each driver ~1.3 trips/hr capacity
            completed_trips = min(total_completed, effective_capacity)
            fulfillment_rate = completed_trips / max(total_requests, 1e-6)
            conversion_rate = blended_conv_num / max(blended_conv_den, 1e-6)

            revenue = round(completed_trips * price, 2)
            driver_payout = round(price * 0.75, 2)   # 75% driver take-rate assumption
            driver_payout_below_floor = driver_payout < cfg.driver_min_payout

            gap_ratio = (raw_demand - raw_supply) / max(raw_supply, 1)

            # crude churn proxy: prob a customer abandons due to high surge
            churn_risk = float(np.clip(0.02 + 0.05 * max(surge - 1.3, 0), 0, 0.5))

            rows.append({
                "timestamp": ts,
                "date": ts.date(),
                "hour": hour,
                "day_of_week": ts.strftime("%A"),
                "is_weekend": is_weekend,
                "zone_id": zone,
                "weather": weather,
                "traffic_index": round(traffic, 3),
                "base_fare": cfg.base_fare,
                "surge_multiplier": round(surge, 3),
                "price": price,
                "demand_requests": round(total_requests, 1),
                "available_drivers": round(raw_supply, 1),
                "completed_trips": round(completed_trips, 1),
                "conversion_rate": round(conversion_rate, 4),
                "fulfillment_rate": round(min(fulfillment_rate, 1.0), 4),
                "demand_supply_gap_ratio": round(gap_ratio, 3),
                "revenue": revenue,
                "driver_payout_per_trip": driver_payout,
                "payout_below_floor_flag": driver_payout_below_floor,
                "est_churn_risk": round(churn_risk, 4),
            })

    df = pd.DataFrame(rows)
    return df.sort_values(["zone_id", "timestamp"]).reset_index(drop=True)


# ----------------------------------------------------------------------
# 7. RUN
# ----------------------------------------------------------------------

if __name__ == "__main__":
    df = generate_dataset(CFG)

    out_path = "dynamic_pricing_synthetic_data.csv"
    df.to_csv(out_path, index=False)

    print(f"Generated {len(df):,} rows across {len(CFG.zones)} zones, "
          f"{CFG.n_days} days.")
    print(f"Saved to: {out_path}\n")
    print("Schema:")
    print(df.dtypes)
    print("\nSample rows:")
    print(df.head(5).to_string())
    print("\nQuick sanity check — mean conversion rate by surge bucket:")
    df["surge_bucket"] = pd.cut(df["surge_multiplier"],
                                 bins=[0.7, 1.0, 1.3, 1.6, 2.0, 3.1])
    print(df.groupby("surge_bucket", observed=True)["conversion_rate"].mean())
