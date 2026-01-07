from datetime import datetime

from pydantic import BaseModel, Field


class PushKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: PushKeys
    user_agent: str | None = None


class PushSubscriptionPreferences(BaseModel):
    notify_price_alerts: bool = True
    notify_dividends: bool = True
    notify_news: bool = False


class PushSubscriptionResponse(BaseModel):
    id: int
    endpoint: str
    is_active: bool
    notify_price_alerts: bool
    notify_dividends: bool
    notify_news: bool
    created_at: datetime
    last_used_at: datetime | None

    class Config:
        from_attributes = True


class NotificationPayload(BaseModel):
    title: str
    body: str
    icon: str = "/icons/icon-192x192.png"
    badge: str = "/icons/badge-72x72.png"
    tag: str | None = None
    data: dict = Field(default_factory=dict)
    actions: list[dict] = Field(default_factory=list)
    require_interaction: bool = False


class VapidKeysResponse(BaseModel):
    public_key: str
