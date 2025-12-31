"""Serviço para buscar cotações em tempo real."""

import asyncio
import json
import yfinance as yf
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import redis

from app.core.config import settings

# Redis client para cache
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


def _get_cached_quote(ticker: str) -> dict | None:
    """Busca cotação do cache Redis."""
    r = _get_redis()
    if not r:
        return None
    try:
        data = r.get(f"quote:{ticker}")
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached_quote(ticker: str, quote: dict, ttl: int = 300) -> None:
    """Salva cotação no cache Redis (TTL padrão 5 minutos)."""
    r = _get_redis()
    if not r:
        return
    try:
        r.setex(f"quote:{ticker}", ttl, json.dumps(quote))
    except Exception:
        pass


def _fetch_quote_sync(ticker: str, use_cache: bool = True) -> dict | None:
    """Busca cotação de forma síncrona (para usar com ThreadPoolExecutor)."""
    # Tentar cache primeiro
    if use_cache:
        cached = _get_cached_quote(ticker)
        if cached:
            cached["from_cache"] = True
            return cached

    try:
        ticker_sa = f"{ticker}.SA" if not ticker.endswith(".SA") else ticker
        stock = yf.Ticker(ticker_sa)
        info = stock.info

        if not info or "regularMarketPrice" not in info:
            return None

        price = info.get("regularMarketPrice")
        previous_close = info.get("regularMarketPreviousClose")

        change = None
        change_percent = None
        if price and previous_close:
            change = price - previous_close
            change_percent = (change / previous_close) * 100

        # Dividend yield vem como decimal (ex: 0.05 = 5%)
        raw_dy = info.get("dividendYield")
        dividend_yield = raw_dy * 100 if raw_dy and raw_dy < 1 else raw_dy

        quote = {
            "ticker": ticker.replace(".SA", ""),
            "price": price,
            "open": info.get("regularMarketOpen"),
            "high": info.get("regularMarketDayHigh"),
            "low": info.get("regularMarketDayLow"),
            "volume": info.get("regularMarketVolume"),
            "previous_close": previous_close,
            "change": round(change, 2) if change else None,
            "change_percent": round(change_percent, 2) if change_percent else None,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "dividend_yield": round(dividend_yield, 2) if dividend_yield else None,
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "timestamp": datetime.now().isoformat(),
        }

        # Salvar no cache (5 minutos durante horário de pregão)
        _set_cached_quote(ticker, quote, ttl=300)

        return quote
    except Exception as e:
        print(f"Error fetching quote for {ticker}: {e}")
        return None


async def get_quote(ticker: str) -> dict | None:
    """Busca cotação atual de uma ação."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _fetch_quote_sync, ticker)


async def get_quotes_batch(tickers: list[str]) -> dict[str, dict]:
    """Busca cotações de múltiplas ações em paralelo."""
    results = {}

    # Buscar em paralelo usando ThreadPoolExecutor
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            ticker: loop.run_in_executor(executor, _fetch_quote_sync, ticker)
            for ticker in tickers
        }

        for ticker, future in futures.items():
            try:
                quote = await future
                if quote:
                    results[ticker] = quote
            except Exception as e:
                print(f"Error fetching {ticker}: {e}")

    return results


def analyze_stock(quote: dict, fundamentals: dict | None = None) -> dict:
    """Análise básica se compensa comprar."""
    analysis = {
        "ticker": quote["ticker"],
        "price": quote["price"],
        "signals": [],
        "score": 0,  # -100 a 100
    }

    # Análise de momento (preço vs 52 semanas)
    if quote.get("fifty_two_week_high") and quote.get("fifty_two_week_low"):
        high = quote["fifty_two_week_high"]
        low = quote["fifty_two_week_low"]
        price = quote["price"]
        position = (price - low) / (high - low) if high != low else 0.5

        if position < 0.3:
            analysis["signals"].append({
                "type": "positive",
                "message": f"Próximo da mínima de 52 semanas (R$ {low:.2f})"
            })
            analysis["score"] += 20
        elif position > 0.8:
            analysis["signals"].append({
                "type": "warning",
                "message": f"Próximo da máxima de 52 semanas (R$ {high:.2f})"
            })
            analysis["score"] -= 10

    # Análise de P/L
    if quote.get("pe_ratio"):
        pe = quote["pe_ratio"]
        if pe < 8:
            analysis["signals"].append({
                "type": "positive",
                "message": f"P/L baixo ({pe:.1f}) - possível oportunidade"
            })
            analysis["score"] += 25
        elif pe < 15:
            analysis["signals"].append({
                "type": "neutral",
                "message": f"P/L razoável ({pe:.1f})"
            })
            analysis["score"] += 10
        elif pe > 25:
            analysis["signals"].append({
                "type": "warning",
                "message": f"P/L alto ({pe:.1f}) - pode estar cara"
            })
            analysis["score"] -= 15

    # Análise de Dividend Yield
    if quote.get("dividend_yield"):
        dy = quote["dividend_yield"]
        if dy > 6:
            analysis["signals"].append({
                "type": "positive",
                "message": f"Dividend Yield atrativo ({dy:.1f}%)"
            })
            analysis["score"] += 20
        elif dy > 3:
            analysis["signals"].append({
                "type": "neutral",
                "message": f"Dividend Yield razoável ({dy:.1f}%)"
            })
            analysis["score"] += 5

    # Análise de variação do dia
    if quote.get("change_percent"):
        change = quote["change_percent"]
        if change < -3:
            analysis["signals"].append({
                "type": "info",
                "message": f"Queda de {abs(change):.1f}% hoje - verificar motivo"
            })
        elif change > 3:
            analysis["signals"].append({
                "type": "info",
                "message": f"Alta de {change:.1f}% hoje"
            })

    # Conclusão
    if analysis["score"] >= 30:
        analysis["recommendation"] = "Pode ser interessante comprar"
        analysis["recommendation_type"] = "buy"
    elif analysis["score"] <= -20:
        analysis["recommendation"] = "Cautela - avaliar melhor"
        analysis["recommendation_type"] = "hold"
    else:
        analysis["recommendation"] = "Neutro - acompanhar"
        analysis["recommendation_type"] = "neutral"

    return analysis
