"""
signals.py — Sinyal uretimi (teknik indikator kombinasyonlari)
EMA Cross, RSI Extreme, BB Squeeze + Volume, VWAP Bounce, Momentum Spike
"""
import pandas as pd
import numpy as np
from . import indicators


def ema_cross_signal(df: pd.DataFrame) -> pd.Series:
    """EMA9 > EMA21 cross sinyali."""
    df = indicators.ema(df, periods=[9, 21])
    cross = (df["EMA9"] > df["EMA21"]) & (df["EMA9"].shift(1) <= df["EMA21"].shift(1))
    return cross.astype(int)


def rsi_extreme_signal(df: pd.DataFrame, oversold: float = 30, overbought: float = 70) -> pd.Series:
    """RSI asiri degerlerden donus sinyali."""
    df = indicators.rsi(df)
    # Oversold cikis (bullish) veya overbought donus (bearish)
    oversold_exit = (df["RSI"] > oversold) & (df["RSI"].shift(1) <= oversold)
    return oversold_exit.astype(int)


def bb_squeeze_volume_signal(df: pd.DataFrame) -> pd.Series:
    """Bollinger squeeze + hacim patlamasi kombinasyonu."""
    df = indicators.bollinger(df)
    df = indicators.volume_profile(df)
    squeeze = df["BB_Squeeze"] == True
    volume_spike = df["Vol_ZScore"] > 2.5
    return (squeeze & volume_spike).astype(int)


def vwap_bounce_signal(df: pd.DataFrame) -> pd.Series:
    """Fiyat VWAP yakinindan yukari donus."""
    df = indicators.vwap(df)
    deviation = (df["close"] - df["VWAP"]) / df["VWAP"]
    bounce = (deviation > 0) & (deviation < 0.02) & (df["close"] > df["close"].shift(1))
    return bounce.astype(int)


def momentum_spike_signal(df: pd.DataFrame, threshold: float = 0.02) -> pd.Series:
    """Anlik fiyat sicramasi + hacim patlamasi."""
    df = indicators.volume_profile(df)
    price_change = df["close"].pct_change()
    spike = (price_change > threshold) & (df["Vol_ZScore"] > 2.0)
    return spike.astype(int)


def combined_signal(df: pd.DataFrame) -> pd.Series:
    """
    Tum sinyalleri birlestirir (agirlikli).
    SIGNAL = EMA(0.20) + RSI(0.20) + Hacim(0.20) + BB(0.15) + VWAP(0.15) + MACD(0.10)
    Skor > 70 = STRONG BUY, 55-70 = BUY, 40-55 = WAIT, < 40 = REJECT
    """
    df = indicators.apply_all(df)

    scores = pd.Series(0.0, index=df.index)

    # EMA uyum (EMA9 > EMA21)
    scores += (df["EMA9"] > df["EMA21"]).astype(float) * 20

    # RSI momentum (30-70 arasi optimal)
    rsi_ok = (df["RSI"] >= 45) & (df["RSI"] <= 65)
    scores += rsi_ok.astype(float) * 20

    # Hacim patlamasi (Z > 2.5)
    scores += (df["Vol_ZScore"] > 2.5).astype(float) * 20

    # Bollinger squeeze
    scores += (df["BB_Squeeze"] == True).astype(float) * 15

    # VWAP uzerinde
    vwap_ok = (df["close"] > df["VWAP"]) & ((df["close"] - df["VWAP"]) / df["VWAP"] < 0.02)
    scores += vwap_ok.astype(float) * 15

    # MACD histogram pozitif
    macd_ok = df["MACD_Hist"] > 0
    scores += macd_ok.astype(float) * 10

    df["Signal_Score"] = scores
    df["Signal"] = np.where(scores >= 70, 2, np.where(scores >= 55, 1, 0))
    return df
