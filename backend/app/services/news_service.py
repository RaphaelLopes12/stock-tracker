"""Servico para buscar noticias do mercado financeiro."""

import asyncio
import feedparser
import httpx
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

# RSS feeds de noticias financeiras brasileiras
RSS_FEEDS = [
    {
        "name": "InfoMoney",
        "url": "https://www.infomoney.com.br/feed/",
        "category": "mercado"
    },
    {
        "name": "InfoMoney Mercados",
        "url": "https://www.infomoney.com.br/mercados/feed/",
        "category": "mercado"
    },
    {
        "name": "Valor Economico",
        "url": "https://valor.globo.com/rss/valor",
        "category": "economia"
    },
    {
        "name": "E-Investidor",
        "url": "https://einvestidor.estadao.com.br/feed/",
        "category": "investimentos"
    },
    {
        "name": "Money Times",
        "url": "https://www.moneytimes.com.br/feed/",
        "category": "mercado"
    },
    {
        "name": "Seu Dinheiro",
        "url": "https://www.seudinheiro.com/feed/",
        "category": "investimentos"
    },
]


def _parse_feed(feed_info: dict) -> list[dict]:
    """Parse um feed RSS e retorna lista de noticias."""
    try:
        feed = feedparser.parse(feed_info["url"])
        news = []

        for entry in feed.entries[:10]:  # Limitar a 10 por fonte
            # Extrair imagem se disponivel
            image = None
            if hasattr(entry, 'media_content') and entry.media_content:
                image = entry.media_content[0].get('url')
            elif hasattr(entry, 'enclosures') and entry.enclosures:
                for enc in entry.enclosures:
                    if enc.get('type', '').startswith('image'):
                        image = enc.get('href')
                        break

            # Parse da data
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6]).isoformat()

            # Limpar descricao
            description = ""
            if hasattr(entry, 'summary'):
                soup = BeautifulSoup(entry.summary, 'html.parser')
                description = soup.get_text()[:200] + "..." if len(soup.get_text()) > 200 else soup.get_text()

            news.append({
                "title": entry.title,
                "description": description,
                "url": entry.link,
                "image": image,
                "source": feed_info["name"],
                "category": feed_info["category"],
                "published": published,
            })

        return news
    except Exception as e:
        print(f"Error parsing feed {feed_info['name']}: {e}")
        return []


async def get_market_news(limit: int = 20) -> list[dict]:
    """Busca noticias de todas as fontes em paralelo."""
    loop = asyncio.get_event_loop()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            loop.run_in_executor(executor, _parse_feed, feed)
            for feed in RSS_FEEDS
        ]

        results = await asyncio.gather(*futures)

    # Combinar e ordenar por data
    all_news = []
    for news_list in results:
        all_news.extend(news_list)

    # Ordenar por data (mais recentes primeiro)
    all_news.sort(key=lambda x: x.get('published') or '', reverse=True)

    return all_news[:limit]


async def get_stock_news(ticker: str, limit: int = 5) -> list[dict]:
    """Busca noticias especificas de uma acao."""
    all_news = await get_market_news(100)

    ticker_upper = ticker.upper()
    ticker_base = ticker_upper.replace("3", "").replace("4", "").replace("11", "")

    # Mapeamento expandido de empresas para keywords
    company_names = {
        # Petroleo e Gas
        "PETR": ["petrobras", "petr4", "petr3", "pre-sal", "pré-sal", "gasolina", "diesel"],
        "PRIO": ["prio", "petrorio", "prio3"],
        "CSAN": ["cosan", "csan3", "raizen"],
        "UGPA": ["ultrapar", "ipiranga", "ugpa3"],
        # Mineracao
        "VALE": ["vale", "vale3", "minerio", "minério", "mineracao", "mineração"],
        "CSNA": ["csn", "csna3", "siderurgia", "companhia siderurgica"],
        "GGBR": ["gerdau", "ggbr4", "ggbr3"],
        "USIM": ["usiminas", "usim5", "usim3"],
        # Bancos
        "ITUB": ["itau", "itaú", "itub4", "itub3", "banco itau"],
        "BBDC": ["bradesco", "bbdc4", "bbdc3", "banco bradesco"],
        "BBAS": ["banco do brasil", "bb", "bbas3"],
        "SANB": ["santander", "sanb11", "banco santander"],
        "BBSE": ["bb seguridade", "bbse3", "seguros"],
        "ITSA": ["itausa", "itsa4", "itsa3"],
        # Energia
        "ELET": ["eletrobras", "elet3", "elet6", "energia eletrica", "energia elétrica"],
        "CPFE": ["cpfl", "cpfe3", "energia"],
        "ENGI": ["energisa", "engi11"],
        "EQTL": ["equatorial", "eqtl3"],
        "TAEE": ["taesa", "taee11", "transmissao", "transmissão"],
        "CMIG": ["cemig", "cmig4", "cmig3"],
        "ENBR": ["energias brasil", "enbr3"],
        # Varejo
        "MGLU": ["magazine luiza", "magalu", "mglu3"],
        "LREN": ["lojas renner", "renner", "lren3"],
        "AMER": ["americanas", "amer3", "lojas americanas"],
        "VIIA": ["via", "viia3", "casas bahia", "ponto frio"],
        "PETZ": ["petz", "petz3"],
        "AZZA": ["arezzo", "azza3"],
        # Alimentos e Bebidas
        "ABEV": ["ambev", "abev3", "cerveja", "brahma", "skol"],
        "JBSS": ["jbs", "jbss3", "carne", "frigorifico", "frigorífico"],
        "BRFS": ["brf", "brfs3", "sadia", "perdigao", "perdigão"],
        "MDIA": ["m. dias", "mdia3"],
        "BEEF": ["minerva", "beef3"],
        # Saude
        "HAPV": ["hapvida", "hapv3", "plano de saude", "plano de saúde"],
        "RDOR": ["rede dor", "rdor3", "hospital"],
        "FLRY": ["fleury", "flry3", "exames", "laboratorio", "laboratório"],
        "QUAL": ["qualicorp", "qual3"],
        # Construcao
        "CYRE": ["cyrela", "cyre3", "imoveis", "imóveis", "construcao", "construção"],
        "MRVE": ["mrv", "mrve3"],
        "EZTC": ["eztec", "eztc3"],
        "EVEN": ["even", "even3"],
        # Tecnologia
        "TOTS": ["totvs", "tots3", "software"],
        "LWSA": ["locaweb", "lwsa3"],
        "POSI": ["positivo", "posi3"],
        # Industria
        "WEGE": ["weg", "wege3", "motores"],
        "EMBR": ["embraer", "embr3", "aviacao", "aviação", "aviao", "avião"],
        "RENT": ["localiza", "rent3", "aluguel de carros"],
        "RAIL": ["rumo", "rail3", "ferrovia"],
        # Telecomunicacoes
        "VIVT": ["vivo", "vivt3", "telefonica", "telefônica"],
        "TIMS": ["tim", "tims3"],
        # Papel e Celulose
        "SUZB": ["suzano", "suzb3", "celulose", "papel"],
        "KLBN": ["klabin", "klbn11", "klbn4"],
        # Outros
        "B3SA": ["b3", "b3sa3", "bolsa", "bovespa", "ibovespa"],
        "NTCO": ["natura", "ntco3", "cosmeticos", "cosméticos"],
        "RADL": ["raia drogasil", "radl3", "farmacia", "farmácia"],
        "SBSP": ["sabesp", "sbsp3", "saneamento"],
        "CPLE": ["copel", "cple6"],
    }

    # Encontrar keywords baseado no ticker base
    keywords = company_names.get(ticker_base, [])

    # Adicionar o ticker como keyword
    keywords.extend([ticker_upper.lower(), ticker_base.lower()])

    # Remover duplicatas
    keywords = list(set(keywords))

    filtered = []
    for news in all_news:
        text = f"{news['title']} {news['description']}".lower()
        if any(kw in text for kw in keywords):
            filtered.append(news)
            if len(filtered) >= limit:
                break

    # Se nao encontrou noticias especificas, buscar noticias gerais do mercado
    if not filtered:
        market_keywords = ["ibovespa", "b3", "bolsa", "acoes", "ações", "mercado", "investidor"]
        for news in all_news:
            text = f"{news['title']} {news['description']}".lower()
            if any(kw in text for kw in market_keywords):
                news["is_market_news"] = True  # Marcar como noticia geral
                filtered.append(news)
                if len(filtered) >= limit:
                    break

    return filtered


async def get_market_summary() -> dict:
    """Retorna resumo do mercado (indices)."""
    # Buscar dados dos principais indices
    try:
        import yfinance as yf

        indices = {
            "^BVSP": "Ibovespa",
            "^GSPC": "S&P 500",
            "^DJI": "Dow Jones",
            "BRL=X": "Dolar",
        }

        summary = []
        for symbol, name in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                price = info.get("regularMarketPrice")
                prev_close = info.get("regularMarketPreviousClose")

                if price and prev_close:
                    change = price - prev_close
                    change_pct = (change / prev_close) * 100

                    summary.append({
                        "symbol": symbol,
                        "name": name,
                        "price": round(price, 2),
                        "change": round(change, 2),
                        "change_percent": round(change_pct, 2),
                    })
            except Exception:
                pass

        return {"indices": summary, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        print(f"Error fetching market summary: {e}")
        return {"indices": [], "timestamp": datetime.now().isoformat()}
