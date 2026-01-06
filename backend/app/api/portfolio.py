"""API endpoints para gestão do portfolio."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Portfolio, Stock, Transaction
from app.schemas.portfolio import (
    ImportResultResponse,
    PortfolioHolding,
    PortfolioResponse,
    PortfolioSummary,
    TransactionCreate,
    TransactionResponse,
)
from app.services.portfolio_service import (
    calculate_portfolio_summary,
    get_portfolio_with_quotes,
    process_transaction,
    recalculate_portfolio_from_transactions,
)
from app.services.import_service import import_csv, get_csv_template

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


@router.get("", response_model=PortfolioResponse)
async def get_portfolio(db: AsyncSession = Depends(get_db)):
    """Retorna o portfolio completo com cotações atuais e resumo."""
    holdings = await get_portfolio_with_quotes(db)
    summary = calculate_portfolio_summary(holdings)

    return PortfolioResponse(holdings=holdings, summary=summary)


@router.get("/holdings", response_model=list[PortfolioHolding])
async def get_holdings(db: AsyncSession = Depends(get_db)):
    """Retorna apenas os holdings do portfolio."""
    return await get_portfolio_with_quotes(db)


@router.get("/summary", response_model=PortfolioSummary)
async def get_summary(db: AsyncSession = Depends(get_db)):
    """Retorna o resumo do portfolio."""
    holdings = await get_portfolio_with_quotes(db)
    return calculate_portfolio_summary(holdings)


@router.get("/transactions", response_model=list[TransactionResponse])
async def get_transactions(
    limit: int = 50,
    ticker: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Retorna o histórico de transações."""
    query = select(Transaction).options(selectinload(Transaction.stock))

    if ticker:
        query = query.join(Stock).where(Stock.ticker == ticker.upper())

    query = query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    return [
        TransactionResponse(
            id=t.id,
            stock_id=t.stock_id,
            ticker=t.stock.ticker,
            stock_name=t.stock.name,
            type=t.type,
            quantity=t.quantity,
            price=t.price,
            total_value=t.total_value,
            date=t.date,
            fees=t.fees,
            notes=t.notes,
            created_at=t.created_at,
        )
        for t in transactions
    ]


@router.post("/transaction", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction_in: TransactionCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra uma nova transação (compra ou venda).
    Atualiza automaticamente o portfolio.
    """
    # Buscar stock pelo ticker
    result = await db.execute(
        select(Stock).where(Stock.ticker == transaction_in.ticker.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Ação {transaction_in.ticker} não encontrada",
        )

    try:
        transaction, portfolio = await process_transaction(
            db=db,
            stock=stock,
            trans_type=transaction_in.type,
            quantity=transaction_in.quantity,
            price=transaction_in.price,
            trans_date=transaction_in.date,
            fees=transaction_in.fees,
            notes=transaction_in.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return TransactionResponse(
        id=transaction.id,
        stock_id=transaction.stock_id,
        ticker=stock.ticker,
        stock_name=stock.name,
        type=transaction.type,
        quantity=transaction.quantity,
        price=transaction.price,
        total_value=transaction.total_value,
        date=transaction.date,
        fees=transaction.fees,
        notes=transaction.notes,
        created_at=transaction.created_at,
    )


@router.delete("/transaction/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Remove uma transação e recalcula o portfolio.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transação não encontrada")

    stock_id = transaction.stock_id

    # Deletar a transação
    await db.delete(transaction)
    await db.commit()

    # Recalcular portfolio
    await recalculate_portfolio_from_transactions(db, stock_id)


@router.post("/import", response_model=ImportResultResponse)
async def import_transactions(
    file: UploadFile = File(...),
    skip_duplicates: bool = True,
    create_missing_stocks: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Importa transações de um arquivo CSV.

    Formatos suportados:
    - Área do Investidor B3 (Excel exportado)
    - Notas de corretagem convertidas (Clear, XP, Rico)
    - Formato genérico com colunas: data, ticker, tipo, quantidade, preço

    O sistema detecta automaticamente o formato e as colunas.
    """
    # Validar tipo de arquivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Arquivo não fornecido")

    filename_lower = file.filename.lower()
    if not (filename_lower.endswith('.csv') or filename_lower.endswith('.txt')):
        raise HTTPException(
            status_code=400,
            detail="Formato não suportado. Envie um arquivo CSV ou TXT."
        )

    # Ler conteúdo
    try:
        content = await file.read()
        # Tentar decodificar com diferentes encodings
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
            try:
                text_content = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível ler o arquivo. Verifique a codificação."
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo: {str(e)}")

    # Importar
    result = await import_csv(
        db=db,
        content=text_content,
        skip_duplicates=skip_duplicates,
        create_missing_stocks=create_missing_stocks,
    )

    return ImportResultResponse(
        success_count=result.success_count,
        error_count=result.error_count,
        skipped_count=result.skipped_count,
        errors=result.errors[:20],  # Limitar erros retornados
        warnings=result.warnings[:10],
        created_stocks=result.created_stocks,
    )


@router.get("/import/template", response_class=PlainTextResponse)
async def get_import_template():
    """
    Retorna um template CSV para importação.
    Baixe este arquivo como modelo para suas transações.
    """
    return PlainTextResponse(
        content=get_csv_template(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=template_transacoes.csv"}
    )


@router.get("/{holding_id}", response_model=PortfolioHolding)
async def get_holding(
    holding_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Retorna detalhes de um holding específico."""
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.stock))
        .where(Portfolio.id == holding_id)
    )
    portfolio = result.scalar_one_or_none()

    if not portfolio:
        raise HTTPException(status_code=404, detail="Holding não encontrado")

    # Buscar cotação atual
    from app.services.quote_service import get_quote

    quote = await get_quote(portfolio.stock.ticker)

    from decimal import Decimal

    current_price = Decimal(str(quote.get("price", 0))) if quote else None
    total_invested = portfolio.average_price * portfolio.quantity

    current_value = None
    gain_loss = None
    gain_loss_percent = None
    change_today = None

    if current_price and current_price > 0:
        current_value = current_price * portfolio.quantity
        gain_loss = current_value - total_invested
        if total_invested > 0:
            gain_loss_percent = float((current_value / total_invested - 1) * 100)
        change_today = quote.get("change_percent") if quote else None

    return PortfolioHolding(
        id=portfolio.id,
        stock_id=portfolio.stock_id,
        ticker=portfolio.stock.ticker,
        stock_name=portfolio.stock.name,
        sector=portfolio.stock.sector,
        quantity=portfolio.quantity,
        average_price=portfolio.average_price,
        first_buy_date=portfolio.first_buy_date,
        notes=portfolio.notes,
        current_price=current_price,
        current_value=current_value,
        total_invested=total_invested,
        gain_loss=gain_loss,
        gain_loss_percent=gain_loss_percent,
        change_today=change_today,
    )
