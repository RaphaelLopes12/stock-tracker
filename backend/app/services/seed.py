"""Seed de ações da B3."""

# Principais ações da B3 por setor
STOCKS_B3 = [
    # Bancos
    {"ticker": "ITUB4", "name": "Itaú Unibanco", "sector": "Financeiro", "subsector": "Bancos"},
    {"ticker": "BBDC4", "name": "Bradesco", "sector": "Financeiro", "subsector": "Bancos"},
    {"ticker": "BBAS3", "name": "Banco do Brasil", "sector": "Financeiro", "subsector": "Bancos"},
    {"ticker": "SANB11", "name": "Santander Brasil", "sector": "Financeiro", "subsector": "Bancos"},
    {"ticker": "ITSA4", "name": "Itaúsa", "sector": "Financeiro", "subsector": "Holdings"},

    # Energia
    {"ticker": "PETR4", "name": "Petrobras PN", "sector": "Petróleo e Gás", "subsector": "Exploração"},
    {"ticker": "PETR3", "name": "Petrobras ON", "sector": "Petróleo e Gás", "subsector": "Exploração"},
    {"ticker": "PRIO3", "name": "PRIO", "sector": "Petróleo e Gás", "subsector": "Exploração"},
    {"ticker": "CSAN3", "name": "Cosan", "sector": "Petróleo e Gás", "subsector": "Distribuição"},
    {"ticker": "UGPA3", "name": "Ultrapar", "sector": "Petróleo e Gás", "subsector": "Distribuição"},

    # Elétricas
    {"ticker": "ELET3", "name": "Eletrobras ON", "sector": "Energia Elétrica", "subsector": "Geração"},
    {"ticker": "ELET6", "name": "Eletrobras PNB", "sector": "Energia Elétrica", "subsector": "Geração"},
    {"ticker": "EGIE3", "name": "Engie Brasil", "sector": "Energia Elétrica", "subsector": "Geração"},
    {"ticker": "EQTL3", "name": "Equatorial", "sector": "Energia Elétrica", "subsector": "Distribuição"},
    {"ticker": "CPFE3", "name": "CPFL Energia", "sector": "Energia Elétrica", "subsector": "Distribuição"},
    {"ticker": "TAEE11", "name": "Taesa", "sector": "Energia Elétrica", "subsector": "Transmissão"},
    {"ticker": "CMIG4", "name": "Cemig", "sector": "Energia Elétrica", "subsector": "Integradas"},

    # Mineração e Siderurgia
    {"ticker": "VALE3", "name": "Vale", "sector": "Mineração", "subsector": "Minerais Metálicos"},
    {"ticker": "CSNA3", "name": "CSN", "sector": "Siderurgia", "subsector": "Siderurgia"},
    {"ticker": "GGBR4", "name": "Gerdau", "sector": "Siderurgia", "subsector": "Siderurgia"},
    {"ticker": "GOAU4", "name": "Gerdau Metalúrgica", "sector": "Siderurgia", "subsector": "Siderurgia"},
    {"ticker": "USIM5", "name": "Usiminas", "sector": "Siderurgia", "subsector": "Siderurgia"},

    # Consumo
    {"ticker": "ABEV3", "name": "Ambev", "sector": "Consumo", "subsector": "Bebidas"},
    {"ticker": "MGLU3", "name": "Magazine Luiza", "sector": "Consumo", "subsector": "Varejo"},
    {"ticker": "LREN3", "name": "Lojas Renner", "sector": "Consumo", "subsector": "Varejo"},
    {"ticker": "PETZ3", "name": "Petz", "sector": "Consumo", "subsector": "Varejo"},
    {"ticker": "ARZZ3", "name": "Arezzo", "sector": "Consumo", "subsector": "Calçados"},
    {"ticker": "NTCO3", "name": "Natura", "sector": "Consumo", "subsector": "Cosméticos"},

    # Indústria
    {"ticker": "WEGE3", "name": "WEG", "sector": "Bens Industriais", "subsector": "Máquinas"},
    {"ticker": "EMBR3", "name": "Embraer", "sector": "Bens Industriais", "subsector": "Aeronáutica"},
    {"ticker": "RENT3", "name": "Localiza", "sector": "Bens Industriais", "subsector": "Aluguel Carros"},
    {"ticker": "RAIL3", "name": "Rumo", "sector": "Bens Industriais", "subsector": "Logística"},

    # Saúde
    {"ticker": "RDOR3", "name": "Rede D'Or", "sector": "Saúde", "subsector": "Hospitais"},
    {"ticker": "HAPV3", "name": "Hapvida", "sector": "Saúde", "subsector": "Planos de Saúde"},
    {"ticker": "FLRY3", "name": "Fleury", "sector": "Saúde", "subsector": "Diagnósticos"},
    {"ticker": "RADL3", "name": "RD Saúde (Raia Drogasil)", "sector": "Saúde", "subsector": "Farmácias"},

    # Construção e Imobiliário
    {"ticker": "CYRE3", "name": "Cyrela", "sector": "Construção", "subsector": "Incorporação"},
    {"ticker": "MRVE3", "name": "MRV", "sector": "Construção", "subsector": "Incorporação"},
    {"ticker": "EZTC3", "name": "EZTec", "sector": "Construção", "subsector": "Incorporação"},

    # Telecomunicações
    {"ticker": "VIVT3", "name": "Telefônica Vivo", "sector": "Telecomunicações", "subsector": "Telefonia"},
    {"ticker": "TIMS3", "name": "TIM", "sector": "Telecomunicações", "subsector": "Telefonia"},

    # Saneamento
    {"ticker": "SBSP3", "name": "Sabesp", "sector": "Saneamento", "subsector": "Água e Esgoto"},
    {"ticker": "CSMG3", "name": "Copasa", "sector": "Saneamento", "subsector": "Água e Esgoto"},

    # Seguros
    {"ticker": "BBSE3", "name": "BB Seguridade", "sector": "Financeiro", "subsector": "Seguros"},
    {"ticker": "PSSA3", "name": "Porto Seguro", "sector": "Financeiro", "subsector": "Seguros"},
    {"ticker": "SUZB3", "name": "Suzano", "sector": "Papel e Celulose", "subsector": "Celulose"},
    {"ticker": "KLBN11", "name": "Klabin", "sector": "Papel e Celulose", "subsector": "Celulose"},

    # Alimentos
    {"ticker": "JBSS3", "name": "JBS", "sector": "Alimentos", "subsector": "Carnes"},
    {"ticker": "BRFS3", "name": "BRF", "sector": "Alimentos", "subsector": "Carnes"},
    {"ticker": "BEEF3", "name": "Minerva", "sector": "Alimentos", "subsector": "Carnes"},
    {"ticker": "MDIA3", "name": "M. Dias Branco", "sector": "Alimentos", "subsector": "Alimentos"},

    # Shoppings e FIIs (ações)
    {"ticker": "MULT3", "name": "Multiplan", "sector": "Shoppings", "subsector": "Shoppings"},
    {"ticker": "IGTI11", "name": "Iguatemi", "sector": "Shoppings", "subsector": "Shoppings"},

    # Tecnologia
    {"ticker": "TOTS3", "name": "Totvs", "sector": "Tecnologia", "subsector": "Software"},
    {"ticker": "LWSA3", "name": "Locaweb", "sector": "Tecnologia", "subsector": "Internet"},

    # B3
    {"ticker": "B3SA3", "name": "B3", "sector": "Financeiro", "subsector": "Bolsa"},
]


async def seed_stocks(db) -> int:
    """Popula o banco com as principais ações da B3."""
    from sqlalchemy import select
    from app.models import Stock

    count = 0
    for stock_data in STOCKS_B3:
        # Verifica se já existe
        result = await db.execute(
            select(Stock).where(Stock.ticker == stock_data["ticker"])
        )
        if result.scalar_one_or_none():
            continue

        stock = Stock(**stock_data)
        db.add(stock)
        count += 1

    if count > 0:
        await db.commit()

    return count
