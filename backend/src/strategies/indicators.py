import numpy as np
import pandas as pd
from typing import List, Dict, Tuple
from decimal import Decimal


class TechnicalIndicators:
    """Technical analysis indicators for trading strategies"""

    @staticmethod
    def sma(data: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return data.rolling(window=period).mean()

    @staticmethod
    def ema(data: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return data.ewm(span=period, adjust=False).mean()

    @staticmethod
    def rsi(data: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def macd(
        data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)

        Returns:
            macd_line, signal_line, histogram
        """
        exp1 = data.ewm(span=fast, adjust=False).mean()
        exp2 = data.ewm(span=slow, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def bollinger_bands(
        data: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Returns:
            upper_band, middle_band, lower_band
        """
        middle_band = data.rolling(window=period).mean()
        std = data.rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        return upper_band, middle_band, lower_band

    @staticmethod
    def stochastic_oscillator(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Returns:
            %K, %D
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=3).mean()

        return k_percent, d_percent

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range (Volatility indicator)"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = pd.Series(true_range).rolling(window=period).mean()

        return atr

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        return (np.sign(close.diff()) * volume).fillna(0).cumsum()

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average Directional Index (Trend strength)"""
        plus_dm = high.diff()
        minus_dm = -low.diff()

        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0

        tr = TechnicalIndicators.atr(high, low, close, period)

        plus_di = 100 * (plus_dm.rolling(window=period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / tr)

        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(window=period).mean()

        return adx

    @staticmethod
    def ichimoku_cloud(
        high: pd.Series, low: pd.Series, close: pd.Series
    ) -> Dict[str, pd.Series]:
        """
        Ichimoku Cloud

        Returns:
            Dict with tenkan_sen, kijun_sen, senkou_span_a, senkou_span_b, chikou_span
        """
        # Conversion Line (Tenkan-sen)
        nine_period_high = high.rolling(window=9).max()
        nine_period_low = low.rolling(window=9).min()
        tenkan_sen = (nine_period_high + nine_period_low) / 2

        # Base Line (Kijun-sen)
        period26_high = high.rolling(window=26).max()
        period26_low = low.rolling(window=26).min()
        kijun_sen = (period26_high + period26_low) / 2

        # Leading Span A (Senkou Span A)
        senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(26)

        # Leading Span B (Senkou Span B)
        period52_high = high.rolling(window=52).max()
        period52_low = low.rolling(window=52).min()
        senkou_span_b = ((period52_high + period52_low) / 2).shift(26)

        # Lagging Span (Chikou Span)
        chikou_span = close.shift(-26)

        return {
            "tenkan_sen": tenkan_sen,
            "kijun_sen": kijun_sen,
            "senkou_span_a": senkou_span_a,
            "senkou_span_b": senkou_span_b,
            "chikou_span": chikou_span,
        }

    @staticmethod
    def fibonacci_retracement(high: float, low: float) -> Dict[str, float]:
        """
        Calculate Fibonacci retracement levels

        Args:
            high: Period high
            low: Period low

        Returns:
            Dict with Fibonacci levels
        """
        diff = high - low
        return {
            "level_0": high,
            "level_236": high - 0.236 * diff,
            "level_382": high - 0.382 * diff,
            "level_500": high - 0.500 * diff,
            "level_618": high - 0.618 * diff,
            "level_786": high - 0.786 * diff,
            "level_100": low,
        }

    @staticmethod
    def pivot_points(high: float, low: float, close: float) -> Dict[str, float]:
        """
        Calculate pivot points

        Args:
            high: Previous period high
            low: Previous period low
            close: Previous period close

        Returns:
            Dict with pivot point and support/resistance levels
        """
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)
        r3 = high + 2 * (pivot - low)
        s3 = low - 2 * (high - pivot)

        return {
            "pivot": pivot,
            "r1": r1,
            "r2": r2,
            "r3": r3,
            "s1": s1,
            "s2": s2,
            "s3": s3,
        }

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate all indicators for a DataFrame with OHLCV data

        Args:
            df: DataFrame with columns: open, high, low, close, volume

        Returns:
            DataFrame with all indicators added
        """
        df = df.copy()

        # Moving Averages
        df["sma_20"] = TechnicalIndicators.sma(df["close"], 20)
        df["sma_50"] = TechnicalIndicators.sma(df["close"], 50)
        df["sma_200"] = TechnicalIndicators.sma(df["close"], 200)
        df["ema_12"] = TechnicalIndicators.ema(df["close"], 12)
        df["ema_26"] = TechnicalIndicators.ema(df["close"], 26)

        # RSI
        df["rsi"] = TechnicalIndicators.rsi(df["close"])

        # MACD
        macd, signal, hist = TechnicalIndicators.macd(df["close"])
        df["macd"] = macd
        df["macd_signal"] = signal
        df["macd_histogram"] = hist

        # Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(df["close"])
        df["bb_upper"] = upper
        df["bb_middle"] = middle
        df["bb_lower"] = lower

        # Stochastic
        k, d = TechnicalIndicators.stochastic_oscillator(df["high"], df["low"], df["close"])
        df["stoch_k"] = k
        df["stoch_d"] = d

        # ATR
        df["atr"] = TechnicalIndicators.atr(df["high"], df["low"], df["close"])

        # OBV
        df["obv"] = TechnicalIndicators.obv(df["close"], df["volume"])

        # ADX
        df["adx"] = TechnicalIndicators.adx(df["high"], df["low"], df["close"])

        # Ichimoku
        ichimoku = TechnicalIndicators.ichimoku_cloud(df["high"], df["low"], df["close"])
        for key, value in ichimoku.items():
            df[f"ichimoku_{key}"] = value

        return df
