"""Serviço para buscar histórico de preços."""

import asyncio
import yfinance as yf
from datetime import datetime


def _fetch_history_sync(ticker: str, period: str = "6mo") -> list[dict]:
    """Busca histórico de preços de forma síncrona."""
    try:
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        stock = yf.Ticker(ticker_sa)
        hist = stock.history(period=period)

        if hist.empty:
            return []

        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 2) if row["Open"] else None,
                "high": round(row["High"], 2) if row["High"] else None,
                "low": round(row["Low"], 2) if row["Low"] else None,
                "close": round(row["Close"], 2) if row["Close"] else None,
                "volume": int(row["Volume"]) if row["Volume"] else 0,
            })

        return data
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return []


async def get_history(ticker: str, period: str = "6mo") -> list[dict]:
    """Busca histórico de preços de uma ação.

    Períodos válidos: 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_history_sync, ticker, period)
