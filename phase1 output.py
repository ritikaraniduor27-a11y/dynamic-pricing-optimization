Python 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
>>> 
====================================================== RESTART: C:/Users/ritik/Downloads/phase1.py ======================================================
Generated 6,480 rows across 3 zones, 90 days.
Saved to: dynamic_pricing_synthetic_data.csv

Schema:
timestamp                  datetime64[us]
date                               object
hour                                int64
day_of_week                           str
is_weekend                           bool
zone_id                               str
weather                               str
traffic_index                     float64
base_fare                         float64
surge_multiplier                  float64
price                             float64
demand_requests                   float64
available_drivers                 float64
completed_trips                   float64
conversion_rate                   float64
fulfillment_rate                  float64
demand_supply_gap_ratio           float64
revenue                           float64
driver_payout_per_trip            float64
payout_below_floor_flag              bool
est_churn_risk                    float64
dtype: object

Sample rows:
            timestamp        date  hour day_of_week  is_weekend           zone_id weather  traffic_index  base_fare  surge_multiplier  price  demand_requests  available_drivers  completed_trips  conversion_rate  fulfillment_rate  demand_supply_gap_ratio  revenue  driver_payout_per_trip  payout_below_floor_flag  est_churn_risk
0 2026-01-01 00:00:00  2026-01-01     0    Thursday       False  Airport_Corridor    Rain          0.205       60.0               1.0   60.0             36.8               40.3             23.0           0.6262            0.6262                   -0.087  1382.56                    45.0                    False            0.02
1 2026-01-01 01:00:00  2026-01-01     1    Thursday       False  Airport_Corridor    Rain          0.191       60.0               1.0   60.0             32.9               47.4             21.0           0.6376            0.6376                   -0.306  1258.12                    45.0                    False            0.02
2 2026-01-01 02:00:00  2026-01-01     2    Thursday       False  Airport_Corridor    Rain          0.182       60.0               1.0   60.0             36.6               49.0             22.9           0.6257            0.6257                   -0.253  1373.73                    45.0                    False            0.02
3 2026-01-01 03:00:00  2026-01-01     3    Thursday       False  Airport_Corridor    Rain          0.265       60.0               1.0   60.0             35.0               49.7             22.4           0.6393            0.6393                   -0.296  1341.86                    45.0                    False            0.02
4 2026-01-01 04:00:00  2026-01-01     4    Thursday       False  Airport_Corridor    Rain          0.196       60.0               1.0   60.0             42.2               56.0             26.8           0.6345            0.6345                   -0.247  1605.40                    45.0                    False            0.02

Quick sanity check — mean conversion rate by surge bucket:
surge_bucket
(0.7, 1.0]    0.660830
(1.0, 1.3]    0.567319
(1.3, 1.6]    0.445854
(1.6, 2.0]    0.364690
(2.0, 3.1]    0.295924
Name: conversion_rate, dtype: float64
