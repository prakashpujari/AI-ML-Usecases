# 🔌 API Examples & Code Snippets

Complete working examples for interacting with the Car Price Prediction API.

## Table of Contents

1. [Python Examples](#python-examples)
2. [cURL Examples](#curl-examples)
3. [JavaScript/Node.js Examples](#javascriptnode-examples)
4. [Batch Processing](#batch-processing)
5. [Error Handling](#error-handling)

---

## Python Examples

### Basic Setup

```python
import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

def make_request(endpoint, method="GET", data=None):
    """Helper function to make API requests"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, json=data, headers=HEADERS)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        return None
```

### Example 1: Health Check

```python
# Check if API is running
response = make_request("/health")

print("Health Check Response:")
print(json.dumps(response, indent=2))

# Expected Output:
# {
#   "status": "healthy",
#   "timestamp": "2026-01-05T21:35:00Z",
#   "version": "1.0.0"
# }
```

### Example 2: Get Model Information

```python
# Get information about the model
response = make_request("/info")

print("Model Information:")
print(f"Model Name: {response['model_name']}")
print(f"Model Version: {response['model_version']}")
print(f"Input Features: {response['input_features']}")
print(f"Accuracy Metrics:")
print(f"  - R² Score: {response['accuracy_metrics']['r2_score']}")
print(f"  - RMSE: ${response['accuracy_metrics']['rmse']:.2f}")
print(f"  - MAE: ${response['accuracy_metrics']['mae']:.2f}")

# Expected Output:
# Model Name: car_price_predictor
# Model Version: 1.0
# Input Features: ['age', 'mileage', 'engine_size', 'brand', ...]
# Accuracy Metrics:
#   - R² Score: 0.876
#   - RMSE: $4321.45
#   - MAE: $3456.78
```

### Example 3: Single Prediction

```python
# Define car features
car_data = {
    "age": 5,
    "mileage": 75000,
    "engine_size": 2.0,
    "brand": "Toyota",
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "color": "White",
    "accident_history": False,
    "service_history": True,
    "ownership_history": 1,
    "current_price": 15000
}

# Make prediction
response = make_request("/predict", method="POST", data=car_data)

# Extract results
price = response['predicted_price']
confidence = response['confidence_level']
lower_bound = response['confidence_interval']['lower']
upper_bound = response['confidence_interval']['upper']

print(f"Predicted Price: ${price:,.2f}")
print(f"Confidence Level: {confidence*100:.1f}%")
print(f"Confidence Interval: ${lower_bound:,.2f} - ${upper_bound:,.2f}")

print("\nFeature Importance:")
for feature, importance in response['feature_importance'].items():
    print(f"  {feature}: {importance*100:.1f}%")

# Expected Output:
# Predicted Price: $18,500.50
# Confidence Level: 85.0%
# Confidence Interval: $17,300.25 - $19,700.75
#
# Feature Importance:
#   mileage: 32.0%
#   age: 28.0%
#   engine_size: 18.0%
#   brand: 15.0%
#   fuel_type: 7.0%
```

### Example 4: Multiple Predictions

```python
# List of cars to price
cars = [
    {
        "age": 3,
        "mileage": 45000,
        "engine_size": 1.8,
        "brand": "Honda",
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "color": "Black",
        "accident_history": False,
        "service_history": True,
        "ownership_history": 1,
        "current_price": 18000
    },
    {
        "age": 7,
        "mileage": 120000,
        "engine_size": 2.5,
        "brand": "Ford",
        "fuel_type": "Diesel",
        "transmission": "Manual",
        "color": "Silver",
        "accident_history": False,
        "service_history": False,
        "ownership_history": 2,
        "current_price": 12000
    },
    {
        "age": 1,
        "mileage": 5000,
        "engine_size": 3.0,
        "brand": "BMW",
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "color": "White",
        "accident_history": False,
        "service_history": True,
        "ownership_history": 1,
        "current_price": 45000
    }
]

# Get predictions for all cars
results = []
for i, car in enumerate(cars, 1):
    response = make_request("/predict", method="POST", data=car)
    results.append({
        "car_id": i,
        "brand": car["brand"],
        "age": car["age"],
        "predicted_price": response['predicted_price'],
        "confidence": response['confidence_level'],
        "model_version": response['model_version']
    })
    print(f"Car {i}: {car['brand']} ({car['age']}yo) → ${response['predicted_price']:,.2f}")

# Display summary
print(f"\nTotal cars processed: {len(results)}")
print(f"Average predicted price: ${sum(r['predicted_price'] for r in results)/len(results):,.2f}")
```

### Example 5: Compare Predictions with Different Features

```python
# Base car
base_car = {
    "age": 5,
    "mileage": 75000,
    "engine_size": 2.0,
    "brand": "Toyota",
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "color": "White",
    "accident_history": False,
    "service_history": True,
    "ownership_history": 1,
    "current_price": 15000
}

# Test different scenarios
scenarios = {
    "High Mileage": {"mileage": 150000},
    "Older Car": {"age": 10},
    "Larger Engine": {"engine_size": 3.5},
    "Premium Brand": {"brand": "BMW"},
}

print("Price Sensitivity Analysis:\n")
print(f"Base Price: ${make_request('/predict', 'POST', base_car)['predicted_price']:,.2f}\n")

for scenario_name, changes in scenarios.items():
    test_car = base_car.copy()
    test_car.update(changes)
    
    response = make_request("/predict", method="POST", data=test_car)
    predicted = response['predicted_price']
    base_predicted = make_request("/predict", method="POST", data=base_car)['predicted_price']
    
    difference = predicted - base_predicted
    percent_change = (difference / base_predicted) * 100
    
    print(f"{scenario_name:20} → ${predicted:>10,.2f} ({percent_change:+.1f}%)")

# Expected Output:
# Price Sensitivity Analysis:
#
# Base Price: $18,500.50
#
# High Mileage      →   $15,200.00 (-17.8%)
# Older Car         →   $14,300.25 (-22.6%)
# Larger Engine     →   $22,450.75 (+21.3%)
# Premium Brand     →   $24,600.50 (+32.8%)
```

### Example 6: Error Handling

```python
def predict_with_error_handling(car_data):
    """Make prediction with comprehensive error handling"""
    
    try:
        # Validate input
        required_fields = [
            "age", "mileage", "engine_size", "brand",
            "fuel_type", "transmission", "color"
        ]
        
        for field in required_fields:
            if field not in car_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Check value ranges
        if not (0 <= car_data["age"] <= 50):
            raise ValueError("Age must be between 0 and 50 years")
        
        if not (0 <= car_data["mileage"] <= 300000):
            raise ValueError("Mileage must be between 0 and 300,000 km")
        
        # Make prediction
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=car_data,
            headers=HEADERS,
            timeout=10
        )
        response.raise_for_status()
        
        return response.json()
    
    except ValueError as ve:
        print(f"Validation Error: {ve}")
        return None
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out. API not responding.")
        return None
    
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API. Is the server running?")
        return None
    
    except requests.exceptions.HTTPError as he:
        print(f"HTTP Error: {he.response.status_code} - {he.response.text}")
        return None
    
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None

# Usage
car_data = {"age": 5, "mileage": 75000, ...}  # Include all fields
result = predict_with_error_handling(car_data)

if result:
    print(f"Success: ${result['predicted_price']:,.2f}")
else:
    print("Prediction failed")
```

---

## cURL Examples

### Basic Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

**Output:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-05T21:35:00Z",
  "version": "1.0.0"
}
```

### Get Model Info

```bash
curl -X GET "http://localhost:8000/info" | jq .
```

### Single Prediction

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "age": 5,
    "mileage": 75000,
    "engine_size": 2.0,
    "brand": "Toyota",
    "fuel_type": "Petrol",
    "transmission": "Automatic",
    "color": "White",
    "accident_history": false,
    "service_history": true,
    "ownership_history": 1,
    "current_price": 15000
  }' | jq .
```

### Pretty Print Response

```bash
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"age": 5, "mileage": 75000, ...}' | jq '{
    price: .predicted_price,
    confidence: .confidence_level,
    range: .confidence_interval
  }'
```

### Save Response to File

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  -o prediction_result.json
```

### With Custom Headers

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/1.0" \
  -H "X-Request-ID: abc123" \
  -d '{...}'
```

---

## JavaScript/Node.js Examples

### Using Fetch API

```javascript
// Modern browsers and Node 18+
const API_BASE_URL = "http://localhost:8000";

async function healthCheck() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    const data = await response.json();
    console.log("Health Status:", data);
    return data;
  } catch (error) {
    console.error("Error:", error);
  }
}

async function predictPrice(carData) {
  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(carData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Prediction error:", error);
  }
}

// Usage
const carData = {
  age: 5,
  mileage: 75000,
  engine_size: 2.0,
  brand: "Toyota",
  fuel_type: "Petrol",
  transmission: "Automatic",
  color: "White",
  accident_history: false,
  service_history: true,
  ownership_history: 1,
  current_price: 15000
};

(async () => {
  const result = await predictPrice(carData);
  console.log(`Predicted Price: $${result.predicted_price.toFixed(2)}`);
  console.log(`Confidence: ${(result.confidence_level * 100).toFixed(1)}%`);
})();
```

### Using Axios (Node.js)

```javascript
const axios = require('axios');

const API = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" }
});

async function makePrediction(carData) {
  try {
    const { data } = await API.post("/predict", carData);
    return data;
  } catch (error) {
    console.error("Prediction failed:", error.response?.data || error.message);
    throw error;
  }
}

// Usage
makePrediction(carData)
  .then(result => {
    console.log(`Price: $${result.predicted_price}`);
    console.log(`Features Importance:`, result.feature_importance);
  })
  .catch(error => console.error("Error:", error));
```

### React Component Example

```javascript
import React, { useState, useEffect } from 'react';

function CarPricePrediction() {
  const [features, setFeatures] = useState({
    age: 5,
    mileage: 75000,
    engine_size: 2.0,
    brand: "Toyota",
    fuel_type: "Petrol",
    transmission: "Automatic",
    color: "White",
    accident_history: false,
    service_history: true,
    ownership_history: 1,
    current_price: 15000
  });
  
  const [prediction, setPrediction] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch("http://localhost:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(features)
      });
      
      const data = await response.json();
      setPrediction(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="prediction-form">
      <h2>Car Price Predictor</h2>
      
      <input
        type="number"
        placeholder="Age (years)"
        value={features.age}
        onChange={e => setFeatures({...features, age: parseInt(e.target.value)})}
      />
      
      <button onClick={handlePredict} disabled={loading}>
        {loading ? "Predicting..." : "Predict Price"}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      {prediction && (
        <div className="result">
          <h3>Estimated Price: ${prediction.predicted_price.toFixed(2)}</h3>
          <p>Confidence: {(prediction.confidence_level * 100).toFixed(1)}%</p>
        </div>
      )}
    </div>
  );
}

export default CarPricePrediction;
```

---

## Batch Processing

### Process CSV File

```python
import csv
import requests

def process_car_csv(input_file, output_file):
    """Process CSV file of cars and add price predictions"""
    
    API_URL = "http://localhost:8000/predict"
    
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames + ['predicted_price', 'confidence']
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for i, row in enumerate(reader, 1):
            # Convert string values to proper types
            car_data = {
                'age': int(row['age']),
                'mileage': int(row['mileage']),
                'engine_size': float(row['engine_size']),
                'brand': row['brand'],
                'fuel_type': row['fuel_type'],
                'transmission': row['transmission'],
                'color': row['color'],
                'accident_history': row['accident_history'].lower() == 'true',
                'service_history': row['service_history'].lower() == 'true',
                'ownership_history': int(row['ownership_history']),
                'current_price': float(row['current_price'])
            }
            
            # Make prediction
            response = requests.post(API_URL, json=car_data)
            prediction = response.json()
            
            # Add results to row
            row['predicted_price'] = prediction['predicted_price']
            row['confidence'] = prediction['confidence_level']
            
            # Write to output
            writer.writerow(row)
            
            print(f"Processed car {i}: {car_data['brand']}")

# Usage
process_car_csv('cars.csv', 'cars_with_predictions.csv')
```

### Example Input CSV

```csv
age,mileage,engine_size,brand,fuel_type,transmission,color,accident_history,service_history,ownership_history,current_price
3,45000,1.8,Honda,Petrol,Automatic,Black,false,true,1,18000
5,75000,2.0,Toyota,Petrol,Automatic,White,false,true,1,15000
7,120000,2.5,Ford,Diesel,Manual,Silver,false,false,2,12000
```

---

## Error Handling

### Common Errors & Solutions

```python
import requests
from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException
)

def handle_api_error(error):
    """Comprehensive error handling"""
    
    if isinstance(error, ConnectionError):
        print("❌ Connection Error: Cannot reach API")
        print("   Solution: Ensure API is running with 'python -m uvicorn predict_api:app'")
    
    elif isinstance(error, Timeout):
        print("❌ Timeout Error: API not responding")
        print("   Solution: API may be overloaded. Wait and retry.")
    
    elif isinstance(error, HTTPError):
        status = error.response.status_code
        if status == 400:
            print("❌ Bad Request: Invalid input data")
            print(f"   Details: {error.response.json()}")
        elif status == 404:
            print("❌ Not Found: API endpoint doesn't exist")
        elif status == 500:
            print("❌ Server Error: Internal API error")
    
    else:
        print(f"❌ Unexpected Error: {error}")

# Usage with retry logic
def predict_with_retry(car_data, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.post(
                "http://localhost:8000/predict",
                json=car_data,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        
        except RequestException as e:
            if attempt == max_retries - 1:
                handle_api_error(e)
                return None
            print(f"Attempt {attempt + 1} failed, retrying...")
```

---

## Performance Monitoring

```python
import time
import statistics

def measure_prediction_time(car_data, iterations=10):
    """Measure API response time"""
    
    times = []
    
    for _ in range(iterations):
        start = time.time()
        response = requests.post(
            "http://localhost:8000/predict",
            json=car_data,
            timeout=10
        )
        elapsed = time.time() - start
        times.append(elapsed * 1000)  # Convert to ms
    
    print(f"Prediction Time Statistics ({iterations} iterations):")
    print(f"  Average: {statistics.mean(times):.2f}ms")
    print(f"  Median:  {statistics.median(times):.2f}ms")
    print(f"  Min:     {min(times):.2f}ms")
    print(f"  Max:     {max(times):.2f}ms")
    print(f"  StdDev:  {statistics.stdev(times):.2f}ms")

# Usage
measure_prediction_time(car_data)

# Expected Output:
# Prediction Time Statistics (10 iterations):
#   Average: 125.34ms
#   Median:  120.15ms
#   Min:     95.23ms
#   Max:     210.56ms
#   StdDev:  35.67ms
```

---

## Complete Working Example

```python
#!/usr/bin/env python3
"""
Complete Car Price Prediction API Example
"""

import requests
import json
from datetime import datetime

class CarPricePredictorClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def health_check(self):
        """Check if API is running"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Health check failed: {e}")
            return None
    
    def get_model_info(self):
        """Get model information"""
        try:
            response = self.session.get(f"{self.base_url}/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to get model info: {e}")
            return None
    
    def predict(self, car_data):
        """Make price prediction"""
        try:
            response = self.session.post(
                f"{self.base_url}/predict",
                json=car_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Prediction failed: {e}")
            return None
    
    def print_prediction(self, prediction):
        """Pretty print prediction result"""
        if not prediction:
            return
        
        print("\n" + "="*50)
        print("PREDICTION RESULT")
        print("="*50)
        print(f"Predicted Price: ${prediction['predicted_price']:,.2f}")
        print(f"Confidence Level: {prediction['confidence_level']*100:.1f}%")
        print(f"Confidence Range: ${prediction['confidence_interval']['lower']:,.2f} - "
              f"${prediction['confidence_interval']['upper']:,.2f}")
        print("\nFeature Importance:")
        for feature, importance in sorted(
            prediction['feature_importance'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            bar = "█" * int(importance * 50)
            print(f"  {feature:20} {bar} {importance*100:.1f}%")
        print("="*50 + "\n")

# Usage
if __name__ == "__main__":
    # Initialize client
    client = CarPricePredictorClient()
    
    # Health check
    print("Checking API health...")
    if not client.health_check():
        print("❌ API is not running")
        exit(1)
    print("✓ API is healthy\n")
    
    # Get model info
    print("Fetching model information...")
    info = client.get_model_info()
    if info:
        print(f"✓ Model: {info['model_name']} v{info['model_version']}\n")
    
    # Make prediction
    car = {
        "age": 5,
        "mileage": 75000,
        "engine_size": 2.0,
        "brand": "Toyota",
        "fuel_type": "Petrol",
        "transmission": "Automatic",
        "color": "White",
        "accident_history": False,
        "service_history": True,
        "ownership_history": 1,
        "current_price": 15000
    }
    
    print("Making prediction...")
    prediction = client.predict(car)
    client.print_prediction(prediction)
```

---

**API Examples Complete! 🎉**

Save these examples as `.py` or `.sh` files and run them with:

```bash
# Python
python example.py

# Bash
bash curl_example.sh
```
