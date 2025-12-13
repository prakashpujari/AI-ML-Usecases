# RNN/LSTM Stock Price Forecasting & Sentiment Analysis

This project demonstrates two powerful applications of Recurrent Neural Networks (RNN) and Long Short-Term Memory (LSTM) models:

1. **Stock Price Forecasting**: Predict future stock prices using historical data and LSTM networks
2. **Sentiment Analysis**: Analyze text sentiment using SimpleRNN with embedding

## Project Structure

```
RecurrentNeuralNetwork(RNNLSTM)/
├── rnn_lstm_app.py      # Core RNN/LSTM implementations
├── streamlit_app.py     # Interactive web interface
├── sample_stock_prices.csv    # Example time series data
└── sample_sentiment_text.csv  # Example sentiment data
```

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit interface:
```bash
# Important: Use quotes around path with parentheses in PowerShell
streamlit run "path/to/RecurrentNeuralNetwork(RNNLSTM)/streamlit_app.py"
```

3. Open your browser to the displayed URL (typically http://localhost:8501)

### Verify your environment

If you want to quickly check that all required Python packages are installed in your active environment, run the small checker script included in this folder:

```bash
python check_requirements.py
```

The script will print OK for installed packages and list any missing packages with a suggested `pip install` command.

## Features

### Time Series Forecasting (LSTM)
- Predict future values based on historical patterns
- Interactive sequence length and epoch configuration
- Real-time training and prediction visualization
- Next-value prediction with confidence display

### Sentiment Analysis (RNN)
- Analyze text sentiment using embedded SimpleRNN
- Support for binary labels (positive/negative or 0/1)
- Real-time accuracy metrics
- Batch prediction on multiple texts

### Interface Features
- Upload custom datasets or use provided samples
- Interactive parameter tuning
- Live training progress
- Results visualization
- Error handling and user guidance

## Data Format Requirements

### Stock Price Data (CSV)
Required columns:
```csv
Close
100.50
101.23
99.87
...
```

### Sentiment Data (CSV)
Required format:
```csv
Text,Sentiment
"Great product!",positive
"Not worth it",negative
...
```

## Technical Implementation

### LSTM Module
The LSTM implementation (`rnn_lstm_app.py`) includes:

```python
def prepare_time_series(data_series, seq_len=10):
    """
    Prepares time series data:
    1. Normalizes using MinMaxScaler
    2. Creates sequences of length seq_len
    3. Returns (X, y) pairs and scaler
    """

def create_lstm(seq_len, features=1, units=50):
    """
    Creates LSTM model:
    - Input shape: (seq_len, features)
    - LSTM layer: 50 units
    - Dense output layer
    - Adam optimizer, MSE loss
    """
```

### RNN Module
The RNN implementation includes:

```python
def prepare_texts(texts, max_words=1000, max_len=20):
    """
    Prepares text data:
    1. Tokenizes text
    2. Converts to sequences
    3. Pads to uniform length
    """

def create_rnn(vocab_size=1000, max_len=20):
    """
    Creates RNN model:
    - Embedding layer
    - SimpleRNN layer
    - Sigmoid output
    - Binary cross-entropy loss
    """
```

## Configuration Options

### LSTM Parameters
- `seq_len`: Length of input sequences (default: 10)
- `features`: Number of input features (default: 1)
- `units`: LSTM units (default: 50)
- `epochs`: Training iterations (adjustable in UI)

### RNN Parameters
- `max_words`: Vocabulary size (default: 1000)
- `max_len`: Maximum sequence length (default: 20)
- `embed_dim`: Embedding dimensions (default: 16)
- `rnn_units`: RNN unit count (default: 32)

## Troubleshooting

### Common Issues

1. Shape Errors:
   - Error: "Invalid input shape"
   - Solution: Ensure enough data points for sequence length
   - Minimum required: data points > sequence length

2. Memory Issues:
   - Reduce batch size (default: 16)
   - Decrease sequence length
   - Lower model complexity (units)

3. Performance Issues:
   - Increase epochs
   - Adjust learning rate
   - Normalize data appropriately

## Advanced Usage

### Running Without UI
Import and use models directly:

```python
from rnn_lstm_app import demo_time_series_workflow, demo_text_workflow

# Time series prediction
df, predictions = demo_time_series_workflow('your_data.csv')

# Sentiment analysis
results = demo_text_workflow('your_sentiment.csv')
```

### Customization
Modify model architecture in `rnn_lstm_app.py`:
- Adjust layer sizes
- Change optimization parameters
- Add regularization
- Modify preprocessing steps

## Privacy Note
- Use anonymized data for production
- No data is stored or transmitted externally
- All processing is local to your machine

## Contributing
Feel free to submit:
- Bug reports
- Feature requests
- Pull requests
- Documentation improvements
