import asyncio
import json
from datetime import datetime, timedelta

import yfinance as yf
import redis

from app.core.config import settings


_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
            _redis_client.ping()
        except Exception as e:
            print(f"Redis not available: {e}")
            _redis_client = False
    return _redis_client if _redis_client else None


def _get_cached_benchmark(key: str) -> dict | None:
    r = _get_redis()
    if not r:
        return None
    try:
        data = r.get(f"benchmark:{key}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached_benchmark(key: str, data: dict, ttl: int = 3600) -> None:
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(f"benchmark:{key}", ttl, json.dumps(data))
    except Exception:
        pass


def _fetch_ibovespa_performance(start_date: datetime, end_date: datetime) -> float | None:
    try:
        ibov = yf.Ticker("^BVSP")
        hist = ibov.history(start=start_date, end=end_date)

        if hist.empty or len(hist) < 2:
            return None

        first_price = float(hist['Close'].iloc[0])
        last_price = float(hist['Close'].iloc[-1])

        if first_price and first_price > 0:
            return float(((last_price / first_price) - 1) * 100)
        return None
    except Exception as e:
        print(f"Error fetching Ibovespa: {e}")
        return None


def _get_cdi_annual_rate() -> float:
    return 13.25


def _calculate_cdi_return(start_date: datetime, end_date: datetime) -> float:
    annual_rate = _get_cdi_annual_rate()
    days = (end_date - start_date).days
    if days <= 0:
        return 0.0

    business_days = int(days * 0.7)
    daily_rate = ((1 + annual_rate / 100) ** (1 / 252)) - 1
    period_return = ((1 + daily_rate) ** business_days - 1) * 100

    return round(period_return, 2)


async def get_benchmark_comparison(
    portfolio_return: float,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    period_days: int = 365,
) -> dict:
    if end_date is None:
        end_date = datetime.now()
    if start_date is None:
        start_date = end_date - timedelta(days=period_days)

    cache_key = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
    cached = _get_cached_benchmark(cache_key)

    if cached:
        ibov_return = cached.get("ibov_return")
        cdi_return = cached.get("cdi_return")
    else:
        loop = asyncio.get_event_loop()
        ibov_return = await loop.run_in_executor(
            None, _fetch_ibovespa_performance, start_date, end_date
        )
        cdi_return = _calculate_cdi_return(start_date, end_date)

        _set_cached_benchmark(cache_key, {
            "ibov_return": ibov_return,
            "cdi_return": cdi_return,
        })

    vs_ibov = None
    vs_cdi = None
    beats_ibov = None
    beats_cdi = None

    if ibov_return is not None:
        ibov_return = float(ibov_return)
        vs_ibov = float(round(portfolio_return - ibov_return, 2))
        beats_ibov = bool(portfolio_return > ibov_return)

    if cdi_return is not None:
        cdi_return = float(cdi_return)
        vs_cdi = float(round(portfolio_return - cdi_return, 2))
        beats_cdi = bool(portfolio_return > cdi_return)

    return {
        "period": {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days": int((end_date - start_date).days),
        },
        "portfolio": {
            "return": float(round(portfolio_return, 2)),
        },
        "benchmarks": {
            "ibovespa": {
                "return": float(round(ibov_return, 2)) if ibov_return is not None else None,
                "vs_portfolio": vs_ibov,
                "beats": beats_ibov,
            },
            "cdi": {
                "return": float(round(cdi_return, 2)) if cdi_return is not None else None,
                "annual_rate": float(_get_cdi_annual_rate()),
                "vs_portfolio": vs_cdi,
                "beats": beats_cdi,
            },
        },
        "summary": {
            "best_investment": _get_best_investment(portfolio_return, ibov_return, cdi_return),
        }
    }


def _get_best_investment(portfolio: float, ibov: float | None, cdi: float | None) -> str:
    options = {"portfolio": portfolio}
    if ibov is not None:
        options["ibovespa"] = ibov
    if cdi is not None:
        options["cdi"] = cdi

    best = max(options, key=lambda x: options[x])
    return best
