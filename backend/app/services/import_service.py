"""Serviço inteligente para importação de transações via CSV/Excel."""

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Stock
from app.services.portfolio_service import process_transaction


class ImportFormat(Enum):
    """Formatos de importação suportados."""
    B3_AREA_INVESTIDOR = "b3_area_investidor"
    CLEAR = "clear"
    XP = "xp"
    RICO = "rico"
    GENERIC = "generic"
    CUSTOM = "custom"


@dataclass
class ParsedTransaction:
    """Transação parseada do CSV."""
    ticker: str
    type: str  # 'buy' ou 'sell'
    quantity: int
    price: Decimal
    date: date
    fees: Decimal = Decimal("0")
    notes: Optional[str] = None
    raw_row: Optional[dict] = None


@dataclass
class ImportResult:
    """Resultado da importação."""
    success_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    errors: list[str] = None
    warnings: list[str] = None
    created_stocks: list[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.created_stocks is None:
            self.created_stocks = []


# Mapeamento de colunas para diferentes formatos
COLUMN_MAPPINGS = {
    # Área do Investidor B3
    "b3_area_investidor": {
        "ticker": ["código negociação", "codigo negociacao", "ticker", "código", "codigo", "ativo", "papel"],
        "type": ["tipo movimentação", "tipo movimentacao", "movimentação", "movimentacao", "tipo", "c/v", "operação", "operacao"],
        "quantity": ["quantidade", "qtd", "qtde", "qt"],
        "price": ["preço", "preco", "preço unitário", "preco unitario", "valor unitário", "valor unitario", "preço/ajuste", "preco/ajuste"],
        "date": ["data", "data do negócio", "data do negocio", "data negócio", "data negocio", "data pregão", "data pregao", "data liquidação", "data liquidacao"],
        "fees": ["taxas", "taxa", "corretagem", "emolumentos", "custos"],
    },
    # Clear/Rico/XP (notas de corretagem - formato similar)
    "corretora": {
        "ticker": ["especificação do título", "especificacao do titulo", "título", "titulo", "papel", "ativo", "código", "codigo"],
        "type": ["c/v", "compra/venda", "tipo", "natureza", "operação", "operacao"],
        "quantity": ["quantidade", "qtd", "qtde", "qt", "q"],
        "price": ["preço/ajuste", "preco/ajuste", "preço", "preco", "valor"],
        "date": ["data pregão", "data pregao", "data", "dt pregão", "dt pregao"],
        "fees": ["taxa operacional", "corretagem", "emolumentos", "taxas"],
    },
    # Formato genérico (mais flexível)
    "generic": {
        "ticker": ["ticker", "ativo", "papel", "código", "codigo", "symbol", "stock", "acao", "ação"],
        "type": ["tipo", "type", "operação", "operacao", "c/v", "compra/venda", "operation", "side"],
        "quantity": ["quantidade", "qtd", "qtde", "quantity", "qty", "qt", "q"],
        "price": ["preço", "preco", "price", "valor", "value", "preço unitário", "preco unitario"],
        "date": ["data", "date", "data operação", "data operacao", "dt"],
        "fees": ["taxas", "taxa", "fees", "fee", "corretagem", "custos"],
        "notes": ["observações", "observacoes", "notas", "notes", "obs"],
    },
}

# Mapeamento de valores para tipo de operação
TYPE_MAPPINGS = {
    "buy": ["c", "compra", "buy", "b", "aquisição", "aquisicao", "entrada", "credito", "crédito", "+"],
    "sell": ["v", "venda", "sell", "s", "alienação", "alienacao", "saída", "saida", "débito", "debito", "-"],
}


def normalize_string(s: str) -> str:
    """Normaliza string para comparação (lowercase, sem acentos)."""
    if not s:
        return ""
    s = s.lower().strip()
    # Remover acentos
    replacements = {
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a', 'ä': 'a',
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'í': 'i', 'ì': 'i', 'î': 'i', 'ï': 'i',
        'ó': 'o', 'ò': 'o', 'õ': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ç': 'c', 'ñ': 'n',
    }
    for old, new in replacements.items():
        s = s.replace(old, new)
    return s


def detect_delimiter(content: str) -> str:
    """Detecta o delimitador do CSV (vírgula, ponto-e-vírgula, tab)."""
    first_lines = content.split('\n')[:5]

    delimiters = {',': 0, ';': 0, '\t': 0}
    for line in first_lines:
        for d in delimiters:
            delimiters[d] += line.count(d)

    return max(delimiters, key=delimiters.get)


def find_column(headers: list[str], possible_names: list[str]) -> Optional[int]:
    """Encontra o índice de uma coluna baseado em possíveis nomes."""
    normalized_headers = [normalize_string(h) for h in headers]

    for name in possible_names:
        normalized_name = normalize_string(name)
        for i, header in enumerate(normalized_headers):
            if normalized_name in header or header in normalized_name:
                return i
    return None


def detect_format_and_map_columns(headers: list[str]) -> tuple[ImportFormat, dict[str, int]]:
    """Detecta o formato e mapeia as colunas automaticamente."""
    column_map = {}
    best_format = ImportFormat.GENERIC
    best_score = 0

    # Tentar cada formato
    for format_name, mappings in COLUMN_MAPPINGS.items():
        score = 0
        temp_map = {}

        for field, possible_names in mappings.items():
            idx = find_column(headers, possible_names)
            if idx is not None:
                temp_map[field] = idx
                score += 1

        # Verificar se tem os campos obrigatórios
        required = ["ticker", "type", "quantity", "price", "date"]
        has_required = all(f in temp_map for f in required)

        if has_required and score > best_score:
            best_score = score
            column_map = temp_map
            if format_name == "b3_area_investidor":
                best_format = ImportFormat.B3_AREA_INVESTIDOR
            elif format_name == "corretora":
                best_format = ImportFormat.CLEAR  # Genérico para corretoras
            else:
                best_format = ImportFormat.GENERIC

    return best_format, column_map


def parse_ticker(value: str) -> str:
    """Extrai o ticker limpo de diferentes formatos."""
    if not value:
        return ""

    value = value.strip().upper()

    # Remover sufixos comuns (F para fracionário, ON, PN, etc se estiver separado)
    # Manter WEGE3, PETR4, etc

    # Se tiver espaço, pegar só a primeira parte (ex: "WEGE3 ON NM" -> "WEGE3")
    if ' ' in value:
        value = value.split()[0]

    # Remover F de fracionário no final se existir
    if value.endswith('F') and len(value) > 5:
        value = value[:-1]

    # Validar formato básico de ticker brasileiro (4-6 chars, letras + números)
    if re.match(r'^[A-Z]{4}\d{1,2}$', value):
        return value

    # Tentar extrair ticker de strings mais complexas
    match = re.search(r'([A-Z]{4}\d{1,2})', value)
    if match:
        return match.group(1)

    return value


def parse_type(value: str) -> Optional[str]:
    """Converte o tipo de operação para 'buy' ou 'sell'."""
    if not value:
        return None

    normalized = normalize_string(value)

    for trans_type, keywords in TYPE_MAPPINGS.items():
        for keyword in keywords:
            if keyword in normalized or normalized in keyword:
                return trans_type

    return None


def parse_quantity(value: str) -> Optional[int]:
    """Parse da quantidade (inteiro positivo)."""
    if not value:
        return None

    value = value.strip()
    # Remover separadores de milhar
    value = value.replace('.', '').replace(',', '').replace(' ', '')
    # Remover sinais
    value = value.replace('+', '').replace('-', '')

    try:
        qty = int(float(value))
        return abs(qty) if qty != 0 else None
    except (ValueError, TypeError):
        return None


def parse_price(value: str) -> Optional[Decimal]:
    """Parse do preço (decimal positivo)."""
    if not value:
        return None

    value = value.strip()
    # Remover símbolos de moeda
    value = re.sub(r'[R$\s]', '', value)

    # Detectar formato brasileiro (1.234,56) vs americano (1,234.56)
    if ',' in value and '.' in value:
        # Se vírgula vem depois do ponto, é formato brasileiro
        if value.rfind(',') > value.rfind('.'):
            value = value.replace('.', '').replace(',', '.')
        else:
            value = value.replace(',', '')
    elif ',' in value:
        # Só vírgula - provavelmente decimal brasileiro
        value = value.replace(',', '.')

    try:
        price = Decimal(value)
        return abs(price) if price > 0 else None
    except (InvalidOperation, TypeError):
        return None


def parse_date(value: str) -> Optional[date]:
    """Parse da data em diversos formatos."""
    if not value:
        return None

    value = value.strip()

    # Formatos comuns
    formats = [
        '%d/%m/%Y',      # 31/12/2024
        '%d-%m-%Y',      # 31-12-2024
        '%Y-%m-%d',      # 2024-12-31
        '%d/%m/%y',      # 31/12/24
        '%d-%m-%y',      # 31-12-24
        '%Y/%m/%d',      # 2024/12/31
        '%d.%m.%Y',      # 31.12.2024
        '%m/%d/%Y',      # 12/31/2024 (americano)
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            # Validar se a data faz sentido
            if 1990 <= dt.year <= 2100:
                return dt.date()
        except ValueError:
            continue

    return None


def parse_fees(value: str) -> Decimal:
    """Parse das taxas (opcional)."""
    if not value:
        return Decimal("0")

    price = parse_price(value)
    return price if price else Decimal("0")


def parse_row(row: dict, column_map: dict[str, int], headers: list[str]) -> tuple[Optional[ParsedTransaction], Optional[str]]:
    """Parse uma linha do CSV para uma transação."""
    try:
        # Converter row (pode ser dict ou list)
        if isinstance(row, dict):
            values = list(row.values())
        else:
            values = list(row)

        # Extrair valores baseado no mapeamento
        def get_value(field: str) -> str:
            idx = column_map.get(field)
            if idx is not None and idx < len(values):
                val = values[idx]
                return str(val).strip() if val else ""
            return ""

        # Parse de cada campo
        ticker = parse_ticker(get_value("ticker"))
        if not ticker:
            return None, "Ticker não encontrado ou inválido"

        trans_type = parse_type(get_value("type"))
        if not trans_type:
            return None, f"Tipo de operação não reconhecido para {ticker}"

        quantity = parse_quantity(get_value("quantity"))
        if not quantity:
            return None, f"Quantidade inválida para {ticker}"

        price = parse_price(get_value("price"))
        if not price:
            return None, f"Preço inválido para {ticker}"

        trans_date = parse_date(get_value("date"))
        if not trans_date:
            return None, f"Data inválida para {ticker}"

        fees = parse_fees(get_value("fees"))
        notes = get_value("notes") if "notes" in column_map else None

        return ParsedTransaction(
            ticker=ticker,
            type=trans_type,
            quantity=quantity,
            price=price,
            date=trans_date,
            fees=fees,
            notes=notes,
            raw_row=row,
        ), None

    except Exception as e:
        return None, f"Erro ao processar linha: {str(e)}"


async def get_or_create_stock(db: AsyncSession, ticker: str, created_stocks: list[str]) -> Optional[Stock]:
    """Busca ou cria uma ação pelo ticker."""
    # Buscar existente
    result = await db.execute(select(Stock).where(Stock.ticker == ticker))
    stock = result.scalar_one_or_none()

    if stock:
        return stock

    # Criar nova ação com nome placeholder
    stock = Stock(
        ticker=ticker,
        name=f"{ticker} (Importado)",
        sector=None,
        is_active=True,
    )
    db.add(stock)
    await db.flush()  # Para obter o ID
    created_stocks.append(ticker)

    return stock


async def import_csv(
    db: AsyncSession,
    content: str,
    skip_duplicates: bool = True,
    create_missing_stocks: bool = True,
) -> ImportResult:
    """
    Importa transações de um CSV de forma inteligente.

    Args:
        db: Sessão do banco de dados
        content: Conteúdo do arquivo CSV
        skip_duplicates: Se True, pula transações que parecem duplicadas
        create_missing_stocks: Se True, cria ações que não existem

    Returns:
        ImportResult com estatísticas e erros
    """
    result = ImportResult()

    try:
        # Detectar delimitador
        delimiter = detect_delimiter(content)

        # Parse do CSV
        reader = csv.reader(io.StringIO(content), delimiter=delimiter)
        rows = list(reader)

        if len(rows) < 2:
            result.errors.append("Arquivo vazio ou sem dados")
            return result

        # Primeira linha são os headers
        headers = rows[0]

        # Detectar formato e mapear colunas
        detected_format, column_map = detect_format_and_map_columns(headers)

        if not column_map or len(column_map) < 5:
            result.errors.append(
                "Não foi possível identificar as colunas obrigatórias. "
                "O arquivo deve conter: ticker/ativo, tipo (compra/venda), quantidade, preço e data."
            )
            return result

        result.warnings.append(f"Formato detectado: {detected_format.value}")
        result.warnings.append(f"Colunas mapeadas: {list(column_map.keys())}")

        # Processar cada linha
        processed_transactions = set()  # Para detectar duplicatas

        for i, row in enumerate(rows[1:], start=2):
            # Pular linhas vazias
            if not row or all(not cell.strip() for cell in row):
                continue

            # Parse da linha
            trans, error = parse_row(row, column_map, headers)

            if error:
                result.errors.append(f"Linha {i}: {error}")
                result.error_count += 1
                continue

            if not trans:
                continue

            # Verificar duplicatas
            trans_key = (trans.ticker, trans.type, trans.quantity, str(trans.price), str(trans.date))
            if skip_duplicates and trans_key in processed_transactions:
                result.skipped_count += 1
                result.warnings.append(f"Linha {i}: Transação duplicada ignorada ({trans.ticker})")
                continue

            processed_transactions.add(trans_key)

            # Buscar ou criar a ação
            stock = await get_or_create_stock(db, trans.ticker, result.created_stocks)

            if not stock:
                if not create_missing_stocks:
                    result.errors.append(f"Linha {i}: Ação {trans.ticker} não encontrada")
                    result.error_count += 1
                    continue

            # Processar a transação
            try:
                await process_transaction(
                    db=db,
                    stock=stock,
                    trans_type=trans.type,
                    quantity=trans.quantity,
                    price=trans.price,
                    trans_date=trans.date,
                    fees=trans.fees,
                    notes=trans.notes or f"Importado do CSV",
                )
                result.success_count += 1

            except ValueError as e:
                result.errors.append(f"Linha {i} ({trans.ticker}): {str(e)}")
                result.error_count += 1
            except Exception as e:
                result.errors.append(f"Linha {i}: Erro ao salvar {trans.ticker}: {str(e)}")
                result.error_count += 1

        # Commit final
        await db.commit()

        if result.created_stocks:
            result.warnings.append(
                f"Ações criadas automaticamente: {', '.join(result.created_stocks)}. "
                "Considere atualizar os nomes em 'Ações'."
            )

    except Exception as e:
        result.errors.append(f"Erro fatal ao processar arquivo: {str(e)}")
        await db.rollback()

    return result


def get_csv_template() -> str:
    """Retorna um template de CSV para download."""
    return """data,ticker,tipo,quantidade,preco,taxas,observacoes
2024-01-15,WEGE3,compra,100,35.50,0,Primeira compra
2024-02-20,PETR4,compra,200,28.75,4.90,
2024-03-10,WEGE3,venda,50,38.00,0,Venda parcial
2024-04-05,ITUB4,compra,150,22.30,0,"""
