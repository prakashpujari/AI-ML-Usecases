# Degradation Analysis Quick Reference

## Quick Commands

### Monitor & Check
```bash
# Run monitoring (auto-detects degradation + rollback)
python scripts/monitor_model_performance.py

# Check with 10% threshold (looser)
python scripts/monitor_model_performance.py --threshold 10

# Check with 2% threshold (stricter)  
python scripts/monitor_model_performance.py --threshold 2

# Disable auto-rollback (alert only)
python scripts/monitor_model_performance.py --no-auto-rollback
```

### View History
```bash
# Last 10 degradation events
python scripts/monitor_model_performance.py --degradation-history

# Last 50 degradation events
python scripts/monitor_model_performance.py --degradation-history 50

# Only HIGH severity
python scripts/monitor_model_performance.py --degradation-history 20 --severity HIGH

# Only CRITICAL severity
python scripts/monitor_model_performance.py --degradation-history 100 --severity CRITICAL
```

### View Models
```bash
# Current model status
python scripts/monitor_model_performance.py --status

# Model history (last 5)
python scripts/monitor_model_performance.py --history 5

# Model history (last 20)
python scripts/monitor_model_performance.py --history 20

# Compare two versions
python scripts/monitor_model_performance.py --compare v1_version v2_version
```

### Rollback
```bash
# Rollback to previous version
python scripts/monitor_model_performance.py --rollback-previous

# Rollback to specific version
python scripts/monitor_model_performance.py --rollback v20250105_110000
```

## Database Fields

### model_degradation_analysis Table

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Unique record ID |
| `degraded_model_version` | VARCHAR(50) | Version with poor performance |
| `previous_stable_version` | VARCHAR(50) | Last known good version |
| `r2_degraded` | FLOAT | R² of degraded model |
| `r2_stable` | FLOAT | R² of stable model |
| `r2_change_percent` | FLOAT | % change in R² |
| `rmse_degraded` | FLOAT | RMSE of degraded model |
| `rmse_stable` | FLOAT | RMSE of stable model |
| `rmse_change_percent` | FLOAT | % change in RMSE |
| `accuracy_degraded` | FLOAT | Accuracy of degraded model |
| `accuracy_stable` | FLOAT | Accuracy of stable model |
| `accuracy_change_percent` | FLOAT | % change in accuracy |
| `severity` | VARCHAR(20) | LOW / MEDIUM / HIGH / CRITICAL |
| `degradation_type` | VARCHAR(100) | Type of degradation detected |
| `threshold_percent` | FLOAT | Threshold used for detection |
| `explanation` | TEXT | Detailed explanation |
| `root_cause_hypothesis` | TEXT | Suspected root cause |
| `recommended_action` | VARCHAR(255) | Suggested action |
| `degradation_triggered` | BOOLEAN | Was degradation detected |
| `rollback_executed` | BOOLEAN | Was automatic rollback done |
| `rollback_timestamp` | TIMESTAMP | When rollback occurred |
| `detected_at` | TIMESTAMP | When degradation detected |
| `created_at` | TIMESTAMP | Record creation time |
| `updated_at` | TIMESTAMP | Last update time |

## Severity Levels

| Level | % Degradation | Meaning | Action |
|-------|---|---------|--------|
| 🟢 LOW | < 10% | Minor degradation | Monitor |
| 🟡 MEDIUM | 10-15% | Noticeable degradation | Review |
| 🟠 HIGH | 15-20% | Significant degradation | Investigate |
| 🔴 CRITICAL | > 20% | Severe degradation | Rollback |

## Python API

### Store Degradation

```python
from scripts.db_utils import ModelEvaluationDB

db = ModelEvaluationDB()

degradation_id = db.store_degradation_analysis(
    degraded_model_version='v20250106_120000',
    previous_stable_version='v20250105_110000',
    degradation_type='R2_DEGRADATION,RMSE_INCREASE',
    severity='HIGH',
    r2_degraded=0.8532,
    r2_stable=0.9263,
    r2_change_percent=-8.35,
    rmse_degraded=0.3450,
    rmse_stable=0.3067,
    rmse_change_percent=12.15,
    threshold_percent=5.0,
    explanation='Model showed significant R² drop...',
    root_cause_hypothesis='Data distribution change...',
    recommended_action='Review training data quality...'
)

print(f"Stored degradation: {degradation_id}")
```

### Get History

```python
# Last 10 events
events = db.get_degradation_history(limit=10)

# Last 20 HIGH severity events
events = db.get_degradation_history(limit=20, severity='HIGH')

# Events with rollback executed
events = db.get_degradation_history(limit=50, rollback_executed=True)

for event in events:
    print(f"v{event['degraded_model_version']}: {event['severity']}")
```

### Get Latest

```python
latest = db.get_latest_degradation()

if latest:
    print(f"Latest: {latest['degraded_model_version']}")
    print(f"Severity: {latest['severity']}")
    print(f"R² Change: {latest['r2_change_percent']:.2f}%")
```

### Get Summary

```python
summary = db.get_degradation_summary()

print(f"Total events: {summary['total_events']}")
print(f"Rollbacks: {summary['rollbacks_executed']}")
print(f"Critical: {summary['critical_count']}")
print(f"High: {summary['high_count']}")
print(f"Medium: {summary['medium_count']}")
print(f"Low: {summary['low_count']}")
print(f"Avg R² Change: {summary['avg_r2_change']:.2f}%")
print(f"Avg RMSE Change: {summary['avg_rmse_change']:.2f}%")
```

### Update Rollback Status

```python
db.update_degradation_with_rollback(
    degradation_id=42,
    rollback_executed=True
)
```

## Output Examples

### Degradation Detected
```
⚠️  PERFORMANCE DEGRADATION DETECTED!
   R² Change: -8.35%
   RMSE Change: +12.15%
   Current Version: v20250106_120000
   Previous Version: v20250105_110000
```

### Rollback Executed
```
🔄 AUTOMATIC ROLLBACK ENABLED - Reverting to previous model...
✓ ROLLBACK SUCCESSFUL to v20250105_110000
✓ Degradation analysis stored with ID: 42
```

### Degradation History
```
🔴 CRITICAL | 2025-01-06 12:15:30
   Degraded: v20250106_120000 → Stable: v20250105_110000
   Type: R2_DEGRADATION,RMSE_INCREASE
   R² Change: -8.35% (0.8532 → 0.9263)
   RMSE Change: +12.15% (0.3450 → 0.3067)
   Rollback: ✓ EXECUTED
```

## Common Scenarios

### Scenario 1: Auto-Detection & Rollback
```bash
$ python scripts/monitor_model_performance.py
⚠️ DEGRADATION DETECTED
✓ ROLLBACK SUCCESSFUL
✓ Analysis stored
```

### Scenario 2: Review Past Events
```bash
$ python scripts/monitor_model_performance.py --degradation-history 10 --severity HIGH
Shows 10 most recent HIGH severity events
```

### Scenario 3: Manual Rollback
```bash
$ python scripts/monitor_model_performance.py --rollback-previous
🔄 MANUAL ROLLBACK INITIATED
✓ Rollback successful
```

### Scenario 4: Compare Versions
```bash
$ python scripts/monitor_model_performance.py --compare v1 v2
Shows detailed comparison of two versions
```

## Files Modified

- `scripts/db_utils.py` - Added degradation table & methods
- `scripts/monitor_model_performance.py` - Stores degradation analysis
- `airflow/dags/model_monitoring_dag.py` - Hourly monitoring
- New: `DEGRADATION_ANALYSIS_GUIDE.md` - Full documentation

## Key Methods Added

### In `db_utils.py`:

1. **`store_degradation_analysis()`** - Insert degradation event
2. **`get_degradation_history()`** - Query degradation history
3. **`get_latest_degradation()`** - Get most recent event
4. **`get_degradation_summary()`** - Statistics & summary
5. **`update_degradation_with_rollback()`** - Update after rollback

### In `monitor_model_performance.py`:

1. **`print_degradation_history()`** - Display history
2. **Updated `check_and_respond()`** - Now stores full analysis

## Indexes Created

```sql
-- Fast lookup by degraded model version
CREATE INDEX idx_degradation_analysis_degraded_model 
    ON model_degradation_analysis(degraded_model_version);

-- Fast filtering by severity
CREATE INDEX idx_degradation_analysis_severity 
    ON model_degradation_analysis(severity);

-- Fast temporal queries
CREATE INDEX idx_degradation_analysis_detected_at 
    ON model_degradation_analysis(detected_at DESC);

-- Fast filtering by rollback status
CREATE INDEX idx_degradation_analysis_rollback_executed 
    ON model_degradation_analysis(rollback_executed);
```

## Next Steps

1. **Run monitoring** to start tracking degradation
2. **Review logs** to understand baseline performance
3. **Set thresholds** appropriate for your use case
4. **Schedule checks** via Airflow (automatic hourly)
5. **Analyze patterns** when degradation occurs

## Tips

- Start with `--threshold 5` (default) for stable models
- Use `--severity CRITICAL` to focus on emergencies
- Run `--degradation-history` weekly for patterns
- Keep `--auto-rollback` enabled for production
- Review `recommended_action` for remediation steps
