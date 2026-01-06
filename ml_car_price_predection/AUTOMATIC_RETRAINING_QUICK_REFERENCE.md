# Automatic Retraining - Quick Reference

## Quick Start

```bash
# Check if retraining is needed
python scripts/automatic_retraining.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv \
  --recent-predictions predictions.npy \
  --recent-actuals actuals.npy

# Execute full retraining pipeline
python scripts/retraining_executor.py \
  --reference-data data/trainset/train.csv \
  --recent-data data/recent_data.csv
```

## Detection Triggers

| Trigger | Detection Method | Threshold | Action |
|---------|-----------------|-----------|--------|
| **Data Drift** | Kolmogorov-Smirnov test | p < 0.05 | Check features |
| **Outliers** | Z-score | > 5% outliers | Flag data quality |
| **Concept Drift** | Error increase | > 15% increase | High priority |
| **Performance Drop** | R² comparison | > 5% drop | Investigate |
| **RMSE Increase** | RMSE comparison | > 10% increase | Monitor |

## Severity Levels

- 🟢 **LOW**: Single mild signal → Monitor
- 🟡 **MEDIUM**: Multiple signals → Investigate  
- 🟠 **HIGH**: Strong signals → Plan retraining
- 🔴 **CRITICAL**: Very strong signals → Immediate retraining

## Python API

```python
from scripts.automatic_retraining import AutomaticRetrainingOrchestrator
import pandas as pd
import numpy as np

# Load data
ref_data = pd.read_csv("data/trainset/train.csv")
recent_data = pd.read_csv("data/recent_data.csv")
predictions = np.random.randn(100)
actuals = np.random.randn(100)

# Create orchestrator
orchestrator = AutomaticRetrainingOrchestrator()

# Check if retraining needed
trigger = orchestrator.should_retrain(
    ref_data, recent_data, predictions, actuals,
    {'r2': 0.85, 'rmse': 0.35, 'accuracy': 0.80}
)

# Access results
if trigger.triggered:
    print(f"Type: {trigger.drift_type.value}")
    print(f"Severity: {trigger.severity}")
    print(f"Confidence: {trigger.confidence}%")
    print(f"Reason: {trigger.reason}")
```

## Database Queries

### View All Retraining Events
```sql
SELECT * FROM model_retraining_events 
ORDER BY triggered_at DESC LIMIT 10;
```

### Count by Trigger Type
```sql
SELECT trigger_type, COUNT(*) 
FROM model_retraining_events 
GROUP BY trigger_type;
```

### Successful Retrain ings
```sql
SELECT * FROM model_retraining_events 
WHERE execution_successful = TRUE 
ORDER BY triggered_at DESC;
```

### Check Improvements
```sql
SELECT 
    triggered_at,
    trigger_type,
    improvement_r2_percent,
    improvement_rmse_percent
FROM model_retraining_events
WHERE execution_successful = TRUE;
```

## Configuration

### Adjust Thresholds

```python
orchestrator = AutomaticRetrainingOrchestrator(
    data_drift_threshold=0.03,       # Stricter drift detection
    performance_threshold=0.03,      # Stricter perf check
    min_samples_for_retraining=200   # Require more samples
)
```

### In Airflow DAG

Edit `airflow/dags/automatic_retraining_dag.py`:
- Schedule: `schedule_interval='0 */6 * * *'` (every 6 hours)
- Pool: `pool='retraining_pool'` (limit concurrent)
- Retries: `retries=1` (retry once if failed)

## Monitoring

### Check Latest Event
```bash
# In database
SELECT * FROM model_retraining_events 
ORDER BY triggered_at DESC LIMIT 1;
```

### View Logs
```bash
tail -f retraining_executor.log
tail -f retraining.log
```

### In Airflow UI
1. Go to `http://localhost:8080`
2. Find DAG: `automatic_model_retraining`
3. Click on task to see logs
4. Check XCom for inter-task communication

## Triggers Explained

### Data Drift
- **What**: Input features distribution changed
- **Impact**: Model trained on different data
- **Solution**: Retrain with new distribution

### Concept Drift
- **What**: Relationship between features and target changed
- **Impact**: Model assumptions no longer valid
- **Solution**: Retrain to learn new relationship

### Performance Degradation
- **What**: Model accuracy/R² declined
- **Impact**: Less accurate predictions
- **Solution**: Retrain with recent data

### Outlier Increase
- **What**: > 5% outliers detected
- **Impact**: Data quality concerns
- **Solution**: Investigate data, then retrain

## Workflow

```
Every 6 Hours:
  1. Analyze retraining need (< 2 min)
  2. Check decision (< 1 min)
  3. If triggered:
     a. Prepare data (< 5 min)
     b. Execute training (5-30 min)
     c. Validate (< 5 min)
     d. Log event (< 1 min)
  4. Continue monitoring
```

## Troubleshooting

### Retraining Not Triggering
```python
# Check thresholds are not too high
orchestrator = AutomaticRetrainingOrchestrator(
    data_drift_threshold=0.10,  # More permissive
    performance_threshold=0.10
)

# Check you have recent data
print(f"Recent data rows: {len(recent_data)}")
print(f"Min required: 100")
```

### Retraining Failing
```bash
# Check logs
tail -f retraining_executor.log

# Verify data exists
ls -l data/trainset/train.csv
ls -l data/recent_data.csv

# Check training script
python train.py --help
```

### Too Many Triggers
- Increase thresholds
- Require higher confidence
- Check data quality
- Verify reference data is correct

## Integration

### With Model Monitoring
```
Monitor → Detect Degradation → Trigger Retraining
   ↑                               ↓
   └──────── Update Model ─────────┘
```

### With Airflow
- Auto-runs every 6 hours
- Can be triggered manually
- Logs all events
- Integrates with other DAGs

## Files

- `scripts/automatic_retraining.py` - Detection logic
- `scripts/retraining_executor.py` - Execution logic
- `airflow/dags/automatic_retraining_dag.py` - Airflow DAG
- `AUTOMATIC_RETRAINING_GUIDE.md` - Full guide

## Next Steps

1. **Observe**: Let it run for a week
2. **Adjust**: Fine-tune thresholds
3. **Validate**: Check model improvements
4. **Optimize**: Adjust schedule/settings
5. **Scale**: Deploy across environments

## Key Metrics

Track these in your monitoring:
- Retraining frequency
- Trigger types distribution
- Execution success rate
- Model improvement per retrain
- Time to retrain
- Cost per retrain

## Support

Need help?
- Check logs in `retraining_executor.log`
- Review `AUTOMATIC_RETRAINING_GUIDE.md`
- Check database tables for history
- Review Airflow logs for DAG issues

---

**Version**: 1.0  
**Status**: Production Ready ✅  
**Last Updated**: 2025-01-06
