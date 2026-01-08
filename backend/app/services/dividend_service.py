"""Serviço para buscar agenda de dividendos."""

import asyncio
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

import yfinance as yf


def _fetch_dividends_sync(ticker: str) -> dict | None:
    """Busca dividendos de forma síncrona."""
    try:
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        stock = yf.Ticker(ticker_sa)

        calendar = None
        try:
            cal = stock.calendar
            if cal is not None and not cal.empty:
                calendar = {
                    "ex_date": cal.get("Ex-Dividend Date"),
                    "dividend_date": cal.get("Dividend Date"),
                }
        except Exception:
            pass

        dividends_history = []
        try:
            divs = stock.dividends
            if divs is not None and len(divs) > 0:
                one_year_ago = datetime.now() - timedelta(days=365)
                recent_divs = divs[divs.index >= one_year_ago.strftime("%Y-%m-%d")]

                for date_idx, value in recent_divs.items():
                    dividends_history.append({
                        "date": date_idx.strftime("%Y-%m-%d"),
                        "value": float(value),
                    })
        except Exception:
            pass

        info = stock.info or {}

        return {
            "ticker": ticker.replace(".SA", "").upper(),
            "name": info.get("shortName") or info.get("longName"),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
            "dividend_rate": info.get("dividendRate"),
            "ex_dividend_date": info.get("exDividendDate"),
            "calendar": calendar,
            "history": dividends_history,
        }
    except Exception as e:
        print(f"Error fetching dividends for {ticker}: {e}")
        return None


async def get_dividend_info(ticker: str) -> dict | None:
    """Busca informações de dividendos de uma ação."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_dividends_sync, ticker)


async def get_dividends_calendar(tickers: list[str]) -> list[dict]:
    """Busca agenda de dividendos de múltiplas ações."""
    results = []

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            ticker: loop.run_in_executor(executor, _fetch_dividends_sync, ticker)
            for ticker in tickers
        }

        for ticker, future in futures.items():
            try:
                data = await future
                if data:
                    results.append(data)
            except Exception as e:
                print(f"Error fetching dividends for {ticker}: {e}")

    return results


def format_upcoming_dividends(dividend_data: list[dict]) -> list[dict]:
    """Formata lista de próximos dividendos ordenados por data."""
    upcoming = []
    today = datetime.now().date()

    for stock in dividend_data:
        if not stock:
            continue

        ex_date = stock.get("ex_dividend_date")
        if ex_date:
            try:
                if isinstance(ex_date, int):
                    ex_date_obj = datetime.fromtimestamp(ex_date).date()
                else:
                    ex_date_obj = datetime.strptime(str(ex_date), "%Y-%m-%d").date()

                if ex_date_obj >= today:
                    upcoming.append({
                        "ticker": stock["ticker"],
                        "name": stock.get("name"),
                        "ex_date": ex_date_obj.isoformat(),
                        "dividend_yield": stock.get("dividend_yield"),
                        "dividend_rate": stock.get("dividend_rate"),
                        "type": "upcoming",
                    })
            except Exception:
                pass

        for div in stock.get("history", [])[-3:]:
            try:
                div_date = datetime.strptime(div["date"], "%Y-%m-%d").date()
                if div_date >= today - timedelta(days=30) and div_date <= today:
                    upcoming.append({
                        "ticker": stock["ticker"],
                        "name": stock.get("name"),
                        "ex_date": div["date"],
                        "value_per_share": div["value"],
                        "dividend_yield": stock.get("dividend_yield"),
                        "type": "recent",
                    })
            except Exception:
                pass

    upcoming.sort(key=lambda x: x.get("ex_date", "9999-12-31"))
    return upcoming
