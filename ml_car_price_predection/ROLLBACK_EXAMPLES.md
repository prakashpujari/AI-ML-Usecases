# 🎯 Model Rollback - Practical Examples

Real-world examples and workflows for using the model rollback system.

## Example 1: Hourly Monitoring Schedule

**Setup**: Automatically check model performance every hour in production

### Step 1: Create Monitoring Script
```bash
# File: run_hourly_monitor.sh
#!/bin/bash

cd /home/mlops/car-price-model
python scripts/monitor_model_performance.py --check --threshold 5.0

# Optional: Send Slack notification on failure
if [ $? -ne 0 ]; then
    curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Model monitoring check failed!"}' \
        $SLACK_WEBHOOK_URL
fi
```

### Step 2: Add Cron Job
```bash
# Run every hour at minute 0
crontab -e

# Add this line:
0 * * * * /home/mlops/car-price-model/run_hourly_monitor.sh >> /home/mlops/car-price-model/monitoring.log 2>&1
```

### Step 3: Monitor Logs
```bash
# Watch logs in real-time
tail -f /home/mlops/car-price-model/monitoring.log

# Output examples:
# 2026-01-05 14:00:22 INFO ✓ No performance degradation detected
# 2026-01-05 15:00:15 WARNING ⚠️  Performance degradation detected!
# 2026-01-05 15:00:16 INFO 🔄 Rollback to v20260105_130000 successful
```

---

## Example 2: Production Deployment Workflow

**Scenario**: Deploy new model to production, monitor for degradation, rollback if needed

### Step 1: Train New Model
```bash
# Train produces new model version automatically
python train.py

# Output: Model stored as v20260105_143022
```

### Step 2: Check if Better Than Previous
```python
from scripts.monitor_model_performance import ModelMonitor

monitor = ModelMonitor(auto_rollback=False)  # Manual only for validation
history = monitor.get_model_history(limit=2)

new_version = history[0]
old_version = history[1]

if new_version['r2_score'] > old_version['r2_score']:
    print(f"✓ New model is better! R²: {new_version['r2_score']:.4f}")
else:
    print(f"✗ New model is worse! Keep old model")
    monitor.manual_rollback()

monitor.close()
```

### Step 3: Monitor for 24 Hours
```bash
# Monitor closely after deployment
python scripts/monitor_model_performance.py --check --threshold 3.0

# If degradation detected, automatic rollback triggers
```

### Step 4: Final Validation
```bash
# After stable for 24 hours, promote to permanent
python scripts/monitor_model_performance.py --status

# If status is HEALTHY - deployment successful!
```

---

## Example 3: Data Quality Issue Detection

**Scenario**: Data distribution changes, model performance degrades

### The Problem
```
Week 1: Model trained on typical data
  - Price range: $15,000 - $45,000
  - Average age: 8 years
  - R² = 0.93

Week 2: New data source added (luxury cars)
  - Price range: $45,000 - $150,000
  - Average age: 3 years
  - Model predictions on luxury cars are poor
  - R² = 0.82 (11% degradation!)
```

### Detection & Response
```python
# Monitoring runs hourly:
from scripts.db_utils import ModelEvaluationDB

with ModelEvaluationDB() as db:
    result = db.check_performance_degradation(threshold_percent=5.0)
    
    # Result:
    # {
    #     'degraded': True,
    #     'r2_change_percent': -11.8,
    #     'rmse_change_percent': 22.5,
    #     'current_version': '20260105_143022',
    #     'previous_version': '20260104_120000'
    # }
    
    # Auto-rollback triggers:
    db.rollback_production_model()
    
    # Model reverts to v20260104_120000
    # Sends alert: "Data drift detected - rolled back"
```

### Resolution
```python
# Data team investigates
# They identify luxury car segment
# They retrain model with luxury car data

# New model (v20260105_150000):
# - Handles both regular and luxury cars
# - R² = 0.91 (acceptable, trained on more diverse data)
# - Deployed after validation
```

---

## Example 4: Quick Emergency Rollback

**Scenario**: Model starts giving bad predictions, need immediate rollback

### Interactive Menu (Fastest)
```bash
python quick_rollback_ref.py

# Output:
# 🎯 MODEL ROLLBACK QUICK REFERENCE
# 1. Show model status
# 2. Check degradation
# 3. Quick rollback
# ...
# Select option (1-8): 3
# 
# ⚠️  Really rollback to previous version? (yes/no): yes
# ✓ Rollback successful!
```

### Command Line (Fastest - No Prompts)
```bash
# Check status
python scripts/monitor_model_performance.py --status

# If bad: Immediate rollback
python scripts/monitor_model_performance.py --rollback-previous

# Verify new status
python scripts/monitor_model_performance.py --status
```

### Programmatic (For Automation)
```python
from scripts.db_utils import ModelEvaluationDB

# Quick check
with ModelEvaluationDB() as db:
    result = db.check_performance_degradation(threshold_percent=5.0)
    
    if result['degraded']:
        # Automatic rollback
        success = db.rollback_production_model()
        print(f"Rollback: {'Success' if success else 'Failed'}")
```

---

## Example 5: A/B Testing Two Models

**Scenario**: You want to compare two model versions and choose the better one

```python
from scripts.monitor_model_performance import ModelMonitor

monitor = ModelMonitor()

# Get candidates
history = monitor.get_model_history(limit=5)

# Select two to compare
candidate_v1 = history[0]['model_version']  # Latest
candidate_v2 = history[2]['model_version']  # From 2 days ago

# Detailed comparison
comparison = monitor.compare_versions(candidate_v1, candidate_v2)

print("A/B TEST RESULTS")
print("================")
print(f"Model A (latest): v{comparison['current_version']}")
print(f"  R²: {comparison['r2_current']:.4f}")
print(f"  RMSE: {comparison['rmse_current']:.2f}")
print()
print(f"Model B (previous): v{comparison['previous_version']}")
print(f"  R²: {comparison['r2_previous']:.4f}")
print(f"  RMSE: {comparison['rmse_previous']:.2f}")
print()
print("VERDICT:")
if comparison['r2_current'] > comparison['r2_previous']:
    print(f"✓ Model A is better (R² +{comparison['r2_change']:.4f})")
else:
    print(f"✗ Model B is better (R² +{abs(comparison['r2_change']):.4f})")

monitor.close()
```

---

## Example 6: Seasonal Model Management

**Scenario**: Maintain different models for different seasons

```python
from scripts.db_utils import ModelEvaluationDB
from datetime import datetime

with ModelEvaluationDB() as db:
    # Get all models
    all_models = db.get_model_history(limit=100)
    
    # Group by season
    current_month = datetime.now().month
    
    if current_month in [12, 1, 2]:  # Winter
        # Use winter model
        winter_models = [m for m in all_models 
                        if 'winter' in m['model_version'].lower()]
        if winter_models:
            best_winter = winter_models[0]
            db.set_production_model(best_winter['model_version'])
            print(f"✓ Activated winter model: {best_winter['model_version']}")
    
    elif current_month in [3, 4, 5]:  # Spring
        # Use spring model
        pass
    
    # Monitor selected model
    result = db.check_performance_degradation()
    if result['degraded']:
        db.rollback_production_model()
```

---

## Example 7: Integration with Airflow DAG

**Scenario**: Monitor model after training automatically in Airflow

```python
# In your training DAG (e.g., train_model_dag.py)

from airflow.operators.python import PythonOperator
from scripts.monitor_model_performance import ModelMonitor

def post_training_monitor(**context):
    """Run after model training completes"""
    monitor = ModelMonitor(
        degradation_threshold=5.0,
        auto_rollback=False  # Manual only for training
    )
    
    # Get new model info
    history = monitor.get_model_history(limit=1)
    new_model = history[0]
    
    # Check if better than previous
    if len(monitor.get_model_history(limit=2)) >= 2:
        comparison = monitor.compare_versions(
            history[0]['model_version'],
            history[1]['model_version']
        )
        
        if comparison['degraded']:
            raise ValueError(
                f"New model worse than previous! "
                f"R² decreased: {comparison['r2_change']:.4f}"
            )
    
    monitor.close()
    return f"Model {new_model['model_version']} validated"

# Add to DAG after training task
validate_model = PythonOperator(
    task_id='validate_new_model',
    python_callable=post_training_monitor,
    dag=dag,
)

train_task >> validate_model
```

---

## Example 8: Performance Trend Analysis

**Scenario**: Analyze model performance trends over time

```python
from scripts.db_utils import ModelEvaluationDB
import matplotlib.pyplot as plt

with ModelEvaluationDB() as db:
    history = db.get_model_history(limit=50)

# Extract data for plotting
versions = [m['model_version'] for m in history]
r2_scores = [m['r2_score'] for m in history]
rmse_scores = [m['rmse_score'] for m in history]

# Create visualization
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6))

# R² trend
ax1.plot(versions, r2_scores, marker='o')
ax1.axhline(y=max(r2_scores) * 0.95, color='r', linestyle='--', label='Alert threshold')
ax1.set_ylabel('R² Score')
ax1.set_title('Model R² Score Trend')
ax1.legend()

# RMSE trend
ax2.plot(versions, rmse_scores, marker='o', color='orange')
ax2.set_ylabel('RMSE')
ax2.set_xlabel('Model Version')
ax2.set_title('Model RMSE Trend')

plt.tight_layout()
plt.savefig('model_performance_trend.png')
print("✓ Saved trend analysis to model_performance_trend.png")
```

---

## Example 9: Alert Integration with Slack

**Scenario**: Send Slack alert when model degrades

```python
import requests
from scripts.db_utils import ModelEvaluationDB

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

with ModelEvaluationDB() as db:
    result = db.check_performance_degradation(threshold_percent=5.0)
    
    if result['degraded']:
        # Prepare Slack message
        message = {
            "text": "🚨 MODEL PERFORMANCE DEGRADATION ALERT",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Model Degradation Detected*\n"
                                f"R² Change: {result['r2_change_percent']}%\n"
                                f"Current: v{result['current_version']}\n"
                                f"Action: Rolled back to v{result['previous_version']}"
                    }
                }
            ]
        }
        
        # Send to Slack
        requests.post(SLACK_WEBHOOK, json=message)
        print("✓ Alert sent to Slack")
```

---

## Example 10: Database Cleanup & Archival

**Scenario**: Keep only recent models, archive old versions

```python
from scripts.db_utils import ModelEvaluationDB
import json
from datetime import datetime, timedelta

with ModelEvaluationDB() as db:
    # Get all models
    all_models = db.get_model_history(limit=1000)
    
    # Keep recent models, archive old ones
    cutoff_date = datetime.now() - timedelta(days=30)
    
    for model in all_models:
        model_date = datetime.fromisoformat(str(model['created_at']))
        
        if model_date < cutoff_date and not model['is_production']:
            # Archive to file
            with open(f"archived_models/v{model['model_version']}.json", 'w') as f:
                json.dump({
                    'version': model['model_version'],
                    'r2_score': model['r2_score'],
                    'rmse_score': model['rmse_score'],
                    'created_at': str(model['created_at'])
                }, f)
            
            print(f"✓ Archived: v{model['model_version']}")
```

---

## Command Cheat Sheet

```bash
# STATUS & INFO
python scripts/monitor_model_performance.py --status
python scripts/monitor_model_performance.py --history
python scripts/monitor_model_performance.py --history 20

# CHECKS & MONITORING
python scripts/monitor_model_performance.py --check
python scripts/monitor_model_performance.py --check --threshold 3.0

# COMPARISON
python scripts/monitor_model_performance.py --compare v1 v2

# ROLLBACK
python scripts/monitor_model_performance.py --rollback-previous
python scripts/monitor_model_performance.py --rollback 20260105_143022

# QUICK REFERENCE (Interactive)
python quick_rollback_ref.py
```

---

**Next Step**: Try Example 1 (Hourly Monitoring) in your environment!

See [MODEL_ROLLBACK_GUIDE.md](MODEL_ROLLBACK_GUIDE.md) for complete reference
