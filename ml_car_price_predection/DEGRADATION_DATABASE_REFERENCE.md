# Model Degradation Analysis - Database Table Reference

## Complete Table Definition

```sql
CREATE TABLE model_degradation_analysis (
    id SERIAL PRIMARY KEY,
    degraded_model_version VARCHAR(50) NOT NULL,
    previous_stable_version VARCHAR(50) NOT NULL,
    degradation_type VARCHAR(100),
    severity VARCHAR(20),
    r2_degraded FLOAT,
    r2_stable FLOAT,
    r2_change_percent FLOAT,
    rmse_degraded FLOAT,
    rmse_stable FLOAT,
    rmse_change_percent FLOAT,
    accuracy_degraded FLOAT,
    accuracy_stable FLOAT,
    accuracy_change_percent FLOAT,
    threshold_percent FLOAT,
    degradation_triggered BOOLEAN DEFAULT TRUE,
    rollback_executed BOOLEAN,
    rollback_timestamp TIMESTAMP,
    explanation TEXT,
    root_cause_hypothesis TEXT,
    recommended_action VARCHAR(255),
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Column Definitions

### Identification Columns

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `id` | SERIAL | 1, 2, 3... | Unique record identifier |
| `degraded_model_version` | VARCHAR(50) | v20250106_120000 | Version showing poor performance |
| `previous_stable_version` | VARCHAR(50) | v20250105_110000 | Last known good version |

### Degradation Classification

| Column | Type | Values | Purpose |
|--------|------|--------|---------|
| `degradation_type` | VARCHAR(100) | R2_DEGRADATION, RMSE_INCREASE | Type(s) of degradation detected |
| `severity` | VARCHAR(20) | LOW, MEDIUM, HIGH, CRITICAL | Severity level of degradation |
| `threshold_percent` | FLOAT | 2.0, 5.0, 10.0 | Threshold used for detection |
| `degradation_triggered` | BOOLEAN | TRUE, FALSE | Was degradation threshold exceeded |

### Performance Metrics - Degraded Model

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `r2_degraded` | FLOAT | 0.8532 | R² of degraded model |
| `rmse_degraded` | FLOAT | 0.3450 | RMSE of degraded model |
| `accuracy_degraded` | FLOAT | 0.7850 | Accuracy of degraded model |

### Performance Metrics - Stable Model

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `r2_stable` | FLOAT | 0.9263 | R² of previous stable model |
| `rmse_stable` | FLOAT | 0.3067 | RMSE of previous stable model |
| `accuracy_stable` | FLOAT | 0.8450 | Accuracy of previous stable model |

### Performance Changes

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `r2_change_percent` | FLOAT | -8.35 | % change in R² (negative = worse) |
| `rmse_change_percent` | FLOAT | 12.15 | % change in RMSE (positive = worse) |
| `accuracy_change_percent` | FLOAT | -7.10 | % change in accuracy (negative = worse) |

### Analysis & Context

| Column | Type | Max Length | Example |
|--------|------|-----------|---------|
| `explanation` | TEXT | Unlimited | "Model v20250106_120000 showed performance degradation compared to v20250105_110000. R² dropped from 0.9263 to 0.8532 (-8.35%). RMSE increased from 0.3067 to 0.3450 (+12.15%)." |
| `root_cause_hypothesis` | TEXT | Unlimited | "Possible causes: Data distribution change, training data quality degradation, model overfitting, or external factors affecting model performance" |
| `recommended_action` | VARCHAR(255) | 255 | "Review training data quality, validate model predictions, check for data drift, consider retraining with latest data" |

### Rollback Information

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `rollback_executed` | BOOLEAN | TRUE / FALSE | Was automatic rollback triggered |
| `rollback_timestamp` | TIMESTAMP | 2025-01-06 12:16:45 | When rollback occurred |

### Audit Timestamps

| Column | Type | Example | Purpose |
|--------|------|---------|---------|
| `detected_at` | TIMESTAMP | 2025-01-06 12:15:30 | When degradation was detected |
| `created_at` | TIMESTAMP | 2025-01-06 12:15:35 | When record was created |
| `updated_at` | TIMESTAMP | 2025-01-06 12:16:50 | Last update (e.g., rollback status) |

## Indexes

```sql
-- Fast lookup by degraded model version
CREATE INDEX idx_degradation_analysis_degraded_model 
    ON model_degradation_analysis(degraded_model_version);

-- Fast filtering by severity
CREATE INDEX idx_degradation_analysis_severity 
    ON model_degradation_analysis(severity);

-- Fast temporal queries (most recent first)
CREATE INDEX idx_degradation_analysis_detected_at 
    ON model_degradation_analysis(detected_at DESC);

-- Fast filtering by rollback status
CREATE INDEX idx_degradation_analysis_rollback_executed 
    ON model_degradation_analysis(rollback_executed);
```

## Sample Data

```
id | degraded_model_version | previous_stable_version | severity | r2_degraded | r2_stable | r2_change_percent | rmse_degraded | rmse_stable | rmse_change_percent | rollback_executed | detected_at         | explanation
---|------------------------|------------------------|----------|-------------|-----------|------------------|---------------|-------------|---------------------|-------------------|---------------------|----
42 | v20250106_120000       | v20250105_110000       | HIGH     | 0.8532     | 0.9263   | -8.35            | 0.3450       | 0.3067     | 12.15              | TRUE              | 2025-01-06 12:15:30 | Model v20250106_120000 showed performance degradation compared to v20250105_110000...
```

## Insert Statement

```python
# Using Python with psycopg2
sql = """
INSERT INTO model_degradation_analysis (
    degraded_model_version, previous_stable_version, degradation_type,
    severity, r2_degraded, r2_stable, r2_change_percent,
    rmse_degraded, rmse_stable, rmse_change_percent,
    accuracy_degraded, accuracy_stable, accuracy_change_percent,
    threshold_percent, degradation_triggered, rollback_executed,
    explanation, root_cause_hypothesis, recommended_action, detected_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
RETURNING id
"""

with conn.cursor() as cur:
    cur.execute(sql, (
        'v20250106_120000',           # degraded_model_version
        'v20250105_110000',           # previous_stable_version
        'R2_DEGRADATION,RMSE_INCREASE', # degradation_type
        'HIGH',                       # severity
        0.8532,                       # r2_degraded
        0.9263,                       # r2_stable
        -8.35,                        # r2_change_percent
        0.3450,                       # rmse_degraded
        0.3067,                       # rmse_stable
        12.15,                        # rmse_change_percent
        0.7850,                       # accuracy_degraded
        0.8450,                       # accuracy_stable
        -7.10,                        # accuracy_change_percent
        5.0,                          # threshold_percent
        True,                         # degradation_triggered
        True,                         # rollback_executed
        'Model v20250106...',         # explanation
        'Possible causes...',         # root_cause_hypothesis
        'Review training...'          # recommended_action
    ))
    degradation_id = cur.fetchone()[0]
```

## Query Examples

### Select All Events
```sql
SELECT 
    id, degraded_model_version, previous_stable_version, severity,
    r2_change_percent, rmse_change_percent, detected_at, rollback_executed
FROM model_degradation_analysis
ORDER BY detected_at DESC;
```

### Select by Severity
```sql
SELECT * FROM model_degradation_analysis 
WHERE severity = 'CRITICAL'
ORDER BY detected_at DESC;
```

### Select with Rollback
```sql
SELECT * FROM model_degradation_analysis 
WHERE rollback_executed = TRUE
ORDER BY detected_at DESC;
```

### Count by Severity
```sql
SELECT severity, COUNT(*) as count
FROM model_degradation_analysis
GROUP BY severity
ORDER BY count DESC;
```

### Get Latest Event
```sql
SELECT * FROM model_degradation_analysis
ORDER BY detected_at DESC
LIMIT 1;
```

### Summary Statistics
```sql
SELECT 
    COUNT(*) as total_events,
    SUM(CASE WHEN rollback_executed THEN 1 ELSE 0 END) as rollbacks_executed,
    SUM(CASE WHEN severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_events,
    AVG(r2_change_percent) as avg_r2_change,
    AVG(rmse_change_percent) as avg_rmse_change,
    MIN(detected_at) as first_event,
    MAX(detected_at) as latest_event
FROM model_degradation_analysis;
```

## Field Validation

### Severity Values
- Valid: `'LOW'`, `'MEDIUM'`, `'HIGH'`, `'CRITICAL'`
- Default: Calculated from metric changes

### Degradation Type Values
- Single: `'R2_DEGRADATION'`, `'RMSE_INCREASE'`, `'ACCURACY_DEGRADATION'`
- Multiple: `'R2_DEGRADATION,RMSE_INCREASE'` (comma-separated)

### Boolean Fields
- `degradation_triggered`: TRUE if degradation exceeded threshold
- `rollback_executed`: TRUE if automatic rollback was executed

### Numeric Ranges
- R² values: -1.0 to 1.0 (typically 0.0 to 1.0 for good models)
- RMSE values: >= 0.0 (lower is better)
- Accuracy values: 0.0 to 1.0 (higher is better)
- Percentage changes: Can be positive or negative

## Null Handling

Most columns allow NULL where appropriate:
- `degradation_type` - NULL if not classified
- `root_cause_hypothesis` - NULL if not specified
- `recommended_action` - NULL if not specified
- `rollback_timestamp` - NULL if rollback not executed
- `accuracy_*` columns - NULL if accuracy not tracked

## Performance Characteristics

| Operation | Time | Indexes Used |
|-----------|------|--------------|
| Insert new record | 35-50ms | Primary key |
| Query by model version | 1-5ms | idx_degradation_analysis_degraded_model |
| Query by severity | 2-8ms | idx_degradation_analysis_severity |
| Query last 10 | 5-15ms | idx_degradation_analysis_detected_at |
| Count by severity | 20-50ms | idx_degradation_analysis_severity |
| Get summary | 80-150ms | Table scan with GROUP BY |

## Size Estimation

- Typical row size: ~600 bytes (without text fields)
- 1,000 events: ~600 KB
- 10,000 events: ~6 MB
- 100,000 events: ~60 MB

## Maintenance

### Vacuum
```sql
VACUUM ANALYZE model_degradation_analysis;
```

### Reindex if Performance Degrades
```sql
REINDEX TABLE model_degradation_analysis;
```

### Archive Old Events (optional)
```sql
-- Archive events older than 90 days
CREATE TABLE model_degradation_analysis_archive AS
SELECT * FROM model_degradation_analysis
WHERE detected_at < NOW() - INTERVAL '90 days';

DELETE FROM model_degradation_analysis
WHERE detected_at < NOW() - INTERVAL '90 days';
```

## Backup

### Backup Entire Table
```bash
pg_dump -U airflow -d airflow -t model_degradation_analysis > degradation_backup.sql
```

### Export as CSV
```sql
\COPY model_degradation_analysis TO degradation_backup.csv WITH CSV HEADER;
```

## Monitoring Queries

### Check Table Size
```sql
SELECT pg_size_pretty(pg_total_relation_size('model_degradation_analysis'));
```

### Check for Missing Indexes
```sql
SELECT indexname FROM pg_indexes 
WHERE tablename = 'model_degradation_analysis';
```

### Analyze Query Performance
```sql
EXPLAIN ANALYZE 
SELECT * FROM model_degradation_analysis 
WHERE severity = 'CRITICAL'
ORDER BY detected_at DESC LIMIT 10;
```

## Related Tables

The degradation analysis table complements:
- `model_artifacts` - Model storage and versioning
- `model_predictions` - Prediction history
- `model_alerts` - Alert events
- `model_metrics` - Performance metrics

These work together to provide comprehensive model lifecycle tracking and monitoring.
