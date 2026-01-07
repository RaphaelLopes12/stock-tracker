import json
from datetime import datetime

from pywebpush import webpush, WebPushException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import NotificationPayload


async def send_push_notification(
    db: AsyncSession,
    subscription: PushSubscription,
    payload: NotificationPayload,
) -> bool:
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {
                    "p256dh": subscription.p256dh_key,
                    "auth": subscription.auth_key,
                }
            },
            data=json.dumps(payload.model_dump()),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_subject},
        )

        await db.execute(
            update(PushSubscription)
            .where(PushSubscription.id == subscription.id)
            .values(last_used_at=datetime.utcnow())
        )
        await db.commit()
        return True

    except WebPushException as e:
        if e.response and e.response.status_code in [404, 410]:
            await db.execute(
                update(PushSubscription)
                .where(PushSubscription.id == subscription.id)
                .values(is_active=False)
            )
            await db.commit()
        print(f"Push notification failed: {e}")
        return False
    except Exception as e:
        print(f"Push notification error: {e}")
        return False


async def send_to_all_subscribers(
    db: AsyncSession,
    payload: NotificationPayload,
    notification_type: str = "price_alerts",
) -> dict:
    filter_field = {
        "price_alerts": PushSubscription.notify_price_alerts,
        "dividends": PushSubscription.notify_dividends,
        "news": PushSubscription.notify_news,
    }.get(notification_type, PushSubscription.notify_price_alerts)

    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.is_active == True,
            filter_field == True,
        )
    )
    subscriptions = result.scalars().all()

    success_count = 0
    failed_count = 0

    for subscription in subscriptions:
        if await send_push_notification(db, subscription, payload):
            success_count += 1
        else:
            failed_count += 1

    return {
        "total": len(subscriptions),
        "sent": success_count,
        "failed": failed_count,
    }


async def send_price_alert_notification(
    db: AsyncSession,
    ticker: str,
    current_price: float,
    target_price: float,
    alert_type: str,
) -> dict:
    if alert_type == "buy":
        title = f"🟢 {ticker} atingiu preço de compra!"
        body = f"Preço atual: R$ {current_price:.2f} | Alvo: R$ {target_price:.2f}"
    else:
        title = f"🔴 {ticker} atingiu preço de venda!"
        body = f"Preço atual: R$ {current_price:.2f} | Alvo: R$ {target_price:.2f}"

    payload = NotificationPayload(
        title=title,
        body=body,
        tag=f"price-alert-{ticker}",
        data={
            "type": "price_alert",
            "ticker": ticker,
            "url": f"/stocks/{ticker}",
        },
        actions=[
            {"action": "view", "title": "Ver ação"},
            {"action": "dismiss", "title": "Dispensar"},
        ],
        require_interaction=True,
    )

    return await send_to_all_subscribers(db, payload, "price_alerts")


async def send_dividend_notification(
    db: AsyncSession,
    ticker: str,
    dividend_type: str,
    value: float,
    payment_date: str,
) -> dict:
    payload = NotificationPayload(
        title=f"💰 Dividendo anunciado: {ticker}",
        body=f"{dividend_type}: R$ {value:.2f}/ação | Pagamento: {payment_date}",
        tag=f"dividend-{ticker}",
        data={
            "type": "dividend",
            "ticker": ticker,
            "url": f"/stocks/{ticker}",
        },
        actions=[
            {"action": "view", "title": "Ver detalhes"},
        ],
    )

    return await send_to_all_subscribers(db, payload, "dividends")
