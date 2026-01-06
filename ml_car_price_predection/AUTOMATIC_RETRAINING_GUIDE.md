# Automatic Model Retraining System

## Overview

A comprehensive **Automatic Model Retraining System** that continuously monitors model performance and automatically retrains the model when drift, degradation, or inefficiency is detected.

## Features

### 1. **Data Drift Detection** 📊
- **Kolmogorov-Smirnov Test**: Detects changes in feature distribution
- **Outlier Detection**: Z-score based outlier identification
- **Per-column Analysis**: Identifies which features drifted
- **Threshold-based Triggering**: Configurable sensitivity

### 2. **Concept Drift Detection** 🔄
- **Prediction Error Analysis**: Monitors if errors are increasing
- **Window-based Comparison**: Compares performance across time windows
- **Trend Detection**: Identifies gradual performance decline
- **Confidence Scoring**: Quantifies drift severity

### 3. **Performance Degradation Detection** 📉
- **R² Monitoring**: Tracks coefficient of determination
- **RMSE Tracking**: Monitors prediction errors
- **Accuracy Monitoring**: Watches classification accuracy
- **Historical Comparison**: Compares against baseline

### 4. **Automatic Retraining** 🚀
- **Trigger-based**: Only retrains when needed
- **Data Preparation**: Combines historical + recent data
- **Background Execution**: Doesn't block production
- **Result Logging**: Tracks all retraining events

### 5. **Intelligent Decision Making** 🧠
- **Multi-signal Fusion**: Combines multiple drift signals
- **Severity Classification**: LOW/MEDIUM/HIGH/CRITICAL
- **Confidence Scoring**: Quantifies trigger certainty
- **Root Cause Analysis**: Identifies which signals triggered

## Components

### 1. **automatic_retraining.py**
Drift detection and retraining decision engine

```python
# Data drift detector
detector = DataDriftDetector(threshold=0.05)
drift_detected, metrics = detector.detect_distribution_shift(
    reference_data, current_data
)

# Concept drift detector
detector = ConceptDriftDetector(window_size=100)
drift_detected, metrics = detector.detect_prediction_error_drift(
    predictions, actuals
)

# Main orchestrator
orchestrator = AutomaticRetrainingOrchestrator()
trigger = orchestrator.should_retrain(
    reference_data, recent_data, predictions, actuals, metrics
)
```

### 2. **retraining_executor.py**
Executes the actual retraining process

```python
executor = RetrainingExecutor(project_root=".")

# Execute full pipeline
result = executor.execute_full_retraining_pipeline(
    reference_data=reference_data,
    recent_data=recent_data,
    recent_predictions=predictions,
    recent_actuals=actuals,
    current_metrics=metrics
)
```

### 3. **automatic_retraining_dag.py**
Airflow orchestration (runs every 6 hours)

Tasks:
- Analyze retraining need
- Check decision
- Execute retraining
- Log completion

## Detection Methods

### Data Drift Detection

**Kolmogorov-Smirnov Test**
```
Compares distribution of each numeric column between:
- Reference data (original training set)
- Recent data (current predictions)

If p-value < threshold (default 0.05):
  → Data drift detected in that column
```

**Outlier Detection**
```
Uses Z-score method:
  Z = (value - mean) / std_dev
  
If |Z| > threshold (default 3.0):
  → Outlier detected
  
If outliers > 5% of data:
  → Trigger retraining
```

### Concept Drift Detection

**Prediction Error Analysis**
```
Splits prediction history into windows:
1. Calculate MAE for first window
2. Calculate MAE for second window
3. Compute error increase percentage

If increase > threshold (default 15%):
  → Concept drift detected
```

### Performance Degradation Detection

**Metric Comparison**
```
Compare current metrics against baseline:
- R² degradation > 5%
- RMSE increase > 10%
- Accuracy drop > 5%

If any threshold exceeded:
  → Performance degradation detected
```

## Severity Classification

| Level | Condition | Action |
|-------|-----------|--------|
| 🟢 LOW | Single mild signal | Monitor |
| 🟡 MEDIUM | Multiple signals OR strong single signal | Investigate |
| 🟠 HIGH | Strong multiple signals | Plan retraining |
| 🔴 CRITICAL | Very strong signals | Immediate retraining |

## Usage Examples

### Check If Retraining Is Needed

```bash
python scripts/automatic_retraining.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv \
  --recent-predictions recent_predictions.npy \
  --recent-actuals recent_actuals.npy \
  --r2 0.85 \
  --rmse 0.35
```

**Output:**
```
════════════════════════════════════════════
RETRAINING DECISION: YES
════════════════════════════════════════════
Reason: Multiple triggers detected: data_drift, concept_drift
Severity: HIGH
Confidence: 82.45%
════════════════════════════════════════════
```

### Execute Retraining Pipeline

```bash
python scripts/retraining_executor.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv
```

**Process:**
1. ✓ Detecting drift/degradation
2. ✓ Preparing training data
3. ✓ Executing model training
4. ✓ Validating new model
5. ✓ Logging results

### Python API

```python
from scripts.automatic_retraining import AutomaticRetrainingOrchestrator
import pandas as pd

# Load data
ref_data = pd.read_csv("data/trainset/train.csv")
recent_data = pd.read_csv("data/recent_data.csv")
predictions = np.load("predictions.npy")
actuals = np.load("actuals.npy")

# Analyze
orchestrator = AutomaticRetrainingOrchestrator()
trigger = orchestrator.should_retrain(
    ref_data, recent_data, predictions, actuals,
    {'r2': 0.85, 'rmse': 0.35}
)

if trigger.triggered:
    print(f"Retraining needed!")
    print(f"Reason: {trigger.reason}")
    print(f"Severity: {trigger.severity}")
```

## Database Tables

### model_retraining_events Table

```sql
CREATE TABLE model_retraining_events (
    id SERIAL PRIMARY KEY,
    trigger_type VARCHAR(50),           -- data_drift, concept_drift, etc.
    severity VARCHAR(20),               -- LOW, MEDIUM, HIGH, CRITICAL
    drift_type VARCHAR(50),
    trigger_reason TEXT,
    trigger_metrics JSONB,              -- Raw metrics
    execution_attempted BOOLEAN,
    execution_successful BOOLEAN,
    execution_metrics JSONB,            -- Execution details
    retraining_model_version VARCHAR(50),
    retraining_r2 FLOAT,
    retraining_rmse FLOAT,
    retraining_accuracy FLOAT,
    comparison_previous_r2 FLOAT,
    improvement_r2_percent FLOAT,
    triggered_at TIMESTAMP,
    execution_completed_at TIMESTAMP
);
```

### Indexes for Performance

```sql
CREATE INDEX idx_retraining_severity ON model_retraining_events(severity);
CREATE INDEX idx_retraining_trigger_type ON model_retraining_events(trigger_type);
CREATE INDEX idx_retraining_triggered_at ON model_retraining_events(triggered_at DESC);
CREATE INDEX idx_retraining_execution_successful ON model_retraining_events(execution_successful);
```

## Configuration

### Drift Detection Thresholds

```python
# Data drift threshold (p-value)
data_drift_threshold = 0.05  # Default: 5%

# Performance degradation threshold
r2_threshold = 0.05          # R² drop > 5%
rmse_threshold = 0.10        # RMSE increase > 10%

# Concept drift threshold
error_threshold = 0.15       # Error increase > 15%

# Outlier threshold
z_score_threshold = 3.0      # 3 standard deviations
outlier_pct_threshold = 5.0  # > 5% outliers

# Minimum samples for retraining
min_samples = 100            # Need at least 100 recent samples
```

### Customize Thresholds

```python
orchestrator = AutomaticRetrainingOrchestrator(
    data_drift_threshold=0.03,  # Stricter
    performance_threshold=0.03,
    min_samples_for_retraining=200
)
```

## Workflow

```
┌─────────────────────────────────────┐
│  Continuous Monitoring (Every 6h)  │
│  ├─ Data drift detection           │
│  ├─ Concept drift detection        │
│  ├─ Performance degradation check  │
│  └─ Outlier detection              │
└──────────────┬──────────────────────┘
               │
        ┌──────▼──────┐
        │ Triggers?   │
        └──────┬──────┘
               │
          ┌────┴────┐
          │          │
        NO          YES
          │          │
          │    ┌─────▼──────┐
          │    │ Calculate  │
          │    │ Severity & │
          │    │ Confidence │
          │    └─────┬──────┘
          │          │
          │    ┌─────▼──────────────┐
          │    │ Prepare Training   │
          │    │ Data (merge recent)│
          │    └─────┬──────────────┘
          │          │
          │    ┌─────▼──────┐
          │    │ Execute    │
          │    │ Retraining │
          │    └─────┬──────┘
          │          │
          │    ┌─────▼──────┐
          │    │ Validate   │
          │    │ New Model  │
          │    └─────┬──────┘
          │          │
          │    ┌─────▼──────┐
          │    │ Log Event  │
          │    │ to DB      │
          │    └────────────┘
          │
    ┌─────▼────────┐
    │ Continue     │
    │ Monitoring   │
    └──────────────┘
```

## Airflow Integration

### Schedule

```
Every 6 hours (0 */6 * * *)
├─ analyze_retraining_need (2 min)
├─ check_retraining_decision (1 min)
├─ execute_retraining (5-30 min)
└─ log_retraining_completion (1 min)
```

### View in Airflow UI

1. Go to `http://localhost:8080`
2. Find DAG: `automatic_model_retraining`
3. View task status and logs
4. Monitor retraining progress

## Queries

### Find All Retraining Events

```sql
SELECT * FROM model_retraining_events 
ORDER BY triggered_at DESC;
```

### Check Recent Retraining

```sql
SELECT 
    triggered_at, 
    severity, 
    trigger_type,
    execution_successful,
    improvement_r2_percent
FROM model_retraining_events
WHERE triggered_at > NOW() - INTERVAL '7 days'
ORDER BY triggered_at DESC;
```

### Analyze Trigger Frequency

```sql
SELECT 
    trigger_type,
    COUNT(*) as frequency,
    AVG(CAST(execution_successful AS INT)) * 100 as success_rate
FROM model_retraining_events
GROUP BY trigger_type;
```

### Check Improvement After Retraining

```sql
SELECT 
    triggered_at,
    improvement_r2_percent,
    improvement_rmse_percent,
    improvement_accuracy_percent
FROM model_retraining_events
WHERE execution_successful = TRUE
ORDER BY triggered_at DESC;
```

## Best Practices

### 1. Appropriate Thresholds
- Start conservative (few triggers)
- Adjust based on observation
- Different thresholds for dev vs prod

### 2. Regular Monitoring
- Review retraining events daily
- Check success rates
- Validate model improvements

### 3. Data Quality
- Ensure recent data is clean
- Monitor for data quality issues
- Log data quality metrics

### 4. Resource Management
- Schedule retraining during low-traffic hours
- Limit concurrent retraining jobs
- Monitor computational costs

### 5. Testing
- Test in staging before production
- Validate new models thoroughly
- Compare against baseline

## Troubleshooting

### No Triggers Being Detected

1. Check data is being collected
2. Verify thresholds aren't too high
3. Ensure reference data is correct
4. Check for data loading errors

### Retraining Failing

1. Check training script errors
2. Verify data files exist
3. Check logs: `retraining_executor.log`
4. Ensure sufficient disk space

### False Positives

1. Increase thresholds
2. Require multiple signals
3. Increase confidence requirement
4. Review trigger metrics

## Performance

| Operation | Time |
|-----------|------|
| Drift detection | < 30s |
| Decision making | < 10s |
| Data preparation | < 5m |
| Model retraining | 5-30m |
| Validation | < 5m |
| Total pipeline | 10-45m |

## Files

```
scripts/
├─ automatic_retraining.py (850 lines)
│  ├─ DriftType enum
│  ├─ RetrainingTrigger dataclass
│  ├─ DataDriftDetector class
│  ├─ ConceptDriftDetector class
│  ├─ ModelPerformanceMonitor class
│  └─ AutomaticRetrainingOrchestrator class
│
├─ retraining_executor.py (600 lines)
│  └─ RetrainingExecutor class
│     ├─ prepare_training_data()
│     ├─ execute_retraining()
│     ├─ log_retraining_event()
│     └─ execute_full_retraining_pipeline()
│
└─ db_utils.py (modified)
   └─ Added model_retraining_events table
      with 4 indexes

airflow/dags/
└─ automatic_retraining_dag.py (250 lines)
   ├─ analyze_retraining_need task
   ├─ check_retraining_decision task
   ├─ execute_retraining task
   └─ log_retraining_completion task
```

## Integration Points

✅ **Model Monitoring** - Uses degradation analysis  
✅ **Airflow** - Scheduled execution  
✅ **Database** - Stores events and metrics  
✅ **Training Script** - Calls existing train.py  
✅ **Model Storage** - Updates model artifacts  

## Next Steps

1. **Start monitoring**: Airflow DAG runs automatically
2. **Review events**: Check database for triggers
3. **Adjust thresholds**: Based on observation
4. **Validate improvements**: Check model performance after retraining
5. **Iterate**: Refine detection parameters

## Summary

The Automatic Model Retraining System provides:

✅ **Continuous Monitoring** - 24/7 drift/degradation detection  
✅ **Intelligent Triggers** - Multi-signal fusion with confidence  
✅ **Automatic Execution** - No manual intervention needed  
✅ **Comprehensive Logging** - Full audit trail  
✅ **Easy Validation** - Simple metrics comparison  
✅ **Production Ready** - Fully documented and tested  

All configured and ready to automatically maintain model performance!
