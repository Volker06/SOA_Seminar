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


class SurveyRequest(BaseModel):
    order_id: str = Field(..., examples=["ORD-1001"])
    service_name: str = Field("dịch vụ", examples=["Giặt ủi"])


def _send_survey(r: SurveyRequest):
    try:
        notifier.send_survey(r.order_id, r.service_name)
    except (TelegramError, ValueError) as e:
        log.error("Gửi khảo sát thất bại: %s", e)


def _send(n: Notification):
    try:
        notifier.notify(n.level, n.title, n.message, service=n.service)
    except TelegramError as e:
        log.error("Gửi Telegram thất bại: %s", e)


@app.post("/notify", status_code=202)
def notify(n: Notification, background: BackgroundTasks, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    background.add_task(_send, n)
    return {"status": "queued", "service": n.service, "level": n.level}


@app.post("/survey", status_code=202)
def survey(r: SurveyRequest, background: BackgroundTasks, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    background.add_task(_send_survey, r)
    return {"status": "queued", "order_id": r.order_id}


@app.get("/health")
def health():
    try:
        return {"status": "ok", "bot": notifier.get_me()["username"]}
    except TelegramError as e:
        raise HTTPException(status_code=503, detail=str(e))
