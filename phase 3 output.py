Python 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.

===== RESTART: C:\Users\ritik\Downloads\project1\phase3_scenario_params.py =====
Built parameter table: 144 (zone x hour x day_type) rows
         zone_id  hour day_type  demand_base   capacity  beta_conv         period  elasticity  base_fare
Airport_Corridor     0  Weekday    32.021875  58.487813   0.661914       Off-Peak      -1.020       60.0
Airport_Corridor     1  Weekday    32.325000  61.252344   0.665484       Off-Peak      -1.020       60.0
Airport_Corridor     2  Weekday    32.764063  64.971563   0.661023       Off-Peak      -1.020       60.0
Airport_Corridor     3  Weekday    32.653125  70.116719   0.659834       Off-Peak      -1.020       60.0
Airport_Corridor     4  Weekday    35.714062  75.974844   0.662595       Off-Peak      -1.020       60.0
Airport_Corridor     5  Weekday    47.234375  82.312344   0.661981       Off-Peak      -1.020       60.0
Airport_Corridor     6  Weekday    84.498437  89.050000   0.646883       Off-Peak      -1.020       60.0
Airport_Corridor     7  Weekday   143.643750  95.101094   0.660817 Peak (commute)      -0.994       60.0
Airport_Corridor     8  Weekday   196.368750 100.045156   0.660817 Peak (commute)      -0.994       60.0
Airport_Corridor     9  Weekday   198.692187 103.167187   0.660817 Peak (commute)      -0.994       60.0

==== RESTART: C:\Users\ritik\Downloads\project1\phase3_optimization_scipy.py ===
====================================================================================================
PHASE 3a: CONTINUOUS NLP OPTIMIZATION (SciPy SLSQP)
====================================================================================================

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

========================================= RESTART: C:\Users\ritik\Downloads\project1\phase3_optimization_pulp.py ========================================
====================================================================================================
PHASE 3b: DISCRETE SURGE-TIER OPTIMIZATION (PuLP MILP)
Tiers available: [1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0]
====================================================================================================

--- Airport_Corridor | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 95,733
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.8 1.5 1.0 1.0 1.0

--- Airport_Corridor | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 109,143
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.2 1.2 1.5 1.2 1.2 1.0 1.5 1.8 1.8 1.8 1.5 1.8 1.8

--- Downtown_CBD | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 148,108
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.8 1.5 1.0 1.0 1.0

--- Downtown_CBD | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 167,579
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.2 1.2 1.2 1.2 1.0 1.5 1.8 1.8 1.8 1.5 1.8 1.8

--- Suburban_Residential | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 58,631
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.2 1.0 1.0 1.0 1.0 1.0

--- Suburban_Residential | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 66,460
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.2 1.5

Saved hour-by-hour tier decisions to phase3_pulp_optimal_pricing.csv

Total daily revenue by scenario (MILP, discrete tiers):
             zone_id day_type  hourly_revenue
    Airport_Corridor  Weekday         95732.6
    Airport_Corridor  Weekend        109143.1
        Downtown_CBD  Weekday        148108.2
        Downtown_CBD  Weekend        167579.2
Suburban_Residential  Weekday         58631.1
Suburban_Residential  Weekend         66459.8

========================================= RESTART: C:\Users\ritik\Downloads\project1\phase3_optimization_pulp.py ========================================
====================================================================================================
PHASE 3b: DISCRETE SURGE-TIER OPTIMIZATION (PuLP MILP)
Tiers available: [1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0]
====================================================================================================

--- Airport_Corridor | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 95,733
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.8 1.5 1.0 1.0 1.0

--- Airport_Corridor | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 109,143
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.2 1.2 1.5 1.2 1.2 1.0 1.5 1.8 1.8 1.8 1.5 1.8 1.8

--- Downtown_CBD | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 148,108
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.8 1.5 1.0 1.0 1.0

--- Downtown_CBD | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 167,579
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.5 1.8 1.5 1.0 1.0 1.2 1.2 1.2 1.2 1.0 1.5 1.8 1.8 1.8 1.5 1.8 1.8

--- Suburban_Residential | Weekday | Solver status: Optimal ---
  Total optimized daily revenue: 58,631
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.2 1.0 1.0 1.0 1.0 1.0

--- Suburban_Residential | Weekend | Solver status: Optimal ---
  Total optimized daily revenue: 66,460
  Hourly tier trajectory (0h-23h):
    1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.0 1.2 1.5

Saved hour-by-hour tier decisions to phase3_pulp_optimal_pricing.csv

Total daily revenue by scenario (MILP, discrete tiers):
             zone_id day_type  hourly_revenue
    Airport_Corridor  Weekday         95732.6
    Airport_Corridor  Weekend        109143.1
        Downtown_CBD  Weekday        148108.2
        Downtown_CBD  Weekend        167579.2
Suburban_Residential  Weekday         58631.1
Suburban_Residential  Weekend         66459.8

======================================== RESTART: C:\Users\ritik\Downloads\project1\phase3_optimization_scipy.py ========================================
====================================================================================================
PHASE 3a: CONTINUOUS NLP OPTIMIZATION (SciPy SLSQP)
====================================================================================================

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

--- Airport_Corridor | Weekday | FEASIBLE, NEAR-OPTIMAL (solver hit eval cap in flat region) ---
  Total optimized daily revenue: 95,637
  Optimal surge range: 1.00x - 1.41x
  Avg surge: 1.07x
  Hourly surge trajectory (0h-23h):
    1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.30 1.28 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.10 1.41 1.40 1.09 1.00 1.00 1.00

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

--- Airport_Corridor | Weekend | FEASIBLE, NEAR-OPTIMAL (solver hit eval cap in flat region) ---
  Total optimized daily revenue: 109,160
  Optimal surge range: 1.00x - 1.75x
  Avg surge: 1.11x
  Hourly surge trajectory (0h-23h):
    1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.01 1.01 1.01 1.00 1.02 1.11 1.22 1.13 1.06 1.00 1.00 1.01 1.01 1.05 1.45 1.71 1.75

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

--- Downtown_CBD | Weekday | FEASIBLE, NEAR-OPTIMAL (solver hit eval cap in flat region) ---
  Total optimized daily revenue: 148,007
  Optimal surge range: 1.00x - 1.40x
  Avg surge: 1.06x
  Hourly surge trajectory (0h-23h):
    1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.29 1.25 1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.10 1.40 1.37 1.10 1.00 1.00 1.00

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

--- Downtown_CBD | Weekend | FEASIBLE, NEAR-OPTIMAL (solver hit eval cap in flat region) ---
  Total optimized daily revenue: 167,661
  Optimal surge range: 1.00x - 1.70x
  Avg surge: 1.09x
  Hourly surge trajectory (0h-23h):
    1.00 1.00 1.00 1.00 1.00 1.00 1.00 1.01 1.01 1.00 1.00 1.00 1.10 1.15 1.12 1.02 1.00 1.00 1.00 1.00 1.05 1.34 1.66 1.70

Warning (from warnings module):
  File "C:\Users\ritik\AppData\Local\Programs\Python\Python313\Lib\site-packages\scipy\optimize\_differentiable_functions.py", line 737
    self.H.update(delta_x, delta_g)
UserWarning: delta_grad == 0.0. Check if the approximated function is linear. If the function is linear better results can be obtained by defining the Hessian as zero instead of using quasi-Newton approximations.

================================================== RESTART: C:/Users/ritik/Downloads/warning stopper.py =================================================
