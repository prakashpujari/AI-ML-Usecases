# 📊 Visual Guide - Screenshots & Workflows

## Dashboard Screenshots Description

### 1. Streamlit Main Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  🚗 Car Price Prediction Dashboard                         │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  📊 FEATURE SELECTION                                      │
│                                                             │
│  Age (years):                                              │
│  Min: 0 ─────────●────────── Max: 20                      │
│  Your Selection: 5 years                                   │
│                                                             │
│  Mileage (km):                                             │
│  Min: 0 ──────────────●──────── Max: 200,000             │
│  Your Selection: 75,000 km                                │
│                                                             │
│  Engine Size (L):                                          │
│  Min: 1.0 ────●───── Max: 5.0                            │
│  Your Selection: 2.0 L                                     │
│                                                             │
│  Brand: [ Toyota ▼ ]                                       │
│  Fuel Type: [ Petrol ▼ ]                                  │
│  Transmission: [ Automatic ▼ ]                            │
│  Color: [ White ▼ ]                                       │
│                                                             │
│  [🔮 Predict Price] Button                                 │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  💰 PREDICTION RESULT                                      │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │                                                      │ │
│  │         Estimated Price: 💵 $18,500.50             │ │
│  │                                                      │ │
│  │         Confidence Range:                           │ │
│  │         Lower Bound: $17,300.25                     │ │
│  │         Upper Bound: $19,700.75                     │ │
│  │                                                      │ │
│  │         Confidence Level:                           │ │
│  │         ████████░░░░░░░░░░░░  85%                   │ │
│  │                                                      │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  🔍 MODEL EXPLANATION (SHAP)                              │
│                                                             │
│  How each feature affects the price:                      │
│                                                             │
│  Mileage:      ━━━━━━━━━━━ (Decreases price by $3,200)   │
│  Age:          ━━━━━━━ (Decreases price by $2,100)       │
│  Engine Size:  ━━ (Increases price by $1,500)            │
│  Brand:        ━ (Increases price by $800)               │
│  Color:        ░ (Minimal impact)                         │
│                                                             │
│  (Red = increases price, Blue = decreases price)         │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  📈 MODEL METRICS & PERFORMANCE                           │
│                                                             │
│  R² Score:     ████████░  0.876  (87.6% variance explained)
│  RMSE:         $4,321.45  (Average prediction error)     │
│  MAE:          $3,456.78  (Mean absolute error)          │
│  Training Samples:  5,000                                │
│  Last Updated:      2026-01-05 21:35:12 UTC             │
│                                                             │
│  Model Status:  ✅ EXCELLENT                              │
│  (R² > 0.85, ready for production)                       │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  📊 Training History                                       │
│                                                             │
│  Model Version   │ Date            │ R²     │ Status      │
│  ─────────────────────────────────────────────────────── │
│  v1.0            │ 2026-01-05 21:30│ 0.876  │ Active ✓   │
│  v0.9            │ 2026-01-05 20:15│ 0.891  │ Staged     │
│  v0.8            │ 2026-01-04 19:45│ 0.843  │ Archive    │
│                                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. FastAPI Documentation (Swagger UI)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  FastAPI - Interactive API Docs                           │
│  http://localhost:8000/docs                               │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  Available Endpoints:                                      │
│                                                             │
│  GET /health                                              │
│  └─ Check if API is running                               │
│                                                             │
│  GET /info                                                │
│  └─ Get model information and available features          │
│                                                             │
│  POST /predict                                            │
│  └─ Make price predictions                                │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  POST /predict                                            │
│                                                             │
│  [▼ Try it out]  [Schema]  [Example Value]               │
│                                                             │
│  Request Body (application/json):                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ {                                                    │ │
│  │   "age": 5,                                          │ │
│  │   "mileage": 75000,                                  │ │
│  │   "engine_size": 2.0,                                │ │
│  │   "brand": "Toyota",                                 │ │
│  │   "fuel_type": "Petrol",                             │ │
│  │   "transmission": "Automatic",                       │ │
│  │   "color": "White",                                  │ │
│  │   "accident_history": false,                         │ │
│  │   "service_history": true,                           │ │
│  │   "ownership_history": 1,                            │ │
│  │   "current_price": 15000                             │ │
│  │ }                                                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  [Execute] Button                                          │
│                                                             │
│  ─────────────────────────────────────────────────────── │
│  Response 200 (application/json):                         │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ {                                                    │ │
│  │   "predicted_price": 18500.50,                       │ │
│  │   "confidence_interval": {                           │ │
│  │     "lower": 17300.25,                               │ │
│  │     "upper": 19700.75                                │ │
│  │   },                                                 │ │
│  │   "confidence_level": 0.85,                          │ │
│  │   "feature_importance": {                            │ │
│  │     "mileage": 0.32,                                 │ │
│  │     "age": 0.28,                                     │ │
│  │     "engine_size": 0.18,                             │ │
│  │     "brand": 0.15,                                   │ │
│  │     "fuel_type": 0.07                                │ │
│  │   },                                                 │ │
│  │   "model_version": "1.0",                            │ │
│  │   "timestamp": "2026-01-05T21:35:12Z"               │ │
│  │ }                                                    │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
│  Response Headers:                                         │
│  content-type: application/json                           │
│  server: uvicorn                                          │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  curl Request:                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ curl -X POST "http://localhost:8000/predict" \       │ │
│  │   -H "Content-Type: application/json" \              │ │
│  │   -d '{"age":5, "mileage":75000, ...}'               │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 3. MLflow Experiment Tracking UI

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  MLflow Experiments Tracking                              │
│  http://localhost:5000                                    │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  Experiments:  [car_price_prediction ▼]                   │
│                                                             │
│  Compare Runs  │  Chart View  │  Runs                      │
│                                                             │
│  ─────────────────────────────────────────────────────── │
│                                                             │
│  Runs List:                                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐ │
│  │ Date            │ Status │ Metrics             │ Tags  │
│  ├─────────────────────────────────────────────────────┤ │
│  │ 2026-01-05 21:30│ ✓      │ R²: 0.876           │ v1.0  │
│  │ UTC             │ FINISH │ RMSE: 4321.45       │ prod  │
│  │                 │        │ MAE: 3456.78        │       │
│  │                 │        │                     │       │
│  │ 2026-01-05 20:15│ ✓      │ R²: 0.891           │ v0.9  │
│  │ UTC             │ FINISH │ RMSE: 3987.23       │ stage │
│  │                 │        │ MAE: 3123.45        │       │
│  │                 │        │                     │       │
│  │ 2026-01-04 19:45│ ✓      │ R²: 0.843           │ v0.8  │
│  │ UTC             │ FINISH │ RMSE: 4567.89       │ arch  │
│  │                 │        │ MAE: 3789.01        │       │
│  │                                                   │       │
│  └─────────────────────────────────────────────────────┘ │
│                                                             │
│  Click run to view details:                                │
│                                                             │
│  Run: abc123def456                                        │
│  Status: FINISHED                                          │
│  Start Time: 2026-01-05 21:30:12                         │
│  End Time: 2026-01-05 21:32:45                           │
│  Duration: 2m 33s                                         │
│                                                             │
│  Parameters:                                               │
│  ├─ model_type: Random Forest                              │
│  ├─ n_estimators: 100                                      │
│  ├─ max_depth: 15                                          │
│  └─ random_state: 42                                       │
│                                                             │
│  Metrics:                                                  │
│  ├─ r2_score: 0.876                                        │
│  ├─ rmse: 4321.45                                          │
│  ├─ mae: 3456.78                                           │
│  └─ training_time_seconds: 153.45                          │
│                                                             │
│  Artifacts:                                                │
│  ├─ model.pkl (2.3 MB)                                     │
│  ├─ feature_importance.png                                 │
│  └─ metrics.json                                           │
│                                                             │
│  Tags:                                                     │
│  ├─ version: 1.0                                           │
│  ├─ environment: production                                │
│  ├─ stage: active                                          │
│  └─ commit: abc123                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4. Airflow DAG Execution

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Airflow DAG: train_model_dag                              │
│  http://localhost:8080                                    │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  DAG Graph View:                                           │
│                                                             │
│              ┌─────────────────┐                           │
│              │ validate_data   │                           │
│              │   [RUNNING]     │  ▌                        │
│              └────────┬────────┘                           │
│                       │                                    │
│              ┌────────▼────────┐                           │
│              │  train_model    │                           │
│              │  [RUNNING]      │  ▌                        │
│              └────────┬────────┘                           │
│                       │                                    │
│              ┌────────▼────────┐                           │
│              │ evaluate_model  │                           │
│              │  [QUEUED]       │  ░                        │
│              └────────┬────────┘                           │
│                       │                                    │
│              ┌────────▼────────┐                           │
│              │ register_model  │                           │
│              │  [QUEUED]       │  ░                        │
│              └────────┬────────┘                           │
│                       │                                    │
│              ┌────────▼────────┐                           │
│              │monitor_perform  │                           │
│              │  [QUEUED]       │  ░                        │
│              └─────────────────┘                           │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  Execution Details:                                        │
│                                                             │
│  DAG Run: 2026-01-05T21:30:00+00:00                       │
│  Status: RUNNING                                           │
│  Progress: 2/5 tasks completed (40%)                      │
│  Start Time: 2026-01-05 21:30:00                         │
│  Expected End: 2026-01-05 21:40:00                       │
│                                                             │
│  Task Execution Times:                                     │
│  ├─ validate_data: 5s ✓                                    │
│  ├─ train_model: 3m 24s (running...)                       │
│  ├─ evaluate_model: 2m (queued)                            │
│  ├─ register_model: 30s (queued)                           │
│  └─ monitor_perform: 20s (queued)                          │
│                                                             │
│  ═══════════════════════════════════════════════════════  │
│                                                             │
│  Task Logs (train_model):                                 │
│                                                             │
│  [2026-01-05 21:35:24] INFO - Starting training...        │
│  [2026-01-05 21:35:25] INFO - Features: 11               │
│  [2026-01-05 21:35:26] INFO - Train samples: 4000        │
│  [2026-01-05 21:35:27] INFO - Test samples: 1000         │
│  [2026-01-05 21:37:30] INFO - Training complete          │
│  [2026-01-05 21:37:31] INFO - R² Score: 0.876           │
│  [2026-01-05 21:37:32] INFO - Model saved                │
│                                                             │
│  [↓ More logs...]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Workflow Examples

### Workflow 1: Making Your First Prediction (5 minutes)

**Step 1: Open Dashboard**
```
1. Open browser
2. Go to: http://localhost:8501
3. You see the Streamlit dashboard
```

**Step 2: Select Car Features**
```
1. Age slider: Drag to 5 years
2. Mileage slider: Drag to 75,000 km
3. Engine size: Drag to 2.0 L
4. Brand dropdown: Select "Toyota"
5. Leave other options as default
```

**Step 3: Get Prediction**
```
1. Click "🔮 Predict Price" button
2. Wait 2-3 seconds
3. See result: $18,500 ± $1,200
```

**Step 4: Understand Result**
```
1. Scroll down to "MODEL EXPLANATION"
2. See feature importance:
   - Red bars = increases price
   - Blue bars = decreases price
3. Red "Mileage" bar (longest) = most important factor
```

### Workflow 2: Training a New Model (10 minutes)

**Step 1: Generate Data**
```powershell
python train.py --n-samples 10000
```

**Step 2: Monitor Training**
```
1. Check terminal output
2. See "Model training completed"
3. See metrics: R² = 0.876, RMSE = 4321.45
```

**Step 3: Verify in MLflow**
```
1. Open: http://localhost:5000
2. See new run appeared
3. Compare metrics with previous runs
```

**Step 4: Test New Model**
```
1. Go to: http://localhost:8501
2. Make predictions (now uses new model)
3. Metrics should update in dashboard
```

### Workflow 3: Scheduling Daily Training (15 minutes)

**Step 1: Start Airflow**
```powershell
astro dev start
```

**Step 2: Access Airflow UI**
```
1. Open: http://localhost:8080
2. Login: admin / admin
3. You see the Airflow dashboard
```

**Step 3: Find Your DAG**
```
1. Click "DAGs" in top menu
2. Search for "train_model_dag"
3. Click on the DAG name
```

**Step 4: Trigger Training**
```
1. Click the Play (▶️) button
2. DAG starts executing
3. Watch tasks complete in order
```

**Step 5: Monitor Execution**
```
1. Click on DAG again
2. See Graph View with status
3. Each task shows progress
4. View logs by clicking task
```

---

## Common UI Elements Explained

### Streamlit Sliders

```
Age (years):
[0] ─────●──── [20]
         ↑
    Current: 5 years

How to use:
1. Click and drag the blue dot
2. Move left = decrease value
3. Move right = increase value
4. Number updates below slider
```

### Status Indicators

```
✓  FINISHED  = Task completed successfully
✗  FAILED    = Task had an error
▌  RUNNING   = Task is currently executing
░  QUEUED    = Task waiting to run
●  PENDING   = Task dependency not met
```

### Progress Bars

```
Confidence:
████████░░░░░░░░░░░░  85%
└─ 8 filled blocks = 80%
└─ 1 partial block = 5%
└─ Total = 85%
```

---

## Performance Expectations

### Model Training Duration

```
Data Size      │ Training Time │ Hardware
─────────────────────────────────────────
5,000 samples  │ ~1-2 minutes  │ 4GB RAM
10,000 samples │ ~3-5 minutes  │ 4GB RAM
50,000 samples │ ~10-15 min    │ 8GB RAM
```

### API Response Time

```
Endpoint     │ Response Time
─────────────────────────────
/health      │ < 10ms
/info        │ < 20ms
/predict     │ 50-200ms
```

### UI Load Times

```
Page              │ Load Time (Docker)
──────────────────────────────────────
Streamlit Home    │ 1-2 seconds
API Docs          │ 1-2 seconds
MLflow UI         │ 2-3 seconds
Airflow DAG       │ 2-3 seconds
```

---

## Keyboard Shortcuts

### Browser

```
Ctrl+R / Cmd+R     = Refresh page
Ctrl+L / Cmd+L     = Focus address bar
F12                = Open developer tools
Ctrl+Shift+Delete  = Clear cache
```

### Terminal

```
Ctrl+C             = Stop running command
Ctrl+A             = Select all
Ctrl+V             = Paste
Ctrl+Z (then Y)    = Undo (Git)
```

---

## Visual Summary

```
START
  │
  ├─► Open http://localhost:8501
  │   (Streamlit Dashboard)
  │
  ├─► Adjust car features
  │   (sliders & dropdowns)
  │
  ├─► Click "Predict"
  │   (Get price prediction)
  │
  ├─► View explanation
  │   (SHAP feature importance)
  │
  ├─► Check metrics
  │   (R² Score, RMSE)
  │
  ├─► If satisfied:
  │   Go to MLflow (5000)
  │
  └─► If training needed:
      Go to Terminal
      Run: python train.py
      
      Then schedule in Airflow
```

---

**Visual Guide Complete! 📊**

For more details, refer to the [main README.md](README.md)
