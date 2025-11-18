"""
Advanced Feature Engineering for Trading ML Models
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import logging

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """Advanced feature engineering for trading data"""

    def __init__(self, lookback_periods: List[int] = None):
        """
        Initialize feature engineer

        Args:
            lookback_periods: Periods for rolling features (default: [5, 10, 20, 50])
        """
        if lookback_periods is None:
            lookback_periods = [5, 10, 20, 50]

        self.lookback_periods = lookback_periods
        self.scaler = StandardScaler()
        self.fitted = False

    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with engineered features
        """
        df = df.copy()

        # Price-based features
        df = self._create_price_features(df)

        # Volume-based features
        df = self._create_volume_features(df)

        # Momentum features
        df = self._create_momentum_features(df)

        # Volatility features
        df = self._create_volatility_features(df)

        # Pattern features
        df = self._create_pattern_features(df)

        # Statistical features
        df = self._create_statistical_features(df)

        # Time-based features
        df = self._create_time_features(df)

        # Interaction features
        df = self._create_interaction_features(df)

        return df

    def _create_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create price-based features"""

        # Price changes
        df['price_change'] = df['close'].pct_change()
        df['price_change_abs'] = df['price_change'].abs()

        # Log returns
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))

        # OHLC relationships
        df['high_low_ratio'] = df['high'] / df['low']
        df['close_open_ratio'] = df['close'] / df['open']
        df['body_size'] = abs(df['close'] - df['open']) / df['open']
        df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['open']
        df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['open']

        # Price position in range
        df['price_position'] = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10)

        # Gap features
        df['gap'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)

        # Moving averages
        for period in self.lookback_periods:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
            df[f'ema_{period}'] = df['close'].ewm(span=period, adjust=False).mean()

            # Distance from MA
            df[f'close_sma_{period}_ratio'] = df['close'] / df[f'sma_{period}']
            df[f'close_ema_{period}_ratio'] = df['close'] / df[f'ema_{period}']

        # Moving average crossovers
        df['sma_5_20_cross'] = (df['sma_5'] > df['sma_20']).astype(int)
        df['ema_5_20_cross'] = (df['ema_5'] > df['ema_20']).astype(int)

        return df

    def _create_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volume-based features"""

        # Volume changes
        df['volume_change'] = df['volume'].pct_change()

        # Volume moving averages
        for period in self.lookback_periods:
            df[f'volume_sma_{period}'] = df['volume'].rolling(window=period).mean()
            df[f'volume_ratio_{period}'] = df['volume'] / df[f'volume_sma_{period}']

        # Price-volume correlation
        for period in [10, 20]:
            df[f'price_volume_corr_{period}'] = df['close'].rolling(period).corr(df['volume'])

        # On-Balance Volume (OBV)
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        df['obv_ema'] = df['obv'].ewm(span=20, adjust=False).mean()

        # Volume Price Trend (VPT)
        df['vpt'] = (df['volume'] * df['close'].pct_change()).cumsum()

        # Money Flow
        df['money_flow'] = df['close'] * df['volume']
        for period in [10, 20]:
            df[f'money_flow_sma_{period}'] = df['money_flow'].rolling(period).mean()

        return df

    def _create_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create momentum features"""

        # Rate of Change (ROC)
        for period in self.lookback_periods:
            df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) /
                                    df['close'].shift(period) * 100)

        # Momentum
        for period in [5, 10, 20]:
            df[f'momentum_{period}'] = df['close'] - df['close'].shift(period)

        # Relative Strength
        for period in [5, 10, 14]:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / (loss + 1e-10)
            df[f'rsi_{period}'] = 100 - (100 / (1 + rs))

        # Stochastic Oscillator
        for period in [14, 21]:
            low_min = df['low'].rolling(window=period).min()
            high_max = df['high'].rolling(window=period).max()
            df[f'stoch_{period}'] = 100 * (df['close'] - low_min) / (high_max - low_min + 1e-10)
            df[f'stoch_{period}_sma'] = df[f'stoch_{period}'].rolling(3).mean()

        # Williams %R
        for period in [14, 21]:
            high_max = df['high'].rolling(window=period).max()
            low_min = df['low'].rolling(window=period).min()
            df[f'williams_r_{period}'] = -100 * (high_max - df['close']) / (high_max - low_min + 1e-10)

        return df

    def _create_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create volatility features"""

        # Historical volatility
        for period in self.lookback_periods:
            df[f'volatility_{period}'] = df['log_return'].rolling(period).std() * np.sqrt(252)

        # Average True Range (ATR)
        for period in [10, 14, 20]:
            high_low = df['high'] - df['low']
            high_close = abs(df['high'] - df['close'].shift())
            low_close = abs(df['low'] - df['close'].shift())
            true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df[f'atr_{period}'] = true_range.rolling(period).mean()

            # Normalized ATR
            df[f'atr_{period}_norm'] = df[f'atr_{period}'] / df['close']

        # Bollinger Bands
        for period in [20, 50]:
            sma = df['close'].rolling(period).mean()
            std = df['close'].rolling(period).std()

            df[f'bb_upper_{period}'] = sma + (std * 2)
            df[f'bb_lower_{period}'] = sma - (std * 2)
            df[f'bb_middle_{period}'] = sma

            # BB Width and Position
            df[f'bb_width_{period}'] = (df[f'bb_upper_{period}'] - df[f'bb_lower_{period}']) / sma
            df[f'bb_position_{period}'] = (df['close'] - df[f'bb_lower_{period}']) / (
                df[f'bb_upper_{period}'] - df[f'bb_lower_{period}'] + 1e-10
            )

        # Keltner Channels
        for period in [20]:
            ema = df['close'].ewm(span=period, adjust=False).mean()
            atr = df[f'atr_{period}']

            df[f'keltner_upper_{period}'] = ema + (atr * 2)
            df[f'keltner_lower_{period}'] = ema - (atr * 2)
            df[f'keltner_width_{period}'] = (df[f'keltner_upper_{period}'] -
                                              df[f'keltner_lower_{period}']) / ema

        return df

    def _create_pattern_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create candlestick pattern features"""

        # Doji
        df['doji'] = (abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10) < 0.1).astype(int)

        # Hammer / Hanging Man
        body = abs(df['close'] - df['open'])
        lower_shadow = df[['open', 'close']].min(axis=1) - df['low']
        upper_shadow = df['high'] - df[['open', 'close']].max(axis=1)

        df['hammer'] = ((lower_shadow > 2 * body) & (upper_shadow < body)).astype(int)
        df['hanging_man'] = ((lower_shadow > 2 * body) & (upper_shadow < body) &
                              (df['close'] < df['open'])).astype(int)

        # Engulfing patterns
        df['bullish_engulfing'] = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (df['open'] < df['close'].shift(1))
        ).astype(int)

        df['bearish_engulfing'] = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open'].shift(1)) &
            (df['open'] > df['close'].shift(1))
        ).astype(int)

        # Morning/Evening Star (simplified)
        df['morning_star'] = (
            (df['close'].shift(2) < df['open'].shift(2)) &  # Day 1: bearish
            (abs(df['close'].shift(1) - df['open'].shift(1)) < body.shift(2) * 0.3) &  # Day 2: small body
            (df['close'] > df['open']) &  # Day 3: bullish
            (df['close'] > (df['close'].shift(2) + df['open'].shift(2)) / 2)
        ).astype(int)

        return df

    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create statistical features"""

        for period in [10, 20, 50]:
            # Skewness
            df[f'skew_{period}'] = df['log_return'].rolling(period).skew()

            # Kurtosis
            df[f'kurt_{period}'] = df['log_return'].rolling(period).kurt()

            # Z-score
            mean = df['close'].rolling(period).mean()
            std = df['close'].rolling(period).std()
            df[f'zscore_{period}'] = (df['close'] - mean) / (std + 1e-10)

            # Percentile rank
            df[f'percentile_{period}'] = df['close'].rolling(period).apply(
                lambda x: stats.percentileofscore(x, x.iloc[-1]) / 100 if len(x) > 0 else 0.5
            )

        return df

    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create time-based features"""

        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            df['day_of_month'] = pd.to_datetime(df['timestamp']).dt.day
            df['month'] = pd.to_datetime(df['timestamp']).dt.month

            # Cyclical encoding
            df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
            df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
            df['day_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
            df['day_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)

        return df

    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create feature interactions"""

        # Price * Volume
        df['price_volume'] = df['close'] * df['volume']

        # Volatility * Volume
        if 'volatility_20' in df.columns:
            df['volatility_volume'] = df['volatility_20'] * df['volume']

        # RSI * ATR
        if 'rsi_14' in df.columns and 'atr_14' in df.columns:
            df['rsi_atr'] = df['rsi_14'] * df['atr_14_norm']

        return df

    def fit_transform(self, df: pd.DataFrame, exclude_columns: List[str] = None) -> pd.DataFrame:
        """
        Fit scaler and transform features

        Args:
            df: DataFrame with features
            exclude_columns: Columns to exclude from scaling

        Returns:
            Scaled DataFrame
        """
        if exclude_columns is None:
            exclude_columns = ['timestamp']

        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        scale_cols = [col for col in numeric_cols if col not in exclude_columns]

        # Fit and transform
        df_scaled = df.copy()
        df_scaled[scale_cols] = self.scaler.fit_transform(df[scale_cols].fillna(0))

        self.fitted = True

        return df_scaled

    def transform(self, df: pd.DataFrame, exclude_columns: List[str] = None) -> pd.DataFrame:
        """
        Transform features using fitted scaler

        Args:
            df: DataFrame with features
            exclude_columns: Columns to exclude from scaling

        Returns:
            Scaled DataFrame
        """
        if not self.fitted:
            raise ValueError("Scaler not fitted. Call fit_transform first.")

        if exclude_columns is None:
            exclude_columns = ['timestamp']

        # Select numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        scale_cols = [col for col in numeric_cols if col not in exclude_columns]

        # Transform
        df_scaled = df.copy()
        df_scaled[scale_cols] = self.scaler.transform(df[scale_cols].fillna(0))

        return df_scaled

    def select_features(
        self,
        df: pd.DataFrame,
        target: pd.Series,
        method: str = 'correlation',
        top_k: int = 50
    ) -> List[str]:
        """
        Select top features

        Args:
            df: DataFrame with features
            target: Target variable
            method: Selection method ('correlation', 'mutual_info')
            top_k: Number of top features to select

        Returns:
            List of selected feature names
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        if method == 'correlation':
            # Correlation with target
            correlations = df[numeric_cols].corrwith(target).abs()
            selected = correlations.nlargest(top_k).index.tolist()

        elif method == 'mutual_info':
            from sklearn.feature_selection import mutual_info_regression

            # Mutual information
            mi_scores = mutual_info_regression(
                df[numeric_cols].fillna(0),
                target,
                random_state=42
            )
            mi_df = pd.DataFrame({'feature': numeric_cols, 'score': mi_scores})
            selected = mi_df.nlargest(top_k, 'score')['feature'].tolist()

        else:
            raise ValueError(f"Unknown method: {method}")

        logger.info(f"Selected {len(selected)} features using {method}")

        return selected


def create_target_variable(
    df: pd.DataFrame,
    horizon: int = 1,
    threshold: float = 0.01
) -> pd.Series:
    """
    Create target variable for classification

    Args:
        df: DataFrame with price data
        horizon: Lookahead periods
        threshold: Minimum change to classify as up/down

    Returns:
        Target series (0=down, 1=hold, 2=up)
    """
    # Future return
    future_return = df['close'].shift(-horizon) / df['close'] - 1

    # Classify
    target = pd.Series(1, index=df.index)  # Default: hold
    target[future_return > threshold] = 2  # Up
    target[future_return < -threshold] = 0  # Down

    return target


def create_regression_target(
    df: pd.DataFrame,
    horizon: int = 1
) -> pd.Series:
    """
    Create target variable for regression

    Args:
        df: DataFrame with price data
        horizon: Lookahead periods

    Returns:
        Target series (future return)
    """
    future_return = df['close'].shift(-horizon) / df['close'] - 1
    return future_return
