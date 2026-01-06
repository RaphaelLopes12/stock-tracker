"""Serviço para cálculos e operações do portfolio."""

from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Portfolio, Stock, Transaction
from app.schemas.portfolio import PortfolioHolding, PortfolioSummary
from app.services.quote_service import get_quotes_batch


async def get_portfolio_holdings(db: AsyncSession) -> list[Portfolio]:
    """Busca todos os holdings do portfolio com dados do stock."""
    result = await db.execute(
        select(Portfolio)
        .options(selectinload(Portfolio.stock))
        .where(Portfolio.quantity > 0)
        .order_by(Portfolio.stock_id)
    )
    return list(result.scalars().all())


async def get_portfolio_with_quotes(db: AsyncSession) -> list[PortfolioHolding]:
    """Busca portfolio com cotações atuais."""
    holdings = await get_portfolio_holdings(db)

    if not holdings:
        return []

    # Buscar cotações em lote
    tickers = [h.stock.ticker for h in holdings]
    quotes = await get_quotes_batch(tickers)

    result = []
    for holding in holdings:
        ticker = holding.stock.ticker
        quote = quotes.get(ticker, {})

        current_price = Decimal(str(quote.get("price", 0))) if quote else None
        total_invested = holding.average_price * holding.quantity

        current_value = None
        gain_loss = None
        gain_loss_percent = None
        change_today = None

        if current_price and current_price > 0:
            current_value = current_price * holding.quantity
            gain_loss = current_value - total_invested
            if total_invested > 0:
                gain_loss_percent = float((current_value / total_invested - 1) * 100)
            change_today = quote.get("change_percent")

        result.append(
            PortfolioHolding(
                id=holding.id,
                stock_id=holding.stock_id,
                ticker=ticker,
                stock_name=holding.stock.name,
                sector=holding.stock.sector,
                quantity=holding.quantity,
                average_price=holding.average_price,
                first_buy_date=holding.first_buy_date,
                notes=holding.notes,
                current_price=current_price,
                current_value=current_value,
                total_invested=total_invested,
                gain_loss=gain_loss,
                gain_loss_percent=gain_loss_percent,
                change_today=change_today,
            )
        )

    return result


def calculate_portfolio_summary(holdings: list[PortfolioHolding]) -> PortfolioSummary:
    """Calcula o resumo do portfolio."""
    if not holdings:
        return PortfolioSummary(
            total_invested=Decimal("0"),
            current_value=Decimal("0"),
            total_gain_loss=Decimal("0"),
            total_gain_loss_percent=0.0,
            holdings_count=0,
        )

    total_invested = Decimal("0")
    current_value = Decimal("0")
    best_performer: Optional[tuple[str, float]] = None
    worst_performer: Optional[tuple[str, float]] = None

    for h in holdings:
        if h.total_invested:
            total_invested += h.total_invested
        if h.current_value:
            current_value += h.current_value

        if h.gain_loss_percent is not None:
            if best_performer is None or h.gain_loss_percent > best_performer[1]:
                best_performer = (h.ticker, h.gain_loss_percent)
            if worst_performer is None or h.gain_loss_percent < worst_performer[1]:
                worst_performer = (h.ticker, h.gain_loss_percent)

    total_gain_loss = current_value - total_invested
    total_gain_loss_percent = 0.0
    if total_invested > 0:
        total_gain_loss_percent = float((current_value / total_invested - 1) * 100)

    return PortfolioSummary(
        total_invested=total_invested,
        current_value=current_value,
        total_gain_loss=total_gain_loss,
        total_gain_loss_percent=total_gain_loss_percent,
        holdings_count=len(holdings),
        best_performer=best_performer[0] if best_performer else None,
        worst_performer=worst_performer[0] if worst_performer else None,
    )


async def process_transaction(
    db: AsyncSession,
    stock: Stock,
    trans_type: str,
    quantity: int,
    price: Decimal,
    trans_date,
    fees: Decimal = Decimal("0"),
    notes: Optional[str] = None,
) -> tuple[Transaction, Portfolio]:
    """
    Processa uma transação e atualiza o portfolio.

    Returns:
        Tuple com a transação criada e o portfolio atualizado
    """
    # Buscar portfolio existente para este stock
    result = await db.execute(select(Portfolio).where(Portfolio.stock_id == stock.id))
    portfolio = result.scalar_one_or_none()

    # Calcular valor total da transação
    total_value = price * quantity

    # Criar a transação
    transaction = Transaction(
        stock_id=stock.id,
        type=trans_type,
        quantity=quantity,
        price=price,
        total_value=total_value,
        date=trans_date,
        fees=fees,
        notes=notes,
    )
    db.add(transaction)

    if trans_type == "buy":
        if portfolio:
            # Calcular novo preço médio
            old_total = portfolio.average_price * portfolio.quantity
            new_total = old_total + total_value
            new_quantity = portfolio.quantity + quantity
            new_average = new_total / new_quantity

            portfolio.quantity = new_quantity
            portfolio.average_price = new_average
        else:
            # Criar novo portfolio
            portfolio = Portfolio(
                stock_id=stock.id,
                quantity=quantity,
                average_price=price,
                first_buy_date=trans_date,
                notes=None,
            )
            db.add(portfolio)

    elif trans_type == "sell":
        if not portfolio or portfolio.quantity < quantity:
            raise ValueError(
                f"Quantidade insuficiente. Disponível: {portfolio.quantity if portfolio else 0}"
            )

        portfolio.quantity -= quantity

        # Se vendeu tudo, zerar mas manter registro
        if portfolio.quantity == 0:
            portfolio.average_price = Decimal("0")

    await db.commit()
    await db.refresh(transaction)
    await db.refresh(portfolio)

    return transaction, portfolio


async def recalculate_portfolio_from_transactions(db: AsyncSession, stock_id: int) -> Optional[Portfolio]:
    """
    Recalcula o portfolio baseado em todas as transações.
    Útil após deletar uma transação.
    """
    # Buscar todas as transações deste stock ordenadas por data
    result = await db.execute(
        select(Transaction)
        .where(Transaction.stock_id == stock_id)
        .order_by(Transaction.date, Transaction.id)
    )
    transactions = list(result.scalars().all())

    # Buscar portfolio
    result = await db.execute(select(Portfolio).where(Portfolio.stock_id == stock_id))
    portfolio = result.scalar_one_or_none()

    if not transactions:
        # Sem transações, deletar portfolio se existir
        if portfolio:
            await db.delete(portfolio)
            await db.commit()
        return None

    # Recalcular desde o início
    quantity = 0
    total_cost = Decimal("0")
    first_buy_date = None

    for t in transactions:
        if t.type == "buy":
            if first_buy_date is None:
                first_buy_date = t.date
            total_cost += t.price * t.quantity
            quantity += t.quantity
        elif t.type == "sell":
            # Venda não altera preço médio, só quantidade
            quantity -= t.quantity
            if quantity > 0:
                # Ajustar custo proporcional
                total_cost = (total_cost / (quantity + t.quantity)) * quantity

    average_price = total_cost / quantity if quantity > 0 else Decimal("0")

    if portfolio:
        portfolio.quantity = quantity
        portfolio.average_price = average_price
        portfolio.first_buy_date = first_buy_date
    else:
        portfolio = Portfolio(
            stock_id=stock_id,
            quantity=quantity,
            average_price=average_price,
            first_buy_date=first_buy_date,
        )
        db.add(portfolio)

    await db.commit()
    await db.refresh(portfolio)

    return portfolio
