# Airflow Deployment Guide - Automatic Retraining 🚀

## Quick Start

### Prerequisites Verified ✅
- ✅ `airflow_settings.yaml` configured
- ✅ `airflow/dags/automatic_retraining_dag.py` ready
- ✅ All dependencies installed
- ✅ Astro CLI available

---

## Deployment Steps

### Step 1: Start Airflow

```powershell
astro dev start
```

**Wait for ~2-3 minutes** until you see:
```
✔ Project is running
✔ Webserver: http://localhost:8080
✔ Postgres: localhost:5432
```

### Step 2: Access Airflow UI

Open your browser and navigate to:
```
http://localhost:8080
```

**Credentials:**
- Username: `admin`
- Password: `admin`

### Step 3: Verify DAG Deployment

1. In Airflow UI, click **DAGs** tab
2. Look for: **`automatic_model_retraining`**
3. Verify status is **ENABLED** (should be green)

**Expected Dashboard:**
```
DAGs
┌─────────────────────────────────────────┐
│ DAG ID                  │ Status        │
├─────────────────────────────────────────┤
│ automatic_model_retraining │ ✅ ENABLED   │
│ train_model_dag            │ ✅ ENABLED   │
│ (other DAGs)               │ ...         │
└─────────────────────────────────────────┘
```

### Step 4: Trigger Manual Run (Optional)

#### Option A: Via UI
1. Click on **`automatic_model_retraining`** DAG name
2. Click **Play button (▶️)** to trigger
3. View execution progress in **Graph View**

#### Option B: Via Command Line
```powershell
astro dev run dags trigger automatic_model_retraining
```

---

## DAG Details

### Schedule
```
Every 6 hours: 0 */6 * * *
Runs at: 00:00, 06:00, 12:00, 18:00 UTC
```

### Tasks

```
analyze_retraining_need
        ↓
check_retraining_decision
        ↓
execute_retraining
        ↓
log_retraining_completion
```

| Task | Purpose | Duration |
|------|---------|----------|
| `analyze_retraining_need` | Check for drift using 3 methods | ~1-2 min |
| `check_retraining_decision` | Verify trigger decision | ~30 sec |
| `execute_retraining` | Run training if triggered | ~5-30 min |
| `log_retraining_completion` | Log results to database | ~1 min |

### Configuration

**File:** `airflow/dags/automatic_retraining_dag.py`

**Key Settings:**
```python
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2026, 1, 1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'automatic_model_retraining',
    default_args=default_args,
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    description='Automatic model retraining on drift detection'
)
```

---

## Monitoring

### View Logs

In Airflow UI:
1. Click on DAG → Select a run
2. Click on task → View logs
3. Search for errors or status messages

### Check Retraining Events

In database (after first run):
```sql
SELECT 
    triggered_at, 
    trigger_type, 
    severity, 
    execution_successful
FROM model_retraining_events
ORDER BY triggered_at DESC;
```

### Verify Task Execution

```powershell
# Check recent runs
astro dev run dags list-runs automatic_model_retraining

# View scheduler logs
astro dev logs --scheduler
```

---

## Expected Behavior

### First Run
1. DAG triggers (manually or by schedule)
2. Task 1: Analyzes for drift
3. Task 2: Makes retraining decision
4. Task 3: Executes if needed
5. Task 4: Logs results

### Success Output
```
Task 1: ✅ COMPLETED - No drift detected
Task 2: ✅ COMPLETED - No retraining needed
Task 3: ⏭️ SKIPPED - Condition not met
Task 4: ✅ COMPLETED - Event logged
```

### Retraining Triggered
```
Task 1: ✅ COMPLETED - Data drift detected (p<0.05)
Task 2: ✅ COMPLETED - Retraining triggered (HIGH severity)
Task 3: ✅ COMPLETED - Training finished, R² improved 2%
Task 4: ✅ COMPLETED - Event logged to database
```

---

## Troubleshooting

### DAG Not Appearing

**Problem:** DAG doesn't show in Airflow UI

**Solutions:**
```powershell
# Restart Airflow
astro dev stop
astro dev start

# Validate DAG syntax
astro dev run dags list

# Check DAG file location
ls airflow/dags/automatic_retraining_dag.py
```

### Connection Refused

**Problem:** Can't connect to Airflow at localhost:8080

**Solutions:**
```powershell
# Check if Airflow is running
astro dev ps

# If not running, start it
astro dev start

# Wait for health check to pass (~2-3 min)
```

### Task Failures

**Problem:** Tasks failing in DAG

**Solutions:**
1. Click on failed task → View logs
2. Check for missing dependencies
3. Verify database connection
4. Ensure data files exist

**Common Issues:**
```
- Missing data files: Check data/trainset/train.csv exists
- Database connection: Verify PostgreSQL is running (port 5433)
- Python packages: pip install -r requirements.txt
```

---

## Stopping Airflow

```powershell
astro dev stop
```

---

## Advanced Configuration

### Change Schedule

Edit `airflow/dags/automatic_retraining_dag.py`:
```python
schedule_interval='0 */12 * * *'  # Every 12 hours
# or
schedule_interval='0 2 * * *'     # Daily at 2 AM
```

### Adjust Retraining Thresholds

Edit `scripts/automatic_retraining.py`:
```python
orchestrator = AutomaticRetrainingOrchestrator(
    data_drift_threshold=0.03,      # More sensitive
    performance_threshold=0.03,     # Stricter checks
    min_samples_for_retraining=200  # Require more data
)
```

### Enable Email Notifications

```python
dag = DAG(
    'automatic_model_retraining',
    default_args={
        'email': ['your-email@example.com'],
        'email_on_failure': True,
        'email_on_retry': False,
    }
)
```

---

## Dashboard Navigation

### From Airflow UI

**View DAG Status:**
- Home → DAGs → automatic_model_retraining

**View Execution:**
- Click DAG → Graph View or Calendar View

**View Task Details:**
- Click task → Logs

**View Execution History:**
- DAG → Runs tab → Select specific run

---

## Database Monitoring

### Recent Events
```sql
SELECT TOP 10
    triggered_at,
    trigger_type,
    severity,
    improvement_r2_percent,
    execution_successful
FROM model_retraining_events
ORDER BY triggered_at DESC;
```

### Success Rate
```sql
SELECT 
    COUNT(*) as total_runs,
    SUM(CASE WHEN execution_successful THEN 1 ELSE 0 END) as successful,
    ROUND(100.0 * SUM(CASE WHEN execution_successful THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM model_retraining_events;
```

### Improvements Tracked
```sql
SELECT 
    AVG(improvement_r2_percent) as avg_r2_improvement,
    AVG(improvement_rmse_percent) as avg_rmse_improvement,
    MAX(improvement_r2_percent) as max_improvement
FROM model_retraining_events
WHERE execution_successful = TRUE;
```

---

## Next Steps

1. ✅ Deploy to Airflow (you are here)
2. Monitor first run (30 minutes)
3. Verify retraining events in database
4. Adjust thresholds if needed
5. Set up monitoring alerts
6. Deploy to production

---

## Quick Commands

```powershell
# Start Airflow
astro dev start

# Access Airflow UI
# http://localhost:8080

# Trigger DAG manually
astro dev run dags trigger automatic_model_retraining

# View logs
astro dev logs --scheduler

# Stop Airflow
astro dev stop

# List all DAGs
astro dev run dags list

# Check specific DAG
astro dev run dags list-runs automatic_model_retraining
```

---

**Status**: ✅ Ready to Deploy  
**Version**: 2.0  
**Last Updated**: January 6, 2026

