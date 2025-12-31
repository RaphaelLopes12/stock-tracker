from datetime import datetime

import yfinance as yf

from app.collectors.base import BaseCollector


class PriceCollector(BaseCollector):
    """Collector for stock prices using yfinance."""

    name = "price"

    def __init__(self, tickers: list[str]):
        super().__init__()
        # Add .SA suffix for Brazilian stocks
        self.tickers = [f"{t}.SA" if not t.endswith(".SA") else t for t in tickers]

    async def collect(self) -> dict:
        """Collect current prices for all tickers."""
        results = {}

        for ticker in self.tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info

                # Get basic price info
                results[ticker.replace(".SA", "")] = {
                    "price": info.get("regularMarketPrice"),
                    "open": info.get("regularMarketOpen"),
                    "high": info.get("regularMarketDayHigh"),
                    "low": info.get("regularMarketDayLow"),
                    "volume": info.get("regularMarketVolume"),
                    "previous_close": info.get("regularMarketPreviousClose"),
                    "change": info.get("regularMarketChange"),
                    "change_percent": info.get("regularMarketChangePercent"),
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                self.errors.append(f"{ticker}: {str(e)}")
                results[ticker.replace(".SA", "")] = {"error": str(e)}

        return {
            "collected": len([r for r in results.values() if "error" not in r]),
            "errors": len(self.errors),
            "prices": results,
        }

    async def get_history(self, ticker: str, period: str = "1mo") -> dict:
        """Get historical prices for a ticker."""
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        stock = yf.Ticker(ticker_sa)
        hist = stock.history(period=period)

        return {
            "ticker": ticker,
            "period": period,
            "data": [
                {
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                }
                for idx, row in hist.iterrows()
            ],
        }
