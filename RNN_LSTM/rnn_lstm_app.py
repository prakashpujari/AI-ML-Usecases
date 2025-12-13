import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Embedding, SimpleRNN
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences

def load_stock_data(file_path):
    """Load and prepare stock price data"""
    df = pd.read_csv(file_path)
    return df

def load_sentiment_data(file_path):
    """Load and prepare sentiment data"""
    df = pd.read_csv(file_path)
    return df

def create_lstm_model(seq_length, features=1):
    """Create and return an LSTM model for time series prediction"""
    model = Sequential([
        LSTM(50, input_shape=(seq_length, features)),
        Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def prepare_time_series_data(data, seq_length):
    """Prepare time series data for LSTM model"""
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(data.reshape(-1, 1))
    
    X, y = [], []
    for i in range(len(scaled_data) - seq_length):
        X.append(scaled_data[i:i+seq_length])
        y.append(scaled_data[i+seq_length])
    
    return np.array(X), np.array(y), scaler

def predict_stock_prices(model, X, scaler):
    """Make predictions using the LSTM model"""
    predictions = model.predict(X)
    return scaler.inverse_transform(predictions)

def create_rnn_model(vocab_size=100, max_length=10, embedding_dim=8):
    """Create and return an RNN model for sentiment analysis"""
    model = Sequential([
        Embedding(input_dim=vocab_size, output_dim=embedding_dim, input_length=max_length),
        SimpleRNN(16),
        Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    return model

def prepare_text_data(texts, max_words=100, max_length=10):
    """Prepare text data for RNN model"""
    tokenizer = Tokenizer(num_words=max_words)
    tokenizer.fit_on_texts(texts)
    sequences = tokenizer.texts_to_sequences(texts)
    X = pad_sequences(sequences, maxlen=max_length)
    return X, tokenizer

def train_and_evaluate_models():
    """Example usage of the models"""
    # Example for LSTM (time series)
    sample_data = np.sin(np.linspace(0, 100, 1000))  # Sample time series data
    seq_length = 10
    X, y, scaler = prepare_time_series_data(sample_data, seq_length)
    lstm_model = create_lstm_model(seq_length)
    lstm_model.fit(X, y, epochs=50, batch_size=32, verbose=1)
    
    # Example for RNN (sentiment analysis)
    sample_texts = [
        "This is great",
        "Not very good",
        "Excellent work",
        "Poor performance"
    ]
    sample_sentiments = np.array([1, 0, 1, 0])  # 1 for positive, 0 for negative
    
    X_text, tokenizer = prepare_text_data(sample_texts)
    rnn_model = create_rnn_model()
    rnn_model.fit(X_text, sample_sentiments, epochs=30, batch_size=1, verbose=1)

if __name__ == "__main__":
    train_and_evaluate_models()