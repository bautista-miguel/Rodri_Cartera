from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pandas as pd
import yfinance as yf


@dataclass
class Quote:
    symbol: str
    price: Optional[float]
    daily_change: Optional[float]
    timestamp: Optional[pd.Timestamp]
    error: Optional[str] = None


def _close_series(data: pd.DataFrame) -> pd.Series:
    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna().astype(float)


def get_quote(symbol: str) -> Quote:
    """Get latest close and change versus previous close from Yahoo Finance."""
    try:
        hist = yf.download(
            symbol,
            period="10d",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if hist is None or hist.empty:
            return Quote(symbol, None, None, None, "Sin datos en Yahoo Finance")

        close = _close_series(hist)
        if close.empty:
            return Quote(symbol, None, None, None, "Historial sin precios de cierre")

        price = float(close.iloc[-1])
        daily_change = None
        if len(close) >= 2 and float(close.iloc[-2]) != 0:
            daily_change = price / float(close.iloc[-2]) - 1
        timestamp = pd.Timestamp(close.index[-1])
        return Quote(symbol, price, daily_change, timestamp)
    except Exception as exc:  # Yahoo can fail temporarily
        return Quote(symbol, None, None, None, str(exc))


def get_history(symbol: str, start: str) -> pd.Series:
    """Download daily closing prices from a chosen start date."""
    try:
        hist = yf.download(
            symbol,
            start=start,
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if hist is None or hist.empty:
            return pd.Series(dtype=float, name="Close")
        close = _close_series(hist)
        close.name = "Close"
        return close
    except Exception:
        return pd.Series(dtype=float, name="Close")
