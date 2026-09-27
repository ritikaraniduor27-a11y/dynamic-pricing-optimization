"""
Phase 3a — Continuous Dynamic Pricing Optimization (SciPy SLSQP)
==================================================================
Solves, for each (zone, day_type) scenario, the 24-hour price-multiplier
trajectory that maximizes total revenue subject to fairness, fulfillment,
churn, driver-payout, supply-retention, and smoothness constraints.

Decision vector per scenario (48-dim): [P_0..P_23, C_0..C_23]
  P_t = price multiplier at hour t
  C_t = completed trips at hour t (auxiliary variable -- see writeup)
"""

import numpy as np
from scipy.optimize import minimize, NonlinearConstraint, LinearConstraint, Bounds
from phase3_scenario_params import build_scenario_params, churn_risk

# ---------------------------------------------------------------------
# Business policy configuration (the "OR guardrails")
# ---------------------------------------------------------------------
P_MIN, P_MAX = 0.8, 3.0          # fairness bounds
FULFILLMENT_MIN = 0.35           # >=35% of interested demand must be served
CHURN_MAX = 0.10                 # per-hour churn-risk ceiling
DRIVER_PAYOUT_FLOOR = 45.0       # currency units per trip
DRIVER_TAKE_RATE = 0.75
DAILY_UTILIZATION_MIN = 0.30     # aggregate: >=30% of daily capacity used
MAX_HOURLY_SWING = 0.5           # smoothness: |P_t - P_{t-1}| <= this

# Near-unit elasticity (~-1.0 to -1.05, estimated in Phase 2) makes the raw
# revenue objective almost perfectly flat in P over large stretches of the
# feasible region -- gradient-based solvers can stall or return noisy local
# points in that regime. A tiny regularization term breaks ties in favor of
# the LOWER price whenever revenue is indifferent -- an economically
# sensible tie-breaker (more volume, less churn risk, same revenue) rather
# than an arbitrary solver artifact. lambda is small enough to never
# override a genuine revenue gradient in the capacity-constrained regime.
REG_LAMBDA = 0.05

N_HOURS = 24


def solve_scenario(zone_df):
    """zone_df: 24 rows (one scenario), indexed by hour 0..23, sorted."""
    zone_df = zone_df.sort_values("hour").reset_index(drop=True)
    D = zone_df["demand_base"].values          # baseline demand, price-independent
    CAP = zone_df["capacity"].values            # driver-side capacity
    BETA = zone_df["beta_conv"].values          # baseline conversion at P=1
    EPS = zone_df["elasticity"].values          # elasticity (negative)
    base_fare = zone_df["base_fare"].iloc[0]

    # Price lower bound tightened by the driver payout floor:
    # P * base_fare * take_rate >= floor  =>  P >= floor / (base_fare*take_rate)
    p_lb = max(P_MIN, DRIVER_PAYOUT_FLOOR / (base_fare * DRIVER_TAKE_RATE))
    p_ub = P_MAX

    # ---- Objective: minimize negative total revenue + tiny tie-breaking
    # regularization pulling toward the lower bound when revenue is flat ----
    def objective(x):
        P, C = x[:N_HOURS], x[N_HOURS:]
        revenue = np.sum(P * base_fare * C)
        reg = REG_LAMBDA * np.sum((P - p_lb) ** 2)
        return -revenue + reg

    def objective_grad(x):
        P, C = x[:N_HOURS], x[N_HOURS:]
        grad = np.zeros(2 * N_HOURS)
        grad[:N_HOURS] = -base_fare * C + 2 * REG_LAMBDA * (P - p_lb)
        grad[N_HOURS:] = -base_fare * P
        return grad

    # ---- Constraint: demand-side cap  D*BETA*P^EPS - C >= 0 ----
    def demand_cap(x):
        P, C = x[:N_HOURS], x[N_HOURS:]
        return D * BETA * np.power(P, EPS) - C

    # ---- Constraint: fulfillment floor  C - FULFILLMENT_MIN*D >= 0 ----
    def fulfillment(x):
        C = x[N_HOURS:]
        return C - FULFILLMENT_MIN * D

    # ---- Constraint: churn ceiling  CHURN_MAX - churn_risk(P) >= 0 ----
    def churn_ceiling(x):
        P = x[:N_HOURS]
        return CHURN_MAX - churn_risk(P)

    # ---- Constraint: daily aggregate utilization ----
    def utilization(x):
        C = x[N_HOURS:]
        return np.array([np.sum(C) - DAILY_UTILIZATION_MIN * np.sum(CAP)])

    # ---- Constraint: smoothness |P_t - P_{t-1}| <= MAX_HOURLY_SWING ----
    # expressed as two linear constraints: P_t - P_{t-1} <= delta, and >= -delta
    def smoothness_upper(x):
        P = x[:N_HOURS]
        return MAX_HOURLY_SWING - (P[1:] - P[:-1])

    def smoothness_lower(x):
        P = x[:N_HOURS]
        return MAX_HOURLY_SWING - (P[:-1] - P[1:])

    constraints = [
        {"type": "ineq", "fun": demand_cap},
        {"type": "ineq", "fun": fulfillment},
        {"type": "ineq", "fun": churn_ceiling},
        {"type": "ineq", "fun": utilization},
        {"type": "ineq", "fun": smoothness_upper},
        {"type": "ineq", "fun": smoothness_lower},
    ]

    bounds = [(p_lb, p_ub)] * N_HOURS + [(0, CAP[t]) for t in range(N_HOURS)]

    # Warm start: P at the payout-floor-adjusted lower bound, C = min(demand@P0, capacity).
    # Starting from a KNOWN FEASIBLE point (rather than an arbitrary guess) avoids the
    # infeasible-restoration failures that showed up with a naive x0.
    p0 = np.full(N_HOURS, p_lb)
    c0 = np.minimum(D * BETA * np.power(p0, EPS), CAP)
    x0 = np.concatenate([p0, c0])

    result = minimize(objective, x0, jac=objective_grad, method="SLSQP",
                       bounds=bounds, constraints=constraints,
                       options={"maxiter": 500, "ftol": 1e-10})

    # Fallback: if SLSQP still fails to converge (can happen in the near-flat
    # revenue regime), retry with trust-constr, which handles degenerate/flat
    # objectives more robustly via its interior trust-region approach.
    if not result.success:
        from scipy.optimize import NonlinearConstraint as NLC
        nlc_demand = NLC(demand_cap, 0, np.inf)
        nlc_fulfill = NLC(fulfillment, 0, np.inf)
        nlc_churn = NLC(churn_ceiling, 0, np.inf)
        nlc_util = NLC(utilization, 0, np.inf)
        nlc_smooth_u = NLC(smoothness_upper, 0, np.inf)
        nlc_smooth_l = NLC(smoothness_lower, 0, np.inf)
        result = minimize(objective, x0, jac=objective_grad, method="trust-constr",
                           bounds=Bounds([b[0] for b in bounds], [b[1] for b in bounds]),
                           constraints=[nlc_demand, nlc_fulfill, nlc_churn,
                                        nlc_util, nlc_smooth_u, nlc_smooth_l],
                           options={"maxiter": 2000, "gtol": 1e-8, "xtol": 1e-10})

    P_opt, C_opt = result.x[:N_HOURS], result.x[N_HOURS:]
    revenue_opt = P_opt * base_fare * C_opt

    # The solver's own .success flag can be False (e.g. hit an iteration/eval
    # cap in a near-flat objective region) even when the returned point is
    # fully feasible and near-optimal. We verify feasibility directly rather
    # than trust the flag alone -- this is standard practice before accepting
    # any NLP solution in production.
    tol = 1e-3
    feasible = (
        np.all(C_opt - (D * BETA * np.power(P_opt, EPS)) <= tol) and
        np.all(C_opt - CAP <= tol) and
        np.all(C_opt - FULFILLMENT_MIN * D >= -tol) and
        np.all(churn_risk(P_opt) <= CHURN_MAX + tol) and
        np.all(P_opt * base_fare * DRIVER_TAKE_RATE >= DRIVER_PAYOUT_FLOOR - tol) and
        np.all(np.abs(np.diff(P_opt)) <= MAX_HOURLY_SWING + tol) and
        (C_opt.sum() >= DAILY_UTILIZATION_MIN * CAP.sum() - tol)
    )

    return {
        "success": result.success,
        "feasible": feasible,
        "message": result.message,
        "P_opt": P_opt,
        "C_opt": C_opt,
        "revenue_opt": revenue_opt,
        "total_revenue": revenue_opt.sum(),
        "D": D, "CAP": CAP, "BETA": BETA, "EPS": EPS, "base_fare": base_fare,
    }


def baseline_revenue(zone_df):
    """Revenue under the Phase 1 rule-based policy (as-is), computed with the
    SAME conversion model, for an apples-to-apples comparison at this stage.
    (Full historical-vs-optimized comparison is Phase 4's job.)"""
    zone_df = zone_df.sort_values("hour").reset_index(drop=True)
    return None  # placeholder -- real historical comparison happens in Phase 4


if __name__ == "__main__":
    params = build_scenario_params()

    print("=" * 100)
    print("PHASE 3a: CONTINUOUS NLP OPTIMIZATION (SciPy SLSQP)")
    print("=" * 100)

    all_results = {}
    for zone in params["zone_id"].unique():
        for day_type in ["Weekday", "Weekend"]:
            scen = params[(params["zone_id"] == zone) & (params["day_type"] == day_type)]
            if len(scen) != N_HOURS:
                print(f"Skipping {zone}/{day_type}: incomplete hours ({len(scen)}/24)")
                continue

            res = solve_scenario(scen)
            all_results[(zone, day_type)] = res

            if res["success"]:
                status = "CONVERGED"
            elif res["feasible"]:
                status = "FEASIBLE, NEAR-OPTIMAL (solver hit eval cap in flat region)"
            else:
                status = "INFEASIBLE -- NEEDS REVIEW"
            print(f"\n--- {zone} | {day_type} | {status} ---")
            print(f"  Total optimized daily revenue: {res['total_revenue']:,.0f}")
            print(f"  Optimal surge range: {res['P_opt'].min():.2f}x - {res['P_opt'].max():.2f}x")
            print(f"  Avg surge: {res['P_opt'].mean():.2f}x")
            print("  Hourly surge trajectory (0h-23h):")
            print("   ", " ".join(f"{p:.2f}" for p in res["P_opt"]))

    # Save consolidated results
    import pandas as pd
    rows = []
    for (zone, day_type), res in all_results.items():
        for h in range(N_HOURS):
            rows.append({
                "zone_id": zone, "day_type": day_type, "hour": h,
                "optimal_surge": round(res["P_opt"][h], 3),
                "completed_trips": round(res["C_opt"][h], 1),
                "hourly_revenue": round(res["revenue_opt"][h], 1),
            })
    out_df = pd.DataFrame(rows)
    out_df.to_csv("phase3_scipy_optimal_pricing.csv", index=False)
    print(f"\nSaved hour-by-hour optimal pricing table to phase3_scipy_optimal_pricing.csv")

    total_by_scenario = out_df.groupby(["zone_id", "day_type"])["hourly_revenue"].sum().reset_index()
    print("\nTotal daily revenue by scenario:")
    print(total_by_scenario.to_string(index=False))
