"""
notification_service.py - Notification Service (REST) theo tư duy SOA.

Các service khác (Order, Payment, Auth, CI/CD...) không cần biết Telegram.
Chúng chỉ gọi REST:  POST /notify  -> service này lo việc gửi qua Telegram.

Chạy :  uvicorn notification_service:app --reload --port 8000
Docs :  http://localhost:8000/docs   (Swagger UI tự sinh)
"""
import logging
import os
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from notifier import TelegramError, TelegramNotifier

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("notification-service")

API_KEY = os.getenv("SERVICE_API_KEY", "change-me")
notifier = TelegramNotifier()

app = FastAPI(title="Notification Service", version="1.0.0",
              description="Nhận yêu cầu thông báo từ các service khác và chuyển tới Telegram.")


class Notification(BaseModel):
    service: str = Field(..., examples=["payment-service"])
    level: Literal["INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    title: str = Field(..., examples=["Thanh toán thất bại"])
    message: str = Field(..., examples=["Order #1234: cổng thanh toán timeout sau 30s"])


def _send(n: Notification):
    try:
        notifier.notify(n.level, n.title, n.message, service=n.service)
    except TelegramError as e:
        log.error("Gửi Telegram thất bại: %s", e)


@app.post("/notify", status_code=202)
def notify(n: Notification, background: BackgroundTasks, x_api_key: str = Header(None)):
    """Nhận thông báo, xếp hàng gửi nền và trả 202 Accepted ngay (không chặn service gọi)."""
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    background.add_task(_send, n)
    return {"status": "queued", "service": n.service, "level": n.level}


@app.get("/health")
def health():
    """Health check: kiểm tra service và token bot còn hợp lệ."""
    try:
        return {"status": "ok", "bot": notifier.get_me()["username"]}
    except TelegramError as e:
        raise HTTPException(status_code=503, detail=str(e))
