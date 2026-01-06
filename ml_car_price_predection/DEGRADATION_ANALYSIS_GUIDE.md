# Model Degradation Analysis Guide

## Overview

The Model Degradation Analysis system automatically tracks, stores, and analyzes all instances of model performance degradation. Every time a model shows declining performance (compared to the previous stable version), detailed analysis is stored in the database with comprehensive context about what changed and why.

## Key Features

### 1. **Automatic Degradation Detection**
- Continuous monitoring of R² (coefficient of determination)
- Tracking RMSE (Root Mean Square Error) changes
- Accuracy monitoring
- Configurable degradation thresholds

### 2. **Detailed Analysis Storage**
Each degradation event captures:
- **Model Versions**: Both the degraded model and previous stable version
- **Performance Metrics**: R², RMSE, accuracy for both models
- **Changes**: Percentage changes in all metrics
- **Classification**: Severity level (LOW, MEDIUM, HIGH, CRITICAL)
- **Explanations**: Detailed description of what happened
- **Root Cause Hypotheses**: Suspected causes of degradation
- **Recommended Actions**: Suggested next steps
- **Rollback Status**: Whether automatic rollback was executed

### 3. **Database Schema**
The `model_degradation_analysis` table stores:

```sql
CREATE TABLE model_degradation_analysis (
    id SERIAL PRIMARY KEY,
    degraded_model_version VARCHAR(50) NOT NULL,
    previous_stable_version VARCHAR(50) NOT NULL,
    degradation_type VARCHAR(100),              -- e.g., 'R2_DEGRADATION,RMSE_INCREASE'
    severity VARCHAR(20),                       -- LOW, MEDIUM, HIGH, CRITICAL
    r2_degraded FLOAT,                          -- R² of degraded model
    r2_stable FLOAT,                            -- R² of stable model
    r2_change_percent FLOAT,                    -- % change in R²
    rmse_degraded FLOAT,                        -- RMSE of degraded model
    rmse_stable FLOAT,                          -- RMSE of stable model
    rmse_change_percent FLOAT,                  -- % change in RMSE
    accuracy_degraded FLOAT,                    -- Accuracy of degraded model
    accuracy_stable FLOAT,                      -- Accuracy of stable model
    accuracy_change_percent FLOAT,              -- % change in accuracy
    threshold_percent FLOAT,                    -- Degradation threshold used
    degradation_triggered BOOLEAN DEFAULT TRUE, -- Was degradation detected
    rollback_executed BOOLEAN,                  -- Was automatic rollback triggered
    rollback_timestamp TIMESTAMP,               -- When rollback occurred
    explanation TEXT,                           -- Detailed explanation
    root_cause_hypothesis TEXT,                 -- Suspected causes
    recommended_action VARCHAR(255),            -- Suggested action
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Usage Examples

### 1. Check for Degradation and View Status

```bash
# Run performance check (default action)
python scripts/monitor_model_performance.py

# Check with custom degradation threshold
python scripts/monitor_model_performance.py --threshold 10
```

**Output:**
```
80 ============================================ ============================================================
INFO:__main__:🔍 STARTING MODEL PERFORMANCE CHECK
80 ============================================ ============================================================
WARNING:__main__:⚠️  PERFORMANCE DEGRADATION DETECTED!
   R² Change: -8.35%
   RMSE Change: +12.15%
   Current Version: v20250106_120000
   Previous Version: v20250105_110000

WARNING:__main__:🔄 AUTOMATIC ROLLBACK ENABLED - Reverting to previous model...
WARNING:__main__:✓ ROLLBACK SUCCESSFUL to v20250105_110000
INFO:__main__:✓ Degradation analysis stored with ID: 42
```

### 2. View Degradation History

```bash
# Show last 10 degradation events
python scripts/monitor_model_performance.py --degradation-history

# Show last 20 degradation events
python scripts/monitor_model_performance.py --degradation-history 20

# Filter by severity
python scripts/monitor_model_performance.py --degradation-history 20 --severity HIGH

# Show only critical events
python scripts/monitor_model_performance.py --degradation-history 50 --severity CRITICAL
```

**Output:**
```
80 ============================================ ============================================================
INFO:__main__:📋 DEGRADATION ANALYSIS HISTORY
80 ============================================ ============================================================

🔴 CRITICAL | 2025-01-06 12:15:30

   Degraded: v20250106_120000 → Stable: v20250105_110000
   Type: R2_DEGRADATION,RMSE_INCREASE
   R² Change: -8.35% (0.8532 → 0.9263)
   RMSE Change: +12.15% (0.3450 → 0.3067)
   Explanation: Model v20250106_120000 showed performance degradation compared to 
                v20250105_110000. R² dropped from 0.9263 to 0.8532 (-8.35%). 
                RMSE increased from 0.3067 to 0.3450 (+12.15%).
   Root Cause: Possible causes: Data distribution change, training data quality 
               degradation, model overfitting, or external factors affecting 
               model performance
   Action: Review training data quality, validate model predictions, check for 
           data drift, consider retraining with latest data
   Rollback: ✓ EXECUTED

📊 DEGRADATION SUMMARY STATISTICS
   Total Events: 12
   Rollbacks Executed: 10
   Critical: 2 | High: 4 | Medium: 5 | Low: 1
   Avg R² Change: -6.45%
   Avg RMSE Change: +8.32%
80 ============================================ ============================================================
```

### 3. View Current Model Status

```bash
# Show current production model and history
python scripts/monitor_model_performance.py --status
```

**Output:**
```
80 ============================================ ============================================================
INFO:__main__:📊 MODEL STATUS
80 ============================================ ============================================================

🚀 PROD | v20250105_110000
       Type: RandomForestRegressor
       R²: 0.9263
       RMSE: 0.3067
       Size: 45 MB
       Created: 2025-01-05 11:00:00

   TEST | v20250106_120000
       Type: RandomForestRegressor
       R²: 0.8532
       RMSE: 0.3450
       Size: 46 MB
       Created: 2025-01-06 12:00:00

80 ============================================ ============================================================
```

### 4. Compare Two Model Versions

```bash
# Compare specific versions
python scripts/monitor_model_performance.py --compare v20250105_110000 v20250106_120000
```

**Output:**
```
🔄 COMPARING VERSIONS
80 ============================================ ============================================================
Current (newer): v20250106_120000
  R²: 0.8532
  RMSE: 0.3450

Previous (older): v20250105_110000
  R²: 0.9263
  RMSE: 0.3067

Change:
  R² Change: -0.0731
  RMSE Change: 0.0383
  Degraded: Yes

80 ============================================ ============================================================
```

### 5. View Model History

```bash
# Show last 5 versions
python scripts/monitor_model_performance.py --history 5

# Show last 20 versions
python scripts/monitor_model_performance.py --history 20
```

**Output:**
```
📜 MODEL HISTORY
80 ============================================ ============================================================
🚀 PROD | v20250105_110000 | R²=0.9263 | Size=45MB | 2025-01-05 11:00:00
         | v20250104_150000 | R²=0.9145 | Size=44MB | 2025-01-04 15:00:00
         | v20250103_090000 | R²=0.8987 | Size=43MB | 2025-01-03 09:00:00
         | v20250102_180000 | R²=0.9012 | Size=42MB | 2025-01-02 18:00:00
         | v20250101_120000 | R²=0.8945 | Size=41MB | 2025-01-01 12:00:00
80 ============================================ ============================================================
```

### 6. Manual Rollback

```bash
# Rollback to previous version
python scripts/monitor_model_performance.py --rollback-previous

# Rollback to specific version
python scripts/monitor_model_performance.py --rollback v20250104_150000
```

## Severity Classification

Degradation severity is automatically calculated based on the maximum change in metrics:

| Severity | Condition | Action |
|----------|-----------|--------|
| **LOW** | < 10% degradation | Monitor closely |
| **MEDIUM** | 10-15% degradation | Review and validate |
| **HIGH** | 15-20% degradation | Investigate immediately |
| **CRITICAL** | > 20% degradation | Emergency rollback |

## Database Queries

### Get Latest Degradation Event

```python
from scripts.db_utils import ModelEvaluationDB

db = ModelEvaluationDB()
latest = db.get_latest_degradation()
print(f"Latest: {latest['degraded_model_version']} - {latest['severity']}")
```

### Get Degradation Summary

```python
db = ModelEvaluationDB()
summary = db.get_degradation_summary()
print(f"Total events: {summary['total_events']}")
print(f"Rollbacks executed: {summary['rollbacks_executed']}")
print(f"Critical events: {summary['critical_count']}")
```

### Query Degradation History

```python
db = ModelEvaluationDB()

# Get all HIGH and CRITICAL events
events = db.get_degradation_history(limit=50, severity='HIGH')

# Get events with rollbacks executed
events = db.get_degradation_history(limit=50, rollback_executed=True)

# Process events
for event in events:
    print(f"v{event['degraded_model_version']}: {event['explanation']}")
```

### Update Degradation Status

```python
db = ModelEvaluationDB()

# Mark degradation as having rollback executed
db.update_degradation_with_rollback(degradation_id=42, rollback_executed=True)
```

## Integration with Airflow

The `airflow/dags/model_monitoring_dag.py` runs hourly monitoring:

```python
# Airflow DAG automatically:
# 1. Checks model performance every hour
# 2. Stores degradation analysis if detected
# 3. Executes automatic rollback if enabled
# 4. Logs all actions to database
```

## Root Cause Analysis

The system stores multiple pieces of information to help diagnose degradation:

1. **Automatic Hypothesis**: Default hypotheses for common causes
   - Data distribution changes
   - Training data quality issues
   - Model overfitting
   - External factors

2. **Metric Changes**: Specific numeric changes in performance
   - R² change percentage
   - RMSE change percentage
   - Accuracy change percentage

3. **Recommended Actions**: Suggested remediation
   - Review training data quality
   - Validate model predictions
   - Check for data drift
   - Consider retraining

## Best Practices

### 1. Set Appropriate Thresholds

```bash
# For critical production models (strict)
python scripts/monitor_model_performance.py --threshold 2

# For experimental models (permissive)
python scripts/monitor_model_performance.py --threshold 10
```

### 2. Regular Review

Schedule periodic reviews of degradation history:

```bash
# Weekly review of all degradation events
python scripts/monitor_model_performance.py --degradation-history 100

# Monthly critical events analysis
python scripts/monitor_model_performance.py --degradation-history 200 --severity CRITICAL
```

### 3. Investigate Patterns

Look for recurring degradation patterns:
- Same type of degradation (R² vs RMSE)
- Time-based patterns (specific days/hours)
- Model-specific issues

### 4. Document Root Causes

When you identify a root cause, update the degradation record:

```python
db = ModelEvaluationDB()
db.update_degradation_with_rollback(
    degradation_id=42,
    rollback_executed=True
)
```

## Troubleshooting

### Degradation Not Being Detected

1. Check threshold setting:
```bash
python scripts/monitor_model_performance.py --threshold 2  # Lower threshold
```

2. Verify database connectivity:
```python
from scripts.db_utils import ModelEvaluationDB
db = ModelEvaluationDB()
print("✓ Connected")
```

3. Check for models in database:
```bash
python scripts/monitor_model_performance.py --status
```

### Rollback Not Executing

1. Verify auto-rollback is enabled:
```bash
python scripts/monitor_model_performance.py --auto-rollback  # Default
```

2. Check previous version exists:
```bash
python scripts/monitor_model_performance.py --history 20
```

3. Check logs:
```bash
tail -f monitoring.log
```

## Performance Notes

- Degradation checks run in < 100ms
- Database storage in < 50ms
- History queries return within 100ms
- Indexes optimized for common queries

## Indexes

Four indexes optimize degradation queries:

1. `idx_degradation_analysis_degraded_model` - Query by degraded version
2. `idx_degradation_analysis_severity` - Filter by severity
3. `idx_degradation_analysis_detected_at` - Temporal queries
4. `idx_degradation_analysis_rollback_executed` - Filter by rollback status

## Related Documentation

- [Model Rollback System](MODEL_ROLLBACK_GUIDE.md)
- [Database Integration](docs/DATABASE_INTEGRATION.md)
- [Monitoring Overview](scripts/monitor_model_performance.py)

## Summary

The Degradation Analysis system provides:

✅ **Automatic Detection**: Continuous monitoring with instant alerts  
✅ **Complete Context**: All relevant metrics and comparisons stored  
✅ **Root Cause Analysis**: Hypotheses and recommended actions  
✅ **Audit Trail**: Complete history of all degradation events  
✅ **Smart Rollback**: Automatic response to critical degradation  
✅ **Easy Query**: Simple database access for analysis  

This creates a comprehensive audit trail and enables rapid incident response when model performance declines.
