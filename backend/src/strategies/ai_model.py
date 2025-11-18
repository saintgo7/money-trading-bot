import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from decimal import Decimal
from loguru import logger


class LSTMTradingModel(nn.Module):
    """
    LSTM-based trading model for predicting price movements

    Architecture:
    - Input: Technical indicators + price data
    - LSTM layers for sequence learning
    - Fully connected layers for prediction
    - Output: Buy/Sell/Hold signal + confidence
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        output_size: int = 3,  # Buy, Sell, Hold
    ):
        super(LSTMTradingModel, self).__init__()

        self.hidden_size = hidden_size
        self.num_layers = num_layers

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
        )

        # Fully connected layers
        self.fc1 = nn.Linear(hidden_size, 64)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout)
        self.fc2 = nn.Linear(64, output_size)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)

        Returns:
            output: Prediction tensor of shape (batch_size, output_size)
        """
        # LSTM forward
        lstm_out, (h_n, c_n) = self.lstm(x)

        # Take the last output
        last_output = lstm_out[:, -1, :]

        # Fully connected layers
        out = self.fc1(last_output)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        out = self.softmax(out)

        return out


class TransformerTradingModel(nn.Module):
    """
    Transformer-based trading model for better long-term dependency learning
    """

    def __init__(
        self,
        input_size: int,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 4,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        output_size: int = 3,
    ):
        super(TransformerTradingModel, self).__init__()

        self.input_projection = nn.Linear(input_size, d_model)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True,
        )

        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        self.fc = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, output_size),
            nn.Softmax(dim=1),
        )

    def forward(self, x):
        """
        Forward pass

        Args:
            x: Input tensor of shape (batch_size, sequence_length, input_size)

        Returns:
            output: Prediction tensor of shape (batch_size, output_size)
        """
        x = self.input_projection(x)
        x = self.transformer_encoder(x)
        x = x[:, -1, :]  # Take last sequence output
        output = self.fc(x)
        return output


class AITradingStrategy:
    """
    AI-based trading strategy using deep learning models
    """

    def __init__(
        self,
        model_type: str = "lstm",
        sequence_length: int = 60,
        device: str = "cpu",
    ):
        self.model_type = model_type
        self.sequence_length = sequence_length
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.model: Optional[nn.Module] = None
        self.scaler = None
        self.feature_columns = []

        logger.info(f"Initialized AI Trading Strategy with {model_type} on {self.device}")

    def initialize_model(self, input_size: int):
        """Initialize the trading model"""
        if self.model_type == "lstm":
            self.model = LSTMTradingModel(
                input_size=input_size, hidden_size=128, num_layers=2, dropout=0.2
            )
        elif self.model_type == "transformer":
            self.model = TransformerTradingModel(
                input_size=input_size, d_model=128, nhead=8, num_layers=4, dropout=0.1
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        self.model.to(self.device)
        logger.info(f"Model initialized with {sum(p.numel() for p in self.model.parameters())} parameters")

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Prepare features from market data

        Args:
            df: DataFrame with OHLCV and indicator data

        Returns:
            Feature array
        """
        # Select relevant features
        feature_cols = [
            "close",
            "volume",
            "rsi",
            "macd",
            "macd_signal",
            "bb_upper",
            "bb_middle",
            "bb_lower",
            "sma_20",
            "sma_50",
            "ema_12",
            "ema_26",
            "stoch_k",
            "stoch_d",
            "atr",
            "adx",
        ]

        # Filter available columns
        self.feature_columns = [col for col in feature_cols if col in df.columns]

        # Extract features
        features = df[self.feature_columns].values

        # Normalize features (using StandardScaler-like normalization)
        mean = np.nanmean(features, axis=0)
        std = np.nanstd(features, axis=0)
        features = (features - mean) / (std + 1e-8)

        # Fill NaN values
        features = np.nan_to_num(features, nan=0.0)

        return features

    def create_sequences(self, features: np.ndarray) -> np.ndarray:
        """
        Create sequences for LSTM/Transformer input

        Args:
            features: Feature array

        Returns:
            Sequences of shape (num_sequences, sequence_length, num_features)
        """
        sequences = []
        for i in range(len(features) - self.sequence_length + 1):
            sequences.append(features[i : i + self.sequence_length])
        return np.array(sequences)

    def predict(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Make trading prediction

        Args:
            df: DataFrame with market data and indicators

        Returns:
            Dict with signal, confidence, and probabilities
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call initialize_model() first.")

        self.model.eval()

        # Prepare features
        features = self.prepare_features(df)

        # Create sequences
        sequences = self.create_sequences(features)

        if len(sequences) == 0:
            return {"signal": "hold", "confidence": 0.0, "probabilities": [0.33, 0.33, 0.34]}

        # Get the latest sequence
        latest_sequence = sequences[-1:]

        # Convert to tensor
        x = torch.FloatTensor(latest_sequence).to(self.device)

        # Make prediction
        with torch.no_grad():
            output = self.model(x)
            probabilities = output.cpu().numpy()[0]

        # Determine signal
        signal_idx = np.argmax(probabilities)
        signals = ["sell", "hold", "buy"]
        signal = signals[signal_idx]
        confidence = float(probabilities[signal_idx])

        logger.info(f"AI Prediction: {signal} (confidence: {confidence:.2%})")

        return {
            "signal": signal,
            "confidence": confidence,
            "probabilities": probabilities.tolist(),
            "buy_prob": float(probabilities[2]),
            "sell_prob": float(probabilities[0]),
            "hold_prob": float(probabilities[1]),
        }

    def train(
        self,
        train_data: pd.DataFrame,
        train_labels: np.ndarray,
        epochs: int = 100,
        batch_size: int = 32,
        learning_rate: float = 0.001,
    ):
        """
        Train the model

        Args:
            train_data: Training data DataFrame
            train_labels: Training labels (0: sell, 1: hold, 2: buy)
            epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
        """
        if self.model is None:
            features = self.prepare_features(train_data)
            self.initialize_model(input_size=features.shape[1])

        # Prepare data
        features = self.prepare_features(train_data)
        sequences = self.create_sequences(features)

        # Align labels with sequences
        labels = train_labels[self.sequence_length - 1 :]

        # Convert to tensors
        X = torch.FloatTensor(sequences).to(self.device)
        y = torch.LongTensor(labels).to(self.device)

        # Create data loader
        dataset = torch.utils.data.TensorDataset(X, y)
        dataloader = torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=True)

        # Loss and optimizer
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)

        # Training loop
        self.model.train()
        for epoch in range(epochs):
            total_loss = 0
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                outputs = self.model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            avg_loss = total_loss / len(dataloader)
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch [{epoch+1}/{epochs}], Loss: {avg_loss:.4f}")

        logger.info("Training completed")

    def save_model(self, path: str):
        """Save model to file"""
        if self.model is None:
            raise ValueError("No model to save")

        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "model_type": self.model_type,
                "sequence_length": self.sequence_length,
                "feature_columns": self.feature_columns,
            },
            path,
        )
        logger.info(f"Model saved to {path}")

    def load_model(self, path: str, input_size: int):
        """Load model from file"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model_type = checkpoint["model_type"]
        self.sequence_length = checkpoint["sequence_length"]
        self.feature_columns = checkpoint["feature_columns"]

        self.initialize_model(input_size)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model.eval()

        logger.info(f"Model loaded from {path}")
