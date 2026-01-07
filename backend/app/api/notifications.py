from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.push_subscription import PushSubscription
from app.schemas.push_subscription import (
    NotificationPayload,
    PushSubscriptionCreate,
    PushSubscriptionPreferences,
    PushSubscriptionResponse,
    VapidKeysResponse,
)
from app.services.web_push_service import send_to_all_subscribers

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/vapid-key")
async def get_vapid_public_key() -> VapidKeysResponse:
    if not settings.vapid_public_key:
        raise HTTPException(status_code=503, detail="Push notifications not configured")
    return VapidKeysResponse(public_key=settings.vapid_public_key)


@router.post("/subscribe")
async def subscribe(
    subscription: PushSubscriptionCreate,
    user_agent: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> PushSubscriptionResponse:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == subscription.endpoint)
    )
    existing = result.scalar_one_or_none()

    if existing:
        await db.execute(
            update(PushSubscription)
            .where(PushSubscription.id == existing.id)
            .values(
                p256dh_key=subscription.keys.p256dh,
                auth_key=subscription.keys.auth,
                user_agent=user_agent or subscription.user_agent,
                is_active=True,
            )
        )
        await db.commit()
        await db.refresh(existing)
        return existing

    new_subscription = PushSubscription(
        endpoint=subscription.endpoint,
        p256dh_key=subscription.keys.p256dh,
        auth_key=subscription.keys.auth,
        user_agent=user_agent or subscription.user_agent,
    )
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)
    return new_subscription


@router.post("/unsubscribe")
async def unsubscribe(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(delete(PushSubscription).where(PushSubscription.endpoint == endpoint))
    await db.commit()

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return {"message": "Unsubscribed successfully"}


@router.get("/subscription")
async def get_subscription(
    endpoint: str,
    db: AsyncSession = Depends(get_db),
) -> PushSubscriptionResponse:
    result = await db.execute(
        select(PushSubscription).where(
            PushSubscription.endpoint == endpoint,
            PushSubscription.is_active == True,
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    return subscription


@router.patch("/preferences")
async def update_preferences(
    endpoint: str,
    preferences: PushSubscriptionPreferences,
    db: AsyncSession = Depends(get_db),
) -> PushSubscriptionResponse:
    result = await db.execute(
        select(PushSubscription).where(PushSubscription.endpoint == endpoint)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await db.execute(
        update(PushSubscription)
        .where(PushSubscription.id == subscription.id)
        .values(**preferences.model_dump())
    )
    await db.commit()
    await db.refresh(subscription)
    return subscription


@router.post("/test")
async def send_test_notification(
    db: AsyncSession = Depends(get_db),
) -> dict:
    payload = NotificationPayload(
        title="Teste de Notificacao",
        body="Se voce esta vendo isso, as notificacoes estao funcionando!",
        tag="test-notification",
        data={"type": "test", "url": "/alerts"},
    )
    return await send_to_all_subscribers(db, payload, "price_alerts")