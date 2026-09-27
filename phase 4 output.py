Python 3.13.7 (tags/v3.13.7:bcee1c3, Aug 14 2025, 14:15:11) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.

========== RESTART: C:/Users/ritik/Downloads/project1/phase4 input.py ==========
==============================================================================================================
PHASE 4: AGGREGATE POLICY COMPARISON (across all 3 zones x 2 day-types, per-day totals)
==============================================================================================================
                  policy  total_daily_revenue  avg_surge  avg_fulfillment  avg_utilization  avg_churn_risk  total_completed_trips  pct_uplift_vs_static  pct_uplift_vs_rulebased
OR-Optimized (PuLP MILP)          645654.0252     1.1764           0.5869           0.5596          0.0244              8676.4589                  9.66                     0.40
OR-Optimized (SciPy NLP)          645666.1446     1.0580           0.6310           0.6221          0.0208              9798.8454                  9.66                     0.40
      Rule-Based (as-is)          643072.5457     1.2913           0.5445           0.4898          0.0276              7548.6138                  9.22                     0.00
                  Static          588765.5536     1.0000           0.6319           0.6230          0.0200              9812.7592                  0.00                    -8.44

==============================================================================================================
PER-SCENARIO BREAKDOWN
==============================================================================================================
policy                         OR-Optimized (PuLP MILP)  OR-Optimized (SciPy NLP)  Rule-Based (as-is)    Static
zone_id              day_type                                                                                  
Airport_Corridor     Weekday                    95733.0                   95640.0             95681.0   85591.0
                     Weekend                   109143.0                  109162.0            108660.0   96397.0
Downtown_CBD         Weekday                   148108.0                  148009.0            147975.0  132962.0
                     Weekend                   167579.0                  167664.0            166615.0  150516.0
Suburban_Residential Weekday                    58631.0                   58688.0             58268.0   58519.0
                     Weekend                    66460.0                   66504.0             65875.0   64780.0
