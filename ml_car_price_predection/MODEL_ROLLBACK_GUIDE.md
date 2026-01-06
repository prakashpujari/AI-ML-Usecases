# 🔄 Model Performance Rollback Guide

Automatically detect performance degradation and rollback to previous model versions with one command.

## Overview

The rollback system provides:

- **Automatic Detection**: Continuously monitor model performance metrics
- **Degradation Alerts**: Alert when R² decreases or RMSE increases
- **Automatic Rollback**: Automatically revert to previous version if degradation detected
- **Manual Control**: Manually rollback to any previous version
- **Version Comparison**: Compare metrics between versions
- **Performance History**: Track all model versions and their performance

## Quick Start

### Automatic Performance Check & Rollback

```bash
# Check performance and automatically rollback if degraded (5% threshold)
python scripts/monitor_model_performance.py --check

# Use custom degradation threshold
python scripts/monitor_model_performance.py --check --threshold 3.0
```

### Manual Rollback

```bash
# Rollback to previous version (one step back)
python scripts/monitor_model_performance.py --rollback-previous

# Rollback to specific version
python scripts/monitor_model_performance.py --rollback 20260105_143022
```

### View Model Status

```bash
# Show current model status
python scripts/monitor_model_performance.py --status

# Show version history (last 10 versions)
python scripts/monitor_model_performance.py --history

# Show last 20 versions
python scripts/monitor_model_performance.py --history 20
```

### Compare Versions

```bash
# Compare two specific versions
python scripts/monitor_model_performance.py --compare 20260105_143022 20260104_120000
```

## How It Works

### Detection Mechanism

```
Current Model vs Previous Model
       ↓
Calculate Metric Changes:
- R² change: (current_r2 - previous_r2) / |previous_r2| * 100
- RMSE change: (current_rmse - previous_rmse) / |previous_rmse| * 100
       ↓
Compare Against Threshold (default 5%)
       ↓
If R² decreased > 5% OR RMSE increased > 5%
       ↓
DEGRADATION DETECTED
```

### Rollback Decision Tree

```
Is Performance Degraded?
├─→ No: ✓ Continue with current model
│
└─→ Yes: Performance degradation detected
    ├─→ Auto-rollback enabled?
    │   ├─→ Yes: Rollback to previous version
    │   │   ├─→ Success: ✓ Using previous model
    │   │   └─→ Failed: ✗ Alert admin
    │   │
    │   └─→ No: ⚠️  Alert admin for manual action
```

## Configuration

### Performance Thresholds

```python
# In monitor_model_performance.py
degradation_threshold = 5.0  # Percent

# Triggers rollback if:
# - R² drops by more than 5%
# - RMSE increases by more than 5%
```

### Automatic vs Manual

```python
# Automatic rollback (default)
monitor = ModelMonitor(auto_rollback=True)

# Manual rollback only
monitor = ModelMonitor(auto_rollback=False)
```

## Usage Examples

### Example 1: Setup Continuous Monitoring

**Create cron job** (Linux/Mac):
```bash
# Run monitoring check every hour
0 * * * * cd /path/to/project && python scripts/monitor_model_performance.py --check >> monitoring.log 2>&1
```

**Create scheduled task** (Windows):
```powershell
# Create task to run every hour
$trigger = New-JobTrigger -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 365)
Register-ScheduledJob -Name ModelMonitor -ScriptBlock { 
    cd C:\path\to\project
    python scripts/monitor_model_performance.py --check
} -Trigger $trigger
```

### Example 2: Programmatic Usage

```python
from scripts.db_utils import ModelEvaluationDB
from scripts.monitor_model_performance import ModelMonitor

# Initialize monitor
monitor = ModelMonitor(
    degradation_threshold=3.0,  # 3% threshold
    auto_rollback=True          # Auto-rollback enabled
)

# Check performance and rollback if needed
result = monitor.check_and_respond()

if result['status'] == 'ROLLED_BACK':
    print("⚠️  Model was rolled back due to performance degradation")
    print(f"Reason: R² decreased by {result['degradation_check']['r2_change_percent']}%")
elif result['status'] == 'OK':
    print("✓ Model performance is stable")

monitor.close()
```

### Example 3: Manual Intervention

```python
from scripts.monitor_model_performance import ModelMonitor

monitor = ModelMonitor(auto_rollback=False)

# View status
monitor.print_status()

# If degradation detected, manually rollback
monitor.manual_rollback()  # To previous
# OR
monitor.manual_rollback(target_version="20260104_120000")  # To specific version

monitor.close()
```

### Example 4: Compare Two Versions

```python
from scripts.monitor_model_performance import ModelMonitor

monitor = ModelMonitor()

# Compare versions
result = monitor.compare_versions("20260105_143022", "20260104_120000")

print(f"R² Current: {result['r2_current']:.4f}")
print(f"R² Previous: {result['r2_previous']:.4f}")
print(f"R² Change: {result['r2_change']:.4f}")
print(f"Degraded: {result['degraded']}")

monitor.close()
```

## Database Functions

### Check Degradation

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    result = db.check_performance_degradation(threshold_percent=5.0)
    
    if result['degraded']:
        print(f"⚠️  Degradation detected!")
        print(f"   R² Change: {result['r2_change_percent']}%")
        print(f"   RMSE Change: {result['rmse_change_percent']}%")
```

### Manual Rollback

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    # Rollback to previous version
    success = db.rollback_production_model()
    
    # OR rollback to specific version
    success = db.rollback_production_model(target_version="20260104_120000")
    
    if success:
        print("✓ Rollback successful")
    else:
        print("✗ Rollback failed")
```

### Compare Models

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    comparison = db.compare_models("20260105_143022", "20260104_120000")
    
    print(f"Current: v{comparison['current_version']}")
    print(f"  R²: {comparison['r2_current']}")
    print(f"\nPrevious: v{comparison['previous_version']}")
    print(f"  R²: {comparison['r2_previous']}")
    print(f"\nDegraded: {comparison['degraded']}")
```

### Get Model History

```python
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    history = db.get_model_history(limit=10)
    
    for model in history:
        prod = "🚀 PROD" if model['is_production'] else "    "
        print(f"{prod} v{model['model_version']}: "
              f"R²={model['r2_score']}, "
              f"Size={model['size_mb']}MB")
```

## Monitoring Workflow

### Recommended Setup

```
┌──────────────────────────────────────────────────────┐
│  Every Hour (Cron Job / Scheduled Task)              │
├──────────────────────────────────────────────────────┤
│  1. Run: monitor_model_performance.py --check        │
│  2. Check latest predictions in model_predictions    │
│  3. Calculate metrics from actual vs predicted       │
│  4. Compare with previous version metrics            │
│  5. If degraded > 5%:                                │
│     → Auto-rollback (if enabled)                     │
│     → Alert admin with details                       │
│  6. Log results in monitoring.log                    │
└──────────────────────────────────────────────────────┘
```

### Log Format

```
2026-01-05 14:32:22 INFO ==================================================================================
2026-01-05 14:32:22 INFO 🔍 STARTING MODEL PERFORMANCE CHECK
2026-01-05 14:32:22 INFO ==================================================================================
2026-01-05 14:32:23 INFO ✓ No performance degradation detected
2026-01-05 14:32:23 INFO    R² Change: -0.5%
2026-01-05 14:32:23 INFO    RMSE Change: 0.2%
2026-01-05 14:32:23 INFO    Current R²: 0.9234
2026-01-05 14:32:23 INFO    Previous R²: 0.9285
2026-01-05 14:32:23 INFO ==================================================================================
```

## Degradation Scenarios

### Scenario 1: Minor Performance Drop

```
Current Model: R² = 0.92, RMSE = 3500
Previous Model: R² = 0.93, RMSE = 3480

Change:
- R² Change: -1.08% (within 5% threshold)
- RMSE Change: 0.57% (within 5% threshold)

Result: ✓ NO ROLLBACK (acceptable variation)
```

### Scenario 2: Significant Degradation

```
Current Model: R² = 0.85, RMSE = 4200
Previous Model: R² = 0.93, RMSE = 3480

Change:
- R² Change: -8.6% (exceeds 5% threshold)
- RMSE Change: 20.7% (exceeds 5% threshold)

Result: 🔄 ROLLBACK TRIGGERED
→ Revert to previous model
→ Log alert
→ Notify admin
```

### Scenario 3: Data Distribution Shift

```
New data has different characteristics:
- Different feature ranges
- Different class distribution
- Different seasonal patterns

Detection:
→ Model predictions diverge from actual
→ Metrics degrade
→ Automatic rollback to stable version

Recovery:
→ Investigate data shift
→ Retrain with new data distribution
→ Deploy new version when ready
```

## Best Practices

✅ **DO**:
- Run monitoring checks regularly (hourly/daily)
- Set appropriate degradation threshold (3-5%)
- Keep multiple model versions available
- Log all rollback events
- Alert stakeholders on significant events
- Archive old versions periodically
- Monitor predictions alongside metrics

❌ **DON'T**:
- Set threshold too low (causes false positives)
- Ignore repeated rollback events
- Delete old versions prematurely
- Deploy without monitoring setup
- Use only one version in production
- Ignore data quality issues

## Troubleshooting

### Issue: "No performance degradation detected" but metrics look bad

**Solution**: Check degradation threshold
```python
# Try lower threshold
monitor = ModelMonitor(degradation_threshold=2.0)
result = monitor.check_and_respond()
```

### Issue: "Rollback failed - target version not found"

**Solution**: Check available versions
```bash
python scripts/monitor_model_performance.py --history
```

### Issue: Constant rollbacks (unstable models)

**Solution**:
1. Investigate data quality issues
2. Check for concept drift
3. Retrain with better data
4. Increase threshold temporarily to stabilize

### Issue: Database connection error during rollback

**Solution**: Check database status
```bash
# Verify database is running
docker-compose -f deployment/dev/docker-compose.dev.yml ps postgres

# Check connection
python -c "from scripts.db_utils import ModelEvaluationDB; ModelEvaluationDB()"
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Model Performance Check

on:
  schedule:
    - cron: '0 * * * *'  # Hourly

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Check model performance
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: python scripts/monitor_model_performance.py --check
      
      - name: Upload logs
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: monitoring-logs
          path: monitoring.log
```

## Alerts & Notifications

### Email Notification on Rollback

```python
import smtplib
from email.mime.text import MIMEText

def notify_admin(result):
    if result['status'] == 'ROLLED_BACK':
        msg = MIMEText(
            f"Model rolled back to {result['degradation_check']['previous_version']}\n"
            f"Reason: R² decreased by {result['degradation_check']['r2_change_percent']}%"
        )
        msg['Subject'] = "🔄 Model Rollback Alert"
        msg['From'] = "model-monitor@example.com"
        msg['To'] = "admin@example.com"
        
        # Send email...
```

## Performance Metrics Explained

### R² Score (Coefficient of Determination)
- Range: -∞ to 1.0
- 1.0 = Perfect predictions
- 0.5 = Model explains 50% of variance
- < 0 = Model worse than baseline
- **Degradation**: Score decreases

### RMSE (Root Mean Square Error)
- Range: 0 to +∞
- Lower is better
- Unit: Same as target variable
- **Degradation**: Score increases

### Threshold Impact
- **3%**: Strict, catches small issues, may have false positives
- **5%**: Balanced (recommended)
- **10%**: Lenient, catches major issues only

---

**Next Steps**:
1. Deploy monitoring in production
2. Set up cron job for hourly checks
3. Configure alerts for your team
4. Monitor for first week to tune threshold
5. Archive models monthly

Check [DATABASE_MODEL_STORAGE.md](DATABASE_MODEL_STORAGE.md) for storage details
