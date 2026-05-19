import sys
sys.path.insert(0, '.')
import numpy as np
import pandas as pd
import json

print("=== D11: AnomalyDetector ===")
from src.stage5_analysis.anomaly_detector import AnomalyDetector
ad = AnomalyDetector()

labs = pd.DataFrame({
    'hadm_id':         [100, 100, 100],
    'label':           ['Creatinine', 'Lactate', 'WBC'],
    'valuenum':        [3.2, 4.1, 18.0],
    'valueuom':        ['mg/dL', 'mmol/L', 'K/uL'],
    'is_abnormal':     [True, True, True],
    'severity_score':  [0.85, 0.72, 0.61],
    'ref_range_upper': [1.2, 2.2, 11.0],
})
lab_anom = ad.detect_lab_anomalies(labs, hadm_id=100)
print(f"Lab anomalies found: {len(lab_anom)}")
for a in lab_anom:
    print(f"  {a['name']:15s}  value={a['value']}  severity={a['severity']}  direction={a['direction']}")

vitals = pd.DataFrame({
    'stay_id':    [1, 1, 1, 1, 1],
    'vital_name': ['heart_rate', 'heart_rate', 'spo2', 'spo2', 'respiratory_rate'],
    'valuenum':   [130, 135, 88, 87, 25],
    'charttime':  pd.to_datetime([
        '2024-01-01 00:00', '2024-01-01 02:00',
        '2024-01-01 00:00', '2024-01-01 02:00',
        '2024-01-01 00:00',
    ]),
})
vital_anom = ad.detect_vital_anomalies(vitals, stay_id=1)
print(f"Vital anomalies found: {len(vital_anom)}")
for v in vital_anom:
    print(f"  {v['vital_name']:20s}  value={v['current_value']}  status={v['status']}  trend={v['trend']}")

score = ad.compute_aggregate_risk_score(lab_anom, vital_anom, mortality_prob=0.4)
print(f"Aggregate risk score: {score:.3f}")

print()
print("=== D12: TrendAnalyzer ===")
from src.stage5_analysis.trend_analyzer import TrendAnalyzer
ta = TrendAnalyzer()

times  = np.array([0, 2, 4, 6, 8, 10, 12], dtype=float)
hr     = np.array([80, 82, 88, 95, 105, 115, 120], dtype=float)
spo2   = np.array([98, 97, 95, 92, 89, 86, 83], dtype=float)
stable = np.array([72, 73, 71, 72, 74, 72, 73], dtype=float)

for name, vals in [('Heart Rate (RISING)', hr), ('SpO2 (FALLING)', spo2), ('BP (STABLE)', stable)]:
    slope = ta.compute_trend_slope(vals, times)
    trend = ta.classify_trend(slope)
    stats = ta.compute_trend_stats(vals, times)
    print(f"  {name:25s}  slope={slope:6.2f}  trend={trend:8s}  pct_change={stats['pct_change']:.1f}%")

vitals_df = pd.DataFrame({
    'stay_id':                  [1]*7 + [1]*7,
    'vital_name':               ['heart_rate']*7 + ['spo2']*7,
    'valuenum':                 list(hr) + list(spo2),
    'hours_from_icu_admission': list(times) + list(times),
})
deteriorating = ta.detect_deterioration(vitals_df, stay_id=1, deterioration_threshold=0.3)
print(f"  Deterioration detected: {deteriorating}")

print()
print("=== D13: SummaryGenerator ===")
from src.stage5_analysis.summary_generator import SummaryGenerator
sg = SummaryGenerator()

note = """Discharge Diagnoses:
1. Sepsis
2. Acute kidney injury
3. Respiratory failure

Patient was admitted to the ICU with fever and hypotension.
"""

labs_df = pd.DataFrame({
    'label':           ['Creatinine', 'Lactate', 'WBC'],
    'valuenum':        [3.2, 4.1, 18.0],
    'valueuom':        ['mg/dL', 'mmol/L', 'K/uL'],
    'is_abnormal':     [True, True, True],
    'severity_score':  [0.85, 0.72, 0.61],
    'ref_range_upper': [1.2, 2.2, 11.0],
})

summary = sg.generate(
    subject_id=12345,
    hadm_id=678901,
    note_text=note,
    lab_features_df=labs_df,
    vitals_features_df=pd.DataFrame(),
    mortality_prob=0.38,
)
print(json.dumps(summary, indent=2, default=str))
