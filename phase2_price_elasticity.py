"""
Phase 2 — Price Elasticity of Demand (PED) Estimation
======================================================
Estimates PED from the observational (non-experimental) synthetic dataset
using log-log regression, and explicitly demonstrates the endogeneity bias
that arises because price (surge) was set as a function of demand in
Phase 1's data-generating process.

Model recall (from generator): conversion_rate ≈ base_conv * surge^elasticity
=> log(conversion_rate) = log(base_conv) + elasticity * log(surge) + controls

This is the textbook log-log demand specification, where the coefficient on
log(price) IS the price elasticity of demand.
"""

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm

pd.set_option("display.width", 140)

df = pd.read_csv("dynamic_pricing_synthetic_data.csv", parse_dates=["timestamp"])

df["log_conv"] = np.log(df["conversion_rate"])
df["log_surge"] = np.log(df["surge_multiplier"])

# Behavioral proxy for customer segment mix: commute peaks skew business
# travelers (inelastic); off-peak skews leisure/price-sensitive (elastic).
peak_hours = {7, 8, 9, 17, 18, 19, 20}
df["period"] = np.where(df["hour"].isin(peak_hours), "Peak (commute)", "Off-Peak")


def report(model, label):
    coef = model.params.get("log_surge", np.nan)
    se = model.bse.get("log_surge", np.nan)
    ci_low, ci_high = model.conf_int().loc["log_surge"] if "log_surge" in model.params else (np.nan, np.nan)
    print(f"{label:55s} | elasticity = {coef:+.3f}  (SE={se:.3f}, 95% CI [{ci_low:.3f}, {ci_high:.3f}])  R²={model.rsquared:.3f}")


print("=" * 100)
print("1. NAIVE POOLED LOG-LOG REGRESSION (no controls -- endogeneity bias expected)")
print("=" * 100)
naive_model = smf.ols("log_conv ~ log_surge", data=df).fit(cov_type="HC1")
report(naive_model, "Naive (pooled, no controls)")
print()
print("Interpretation: this estimate is contaminated because surge was set BY the")
print("demand level (rule_based_surge()). Zones/hours with structurally higher demand")
print("also have both higher surge AND different baseline conversion -- omitted variable")
print("bias. This is why production teams NEVER estimate elasticity off raw price-demand")
print("correlation without controls or a genuine price experiment (A/B test).\n")


print("=" * 100)
print("2. FIXED-EFFECTS REGRESSION (zone + hour + weekday + weather controls)")
print("=" * 100)
fe_model = smf.ols(
    "log_conv ~ log_surge + C(zone_id) + C(hour) + C(is_weekend) + C(weather)",
    data=df
).fit(cov_type="HC1")
report(fe_model, "Fixed-effects (zone/hour/weekday/weather)")
print()
print("Interpretation: absorbing zone-level and time-of-day demand shocks isolates the")
print("within-zone-hour price response, giving a materially cleaner (more negative)")
print("elasticity estimate. This is the number to hand to the optimizer in Phase 3.\n")


print("=" * 100)
print("3. FIXED-EFFECTS ELASTICITY BY ZONE")
print("=" * 100)
for zone in df["zone_id"].unique():
    sub = df[df["zone_id"] == zone]
    m = smf.ols(
        "log_conv ~ log_surge + C(hour) + C(is_weekend) + C(weather)", data=sub
    ).fit(cov_type="HC1")
    report(m, zone)
print()


print("=" * 100)
print("4. FIXED-EFFECTS ELASTICITY BY TIME PERIOD (peak vs off-peak proxy for segment mix)")
print("=" * 100)
for period in df["period"].unique():
    sub = df[df["period"] == period]
    m = smf.ols(
        "log_conv ~ log_surge + C(zone_id) + C(is_weekend) + C(weather)", data=sub
    ).fit(cov_type="HC1")
    report(m, period)
print()
print("Interpretation: peak-hour (commute, business-skewed) elasticity should sit closer")
print("to the inelastic end; off-peak (leisure/price-sensitive-skewed) elasticity should")
print("be materially more negative. This directional check validates the generator AND")
print("mirrors real platforms' finding that business/commute demand is price-inelastic.\n")


print("=" * 100)
print("5. SUMMARY TABLE FOR DOWNSTREAM OPTIMIZATION (Phase 3 input)")
print("=" * 100)
summary_rows = []
for zone in df["zone_id"].unique():
    for period in df["period"].unique():
        sub = df[(df["zone_id"] == zone) & (df["period"] == period)]
        m = smf.ols(
            "log_conv ~ log_surge + C(is_weekend) + C(weather)", data=sub
        ).fit(cov_type="HC1")
        summary_rows.append({
            "zone_id": zone,
            "period": period,
            "estimated_elasticity": round(m.params["log_surge"], 3),
            "std_error": round(m.bse["log_surge"], 3),
            "n_obs": int(m.nobs),
        })

elasticity_table = pd.DataFrame(summary_rows)
print(elasticity_table.to_string(index=False))
elasticity_table.to_csv("phase2_elasticity_estimates.csv", index=False)
print("\nSaved zone x period elasticity table to phase2_elasticity_estimates.csv")
print("(this feeds directly into Phase 3's optimization model as the demand-response function)")
