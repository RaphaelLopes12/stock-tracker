"""API endpoints para alertas de precos e indicadores."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models import Alert, AlertHistory, Stock
from app.services.quote_service import get_quote

router = APIRouter(prefix="/alerts", tags=["alerts"])


# Schemas
class AlertCondition(BaseModel):
    """Condicao do alerta."""
    operator: str = Field(..., description="Operador: 'above', 'below', 'change_up', 'change_down'")
    value: float = Field(..., description="Valor alvo ou percentual")


class AlertCreate(BaseModel):
    """Schema para criar alerta."""
    ticker: str = Field(..., description="Ticker da acao (ex: WEGE3)")
    name: Optional[str] = Field(None, description="Nome personalizado do alerta")
    type: str = Field(..., description="Tipo: 'price', 'change_percent', 'pe_ratio', 'dividend_yield'")
    condition: AlertCondition
    cooldown_hours: int = Field(default=24, description="Horas entre disparos do mesmo alerta")


class AlertUpdate(BaseModel):
    """Schema para atualizar alerta."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    condition: Optional[AlertCondition] = None
    cooldown_hours: Optional[int] = None


class AlertResponse(BaseModel):
    """Schema de resposta do alerta."""
    id: int
    ticker: str
    name: Optional[str]
    type: str
    condition: dict
    is_active: bool
    last_triggered_at: Optional[datetime]
    trigger_count: int
    cooldown_hours: int
    created_at: datetime

    class Config:
        from_attributes = True


class AlertHistoryResponse(BaseModel):
    """Schema de resposta do historico."""
    id: int
    alert_id: int
    triggered_at: datetime
    message: Optional[str]
    data: Optional[dict]

    class Config:
        from_attributes = True


# Helpers
def get_alert_type_description(alert_type: str) -> str:
    """Retorna descricao educativa do tipo de alerta."""
    descriptions = {
        "price": "Alerta de Preco: dispara quando o preco da acao atinge o valor definido.",
        "change_percent": "Alerta de Variacao: dispara quando a acao varia X% no dia.",
        "pe_ratio": "Alerta de P/L: dispara quando o indicador Preco/Lucro atinge o valor.",
        "dividend_yield": "Alerta de Dividendos: dispara quando o Dividend Yield atinge o valor.",
    }
    return descriptions.get(alert_type, "")


def format_alert_message(alert: Alert, quote: dict) -> str:
    """Formata mensagem do alerta disparado."""
    ticker = alert.stock.ticker if alert.stock else "???"
    condition = alert.condition
    operator = condition.get("operator", "")
    value = condition.get("value", 0)

    if alert.type == "price":
        current = quote.get("price", 0)
        direction = "subiu acima de" if operator == "above" else "caiu abaixo de"
        return f"{ticker} {direction} R$ {value:.2f}! Preco atual: R$ {current:.2f}"

    elif alert.type == "change_percent":
        current = quote.get("change_percent", 0)
        direction = "subiu" if operator == "change_up" else "caiu"
        return f"{ticker} {direction} {abs(current):.2f}% hoje! Alerta configurado para {value}%"

    elif alert.type == "pe_ratio":
        current = quote.get("pe_ratio", 0)
        direction = "subiu acima de" if operator == "above" else "caiu abaixo de"
        return f"P/L de {ticker} {direction} {value}! P/L atual: {current:.1f}"

    elif alert.type == "dividend_yield":
        current = quote.get("dividend_yield", 0)
        direction = "subiu acima de" if operator == "above" else "caiu abaixo de"
        return f"Dividend Yield de {ticker} {direction} {value}%! DY atual: {current:.1f}%"

    return f"Alerta disparado para {ticker}"


# Endpoints
@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Lista todos os alertas cadastrados."""
    query = (
        select(Alert)
        .options(selectinload(Alert.stock))
        .order_by(Alert.created_at.desc())
    )

    if active_only:
        query = query.where(Alert.is_active == True)

    result = await db.execute(query)
    alerts = result.scalars().all()

    # Adicionar ticker na resposta
    response = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "ticker": alert.stock.ticker if alert.stock else None,
            "name": alert.name,
            "type": alert.type,
            "condition": alert.condition,
            "is_active": alert.is_active,
            "last_triggered_at": alert.last_triggered_at,
            "trigger_count": alert.trigger_count,
            "cooldown_hours": alert.cooldown_hours,
            "created_at": alert.created_at,
        }
        response.append(alert_dict)

    return response


@router.get("/history", response_model=list[AlertHistoryResponse])
async def list_alert_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Lista historico de alertas disparados."""
    query = (
        select(AlertHistory)
        .order_by(AlertHistory.triggered_at.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/types")
async def list_alert_types():
    """Lista tipos de alertas disponiveis com explicacoes educativas."""
    return {
        "types": [
            {
                "type": "price",
                "name": "Preco Alvo",
                "description": "Receba um alerta quando a acao atingir um preco especifico.",
                "tip": "Use para definir um preco de compra ou venda que voce considera ideal.",
                "operators": [
                    {"value": "above", "label": "Acima de", "description": "Quando subir acima do valor"},
                    {"value": "below", "label": "Abaixo de", "description": "Quando cair abaixo do valor"},
                ],
                "value_label": "Preco (R$)",
                "value_placeholder": "Ex: 45.00",
            },
            {
                "type": "change_percent",
                "name": "Variacao Diaria",
                "description": "Receba um alerta quando a acao variar muito em um dia.",
                "tip": "Util para detectar quedas bruscas (oportunidades) ou altas exageradas.",
                "operators": [
                    {"value": "change_up", "label": "Subir mais de", "description": "Alta acima do percentual"},
                    {"value": "change_down", "label": "Cair mais de", "description": "Queda acima do percentual"},
                ],
                "value_label": "Variacao (%)",
                "value_placeholder": "Ex: 5",
            },
            {
                "type": "pe_ratio",
                "name": "P/L (Preco/Lucro)",
                "description": "Receba um alerta quando o indicador P/L atingir um valor.",
                "tip": "P/L abaixo de 15 geralmente indica acao barata. Acima de 25 pode estar cara.",
                "operators": [
                    {"value": "below", "label": "Abaixo de", "description": "P/L ficou barato"},
                    {"value": "above", "label": "Acima de", "description": "P/L ficou caro"},
                ],
                "value_label": "P/L",
                "value_placeholder": "Ex: 15",
            },
            {
                "type": "dividend_yield",
                "name": "Dividend Yield",
                "description": "Receba um alerta quando o DY atingir um valor.",
                "tip": "DY acima de 6% e considerado excelente para renda passiva.",
                "operators": [
                    {"value": "above", "label": "Acima de", "description": "DY ficou atrativo"},
                    {"value": "below", "label": "Abaixo de", "description": "DY caiu"},
                ],
                "value_label": "DY (%)",
                "value_placeholder": "Ex: 6",
            },
        ]
    }


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_in: AlertCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo alerta."""
    # Buscar stock
    result = await db.execute(
        select(Stock).where(Stock.ticker == alert_in.ticker.upper())
    )
    stock = result.scalar_one_or_none()

    if not stock:
        raise HTTPException(
            status_code=404,
            detail=f"Acao {alert_in.ticker} nao encontrada. Adicione-a primeiro na lista de acoes."
        )

    # Validar tipo
    valid_types = ["price", "change_percent", "pe_ratio", "dividend_yield"]
    if alert_in.type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo invalido. Use um dos: {', '.join(valid_types)}"
        )

    # Criar alerta
    alert = Alert(
        stock_id=stock.id,
        name=alert_in.name or f"Alerta {alert_in.type} - {stock.ticker}",
        type=alert_in.type,
        condition=alert_in.condition.model_dump(),
        cooldown_hours=alert_in.cooldown_hours,
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return {
        "id": alert.id,
        "ticker": stock.ticker,
        "name": alert.name,
        "type": alert.type,
        "condition": alert.condition,
        "is_active": alert.is_active,
        "last_triggered_at": alert.last_triggered_at,
        "trigger_count": alert.trigger_count,
        "cooldown_hours": alert.cooldown_hours,
        "created_at": alert.created_at,
    }


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca um alerta especifico."""
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.stock))
        .where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    return {
        "id": alert.id,
        "ticker": alert.stock.ticker if alert.stock else None,
        "name": alert.name,
        "type": alert.type,
        "condition": alert.condition,
        "is_active": alert.is_active,
        "last_triggered_at": alert.last_triggered_at,
        "trigger_count": alert.trigger_count,
        "cooldown_hours": alert.cooldown_hours,
        "created_at": alert.created_at,
    }


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    alert_in: AlertUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza um alerta."""
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.stock))
        .where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    # Atualizar campos
    if alert_in.name is not None:
        alert.name = alert_in.name
    if alert_in.is_active is not None:
        alert.is_active = alert_in.is_active
    if alert_in.condition is not None:
        alert.condition = alert_in.condition.model_dump()
    if alert_in.cooldown_hours is not None:
        alert.cooldown_hours = alert_in.cooldown_hours

    await db.commit()
    await db.refresh(alert)

    return {
        "id": alert.id,
        "ticker": alert.stock.ticker if alert.stock else None,
        "name": alert.name,
        "type": alert.type,
        "condition": alert.condition,
        "is_active": alert.is_active,
        "last_triggered_at": alert.last_triggered_at,
        "trigger_count": alert.trigger_count,
        "cooldown_hours": alert.cooldown_hours,
        "created_at": alert.created_at,
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove um alerta."""
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    await db.delete(alert)
    await db.commit()


@router.post("/{alert_id}/check")
async def check_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Verifica manualmente se um alerta deve disparar."""
    result = await db.execute(
        select(Alert)
        .options(selectinload(Alert.stock))
        .where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alerta nao encontrado")

    if not alert.stock:
        raise HTTPException(status_code=400, detail="Alerta sem acao associada")

    # Buscar cotacao atual
    quote = await get_quote(alert.stock.ticker)

    if not quote:
        raise HTTPException(
            status_code=503,
            detail=f"Nao foi possivel obter cotacao de {alert.stock.ticker}"
        )

    # Verificar condicao
    triggered = False
    condition = alert.condition
    operator = condition.get("operator", "")
    target_value = condition.get("value", 0)

    if alert.type == "price":
        current = quote.get("price", 0)
        if operator == "above" and current >= target_value:
            triggered = True
        elif operator == "below" and current <= target_value:
            triggered = True

    elif alert.type == "change_percent":
        current = quote.get("change_percent", 0)
        if operator == "change_up" and current >= target_value:
            triggered = True
        elif operator == "change_down" and current <= -target_value:
            triggered = True

    elif alert.type == "pe_ratio":
        current = quote.get("pe_ratio")
        if current:
            if operator == "above" and current >= target_value:
                triggered = True
            elif operator == "below" and current <= target_value:
                triggered = True

    elif alert.type == "dividend_yield":
        current = quote.get("dividend_yield")
        if current:
            if operator == "above" and current >= target_value:
                triggered = True
            elif operator == "below" and current <= target_value:
                triggered = True

    return {
        "alert_id": alert.id,
        "ticker": alert.stock.ticker,
        "triggered": triggered,
        "current_quote": quote,
        "condition": condition,
        "message": format_alert_message(alert, quote) if triggered else None,
    }
