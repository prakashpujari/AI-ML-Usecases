# Degradation Analysis - SQL Query Examples

## Connecting to Database

```bash
# For development (port 5433)
psql -h localhost -p 5433 -U airflow -d airflow

# Or use the environment variable
psql $DATABASE_URL
```

## Basic Queries

### 1. View All Degradation Events

```sql
SELECT 
    id,
    degraded_model_version,
    previous_stable_version,
    severity,
    r2_change_percent,
    rmse_change_percent,
    detected_at,
    rollback_executed
FROM model_degradation_analysis
ORDER BY detected_at DESC;
```

### 2. Count Events by Severity

```sql
SELECT 
    severity,
    COUNT(*) as event_count
FROM model_degradation_analysis
GROUP BY severity
ORDER BY 
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;
```

**Example Output:**
```
severity | event_count
----------+-------------
CRITICAL |           2
HIGH     |           4
MEDIUM   |           5
LOW      |           1
```

### 3. Show Only Critical Events

```sql
SELECT 
    degraded_model_version,
    previous_stable_version,
    r2_change_percent,
    rmse_change_percent,
    rollback_executed,
    detected_at
FROM model_degradation_analysis
WHERE severity = 'CRITICAL'
ORDER BY detected_at DESC;
```

### 4. Events That Triggered Rollback

```sql
SELECT 
    id,
    degraded_model_version,
    previous_stable_version,
    severity,
    detected_at,
    rollback_timestamp
FROM model_degradation_analysis
WHERE rollback_executed = TRUE
ORDER BY detected_at DESC;
```

### 5. Recent Events (Last 24 Hours)

```sql
SELECT 
    degraded_model_version,
    severity,
    r2_change_percent,
    rmse_change_percent,
    detected_at
FROM model_degradation_analysis
WHERE detected_at > NOW() - INTERVAL '24 hours'
ORDER BY detected_at DESC;
```

## Analysis Queries

### 6. Average Degradation by Model Version

```sql
SELECT 
    degraded_model_version,
    COUNT(*) as degradation_count,
    AVG(ABS(r2_change_percent)) as avg_r2_change,
    AVG(ABS(rmse_change_percent)) as avg_rmse_change,
    MAX(ABS(r2_change_percent)) as max_r2_change,
    ROUND(100.0 * SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) / COUNT(*), 2) as rollback_rate_pct
FROM model_degradation_analysis
GROUP BY degraded_model_version
ORDER BY degradation_count DESC;
```

### 7. Worst Performing Models

```sql
SELECT 
    degraded_model_version,
    ROUND(AVG(r2_change_percent)::numeric, 2) as avg_r2_change_pct,
    ROUND(AVG(rmse_change_percent)::numeric, 2) as avg_rmse_change_pct,
    COUNT(*) as total_degradations
FROM model_degradation_analysis
GROUP BY degraded_model_version
ORDER BY ABS(avg_r2_change_pct) DESC
LIMIT 10;
```

### 8. Most Common Degradation Types

```sql
SELECT 
    degradation_type,
    COUNT(*) as event_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM model_degradation_analysis), 2) as percentage
FROM model_degradation_analysis
GROUP BY degradation_type
ORDER BY event_count DESC;
```

### 9. Timeline of Degradation Events

```sql
SELECT 
    DATE_TRUNC('day', detected_at) as degradation_date,
    COUNT(*) as daily_count,
    SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as rollbacks,
    COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_count
FROM model_degradation_analysis
GROUP BY DATE_TRUNC('day', detected_at)
ORDER BY degradation_date DESC;
```

### 10. Rollback Success Rate

```sql
SELECT 
    ROUND(100.0 * SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) / COUNT(*), 2) as rollback_success_rate,
    COUNT(*) as total_degradations,
    SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as rollbacks_executed
FROM model_degradation_analysis;
```

## Performance Analysis

### 11. Most Severe Degradations

```sql
SELECT 
    degraded_model_version,
    previous_stable_version,
    severity,
    r2_change_percent,
    rmse_change_percent,
    accuracy_change_percent,
    detected_at
FROM model_degradation_analysis
WHERE severity IN ('HIGH', 'CRITICAL')
ORDER BY ABS(r2_change_percent) DESC, ABS(rmse_change_percent) DESC
LIMIT 20;
```

### 12. Average R² and RMSE Change by Severity

```sql
SELECT 
    severity,
    COUNT(*) as event_count,
    ROUND(AVG(r2_change_percent)::numeric, 4) as avg_r2_change,
    ROUND(AVG(rmse_change_percent)::numeric, 4) as avg_rmse_change,
    ROUND(AVG(accuracy_change_percent)::numeric, 4) as avg_accuracy_change,
    ROUND(MIN(r2_change_percent)::numeric, 4) as min_r2_change,
    ROUND(MAX(r2_change_percent)::numeric, 4) as max_r2_change
FROM model_degradation_analysis
GROUP BY severity
ORDER BY 
    CASE severity
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'LOW' THEN 4
    END;
```

## Root Cause Analysis

### 13. Events with Specific Root Causes

```sql
SELECT 
    degraded_model_version,
    severity,
    root_cause_hypothesis,
    COUNT(*) as occurrence_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM model_degradation_analysis), 2) as percentage
FROM model_degradation_analysis
WHERE root_cause_hypothesis IS NOT NULL
GROUP BY root_cause_hypothesis, severity, degraded_model_version
ORDER BY occurrence_count DESC;
```

### 14. Recommended Actions Taken

```sql
SELECT 
    recommended_action,
    COUNT(*) as frequency,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM model_degradation_analysis), 2) as percentage
FROM model_degradation_analysis
WHERE recommended_action IS NOT NULL
GROUP BY recommended_action
ORDER BY frequency DESC;
```

### 15. Unresolved High-Severity Issues

```sql
SELECT 
    id,
    degraded_model_version,
    severity,
    detected_at,
    explanation,
    recommended_action,
    rollback_executed
FROM model_degradation_analysis
WHERE severity IN ('HIGH', 'CRITICAL')
  AND rollback_executed = FALSE
ORDER BY detected_at DESC;
```

## Trend Analysis

### 16. Degradation Events This Week

```sql
SELECT 
    EXTRACT(DAY FROM detected_at) as day,
    COUNT(*) as count,
    COUNT(CASE WHEN rollback_executed THEN 1 END) as rollbacks,
    STRING_AGG(DISTINCT severity, ', ' ORDER BY severity) as severities
FROM model_degradation_analysis
WHERE detected_at > NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(DAY FROM detected_at)
ORDER BY day DESC;
```

### 17. Model Degradation Progression

```sql
SELECT 
    degraded_model_version,
    DATE_TRUNC('hour', detected_at) as hour,
    COUNT(*) as hourly_degradations,
    AVG(ABS(r2_change_percent)) as avg_r2_degradation
FROM model_degradation_analysis
WHERE detected_at > NOW() - INTERVAL '7 days'
GROUP BY degraded_model_version, DATE_TRUNC('hour', detected_at)
ORDER BY degraded_model_version, hour DESC;
```

## Comparison Queries

### 18. Compare Model Versions Performance

```sql
WITH degradation_stats AS (
    SELECT 
        degraded_model_version as model_version,
        COUNT(*) as total_events,
        COUNT(CASE WHEN severity = 'CRITICAL' THEN 1 END) as critical_events,
        ROUND(AVG(ABS(r2_change_percent))::numeric, 2) as avg_r2_change
    FROM model_degradation_analysis
    GROUP BY degraded_model_version
)
SELECT 
    model_version,
    total_events,
    critical_events,
    avg_r2_change,
    RANK() OVER (ORDER BY total_events DESC) as reliability_rank
FROM degradation_stats
ORDER BY reliability_rank;
```

### 19. Which Models Rolled Back Successfully

```sql
SELECT 
    degraded_model_version,
    previous_stable_version,
    COUNT(*) as rollback_count,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM model_degradation_analysis WHERE rollback_executed = TRUE), 2) as pct_of_rollbacks
FROM model_degradation_analysis
WHERE rollback_executed = TRUE
GROUP BY degraded_model_version, previous_stable_version
ORDER BY rollback_count DESC;
```

## Real-time Monitoring

### 20. Last 24 Hours Summary

```sql
SELECT 
    'Last 24 Hours' as period,
    COUNT(*) as total_events,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical,
    SUM(CASE WHEN severity = 'HIGH' THEN 1 ELSE 0 END) as high,
    SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as rollbacks,
    ROUND(AVG(ABS(r2_change_percent))::numeric, 2) as avg_r2_change_pct,
    ROUND(AVG(ABS(rmse_change_percent))::numeric, 2) as avg_rmse_change_pct
FROM model_degradation_analysis
WHERE detected_at > NOW() - INTERVAL '24 hours';
```

## Viewing Full Details

### 21. Complete Degradation Event Details

```sql
SELECT 
    id,
    degraded_model_version,
    previous_stable_version,
    degradation_type,
    severity,
    r2_degraded,
    r2_stable,
    r2_change_percent,
    rmse_degraded,
    rmse_stable,
    rmse_change_percent,
    accuracy_degraded,
    accuracy_stable,
    accuracy_change_percent,
    threshold_percent,
    explanation,
    root_cause_hypothesis,
    recommended_action,
    rollback_executed,
    detected_at
FROM model_degradation_analysis
WHERE id = 1;  -- Replace with specific ID
```

## Export Queries

### 22. Export Degradation Events as CSV

```sql
\COPY (
    SELECT 
        detected_at,
        degraded_model_version,
        previous_stable_version,
        severity,
        r2_change_percent,
        rmse_change_percent,
        rollback_executed
    FROM model_degradation_analysis
    ORDER BY detected_at DESC
) TO STDOUT WITH CSV HEADER;
```

### 23. Export Last Week's High-Severity Events

```sql
\COPY (
    SELECT 
        detected_at,
        degraded_model_version,
        severity,
        explanation,
        recommended_action,
        rollback_executed
    FROM model_degradation_analysis
    WHERE severity IN ('HIGH', 'CRITICAL')
      AND detected_at > NOW() - INTERVAL '7 days'
    ORDER BY detected_at DESC
) TO '/tmp/high_severity_events.csv' WITH CSV HEADER;
```

## Performance Tips

1. **Use indexes for common queries:**
   - `WHERE degraded_model_version = 'v...'`
   - `WHERE severity = 'CRITICAL'`
   - `WHERE detected_at > ...`
   - `WHERE rollback_executed = TRUE`

2. **Aggregate with date_trunc for timeseries:**
   ```sql
   DATE_TRUNC('hour', detected_at)  -- hourly
   DATE_TRUNC('day', detected_at)   -- daily
   ```

3. **Use EXPLAIN to check query plans:**
   ```sql
   EXPLAIN ANALYZE SELECT ... ;
   ```

4. **Regular maintenance:**
   ```sql
   VACUUM ANALYZE model_degradation_analysis;
   ```

## Useful Views

### Create a Summary View

```sql
CREATE VIEW degradation_summary AS
SELECT 
    severity,
    COUNT(*) as event_count,
    ROUND(AVG(ABS(r2_change_percent))::numeric, 2) as avg_r2_change,
    ROUND(AVG(ABS(rmse_change_percent))::numeric, 2) as avg_rmse_change,
    SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as successful_rollbacks,
    MAX(detected_at) as latest_event
FROM model_degradation_analysis
GROUP BY severity;
```

Query it:
```sql
SELECT * FROM degradation_summary;
```
