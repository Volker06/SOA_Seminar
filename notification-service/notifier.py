"""
notifier.py - Thư viện gửi System Notification qua Telegram Bot API.

Chức năng:
  - send_message : gửi tin nhắn (HTML), hỗ trợ im lặng (không rung/chuông)
  - notify       : gửi thông báo có cấu trúc (level, title, message, service, host, time)
  - send_document: gửi file (log, báo cáo...)
  - Retry tự động, xử lý rate limit (HTTP 429), cắt tin nhắn quá dài (giới hạn 4096 ký tự)
"""
import html
import logging
import os
import socket
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("notifier")

API_URL = "https://api.telegram.org/bot{token}/{method}"
MAX_LEN = 4096  # giới hạn ký tự của 1 tin nhắn Telegram

LEVEL_ICON = {
    "INFO": "ℹ️",
    "SUCCESS": "✅",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🚨",
}


class TelegramError(Exception):
    """Lỗi trả về từ Telegram API hoặc lỗi mạng sau khi đã retry."""


class TelegramNotifier:
    def __init__(self, token=None, chat_id=None, timeout=10, max_retries=3):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        if not self.token or not self.chat_id:
            raise ValueError("Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID (xem file .env)")
        self.timeout = timeout
        self.max_retries = max_retries
        self.host = socket.gethostname()

    # ------------------------------------------------------------------ core
    def _call(self, method, payload=None, file_field=None, file_path=None):
        """Gọi 1 method của Bot API, có retry + xử lý 429."""
        url = API_URL.format(token=self.token, method=method)
        last_err = None

        for attempt in range(1, self.max_retries + 1):
            try:
                if file_path:
                    with open(file_path, "rb") as f:
                        resp = requests.post(
                            url, data=payload, files={file_field: f}, timeout=self.timeout * 3
                        )
                else:
                    resp = requests.post(url, json=payload, timeout=self.timeout)
                data = resp.json()
            except (requests.RequestException, ValueError) as e:
                last_err = e
                wait = 2 ** attempt
                log.warning("Lỗi mạng (%s), thử lại sau %ss [%s/%s]", e, wait, attempt, self.max_retries)
                time.sleep(wait)
                continue

            if data.get("ok"):
                return data["result"]

            # Rate limit: Telegram cho biết phải đợi bao lâu
            if resp.status_code == 429:
                wait = data.get("parameters", {}).get("retry_after", 1) + 1
                log.warning("Bị rate limit, đợi %ss", wait)
                time.sleep(wait)
                continue

            # Lỗi khác (token sai, chat_id sai, bot bị chặn...) -> không retry
            raise TelegramError(f"{data.get('error_code')}: {data.get('description')}")

        raise TelegramError(f"Thất bại sau {self.max_retries} lần thử: {last_err}")

    # ------------------------------------------------------------- public API
    def get_me(self):
        """Kiểm tra token hợp lệ, trả về thông tin bot."""
        return self._call("getMe")

    def send_message(self, text, parse_mode="HTML", silent=False, reply_markup=None):
        if len(text) > MAX_LEN:
            text = text[: MAX_LEN - 20] + "\n… (đã cắt bớt)"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_notification": silent,  # True = không phát âm thanh
            "disable_web_page_preview": True,
        }
        if reply_markup:  # inline keyboard (nút bấm) đính kèm tin nhắn
            payload["reply_markup"] = reply_markup
        return self._call("sendMessage", payload)

    def send_document(self, path, caption=""):
        payload = {"chat_id": self.chat_id, "caption": caption[:1024], "parse_mode": "HTML"}
        return self._call("sendDocument", payload, file_field="document", file_path=path)

    def notify(self, level, title, message, service=None):
        """Gửi thông báo hệ thống có định dạng chuẩn."""
        level = level.upper()
        icon = LEVEL_ICON.get(level, "🔔")
        esc = html.escape  # tránh lỗi khi nội dung chứa <, >, &
        lines = [f"{icon} <b>[{level}] {esc(title)}</b>", ""]
        if service:
            lines.append(f"<b>Service:</b> {esc(service)}")
        lines.append(f"<b>Host:</b> {esc(self.host)}")
        lines.append(f"<b>Time:</b> {datetime.now():%Y-%m-%d %H:%M:%S}")
        lines.append("")
        lines.append(f"<pre>{esc(message)}</pre>")
        # INFO/SUCCESS gửi im lặng, còn lại có âm thanh
        silent = level in ("INFO", "SUCCESS")
        return self.send_message("\n".join(lines), silent=silent)

    def send_survey(self, order_id, service_name="dịch vụ"):
        """Chủ động đẩy phiếu khảo sát sau bán (5 nút sao) tới khách hàng.

        callback_data có dạng  SURVEY:RATE:<order_id>:<số sao>
        -> bot Java nhận callback_query này và điều khiển phần hội thoại tiếp theo.
        """
        order_id = str(order_id)
        if ":" in order_id or len(order_id.encode()) > 30:
            raise ValueError("order_id không được chứa ':' và tối đa 30 byte (giới hạn callback_data 64 byte)")
        esc = html.escape
        text = (
            "⭐ <b>Khảo sát sau dịch vụ</b>\n\n"
            f"Cảm ơn bạn đã sử dụng <b>{esc(service_name)}</b> (mã đơn <code>{esc(order_id)}</code>).\n"
            "Bạn hài lòng với dịch vụ ở mức nào? Hãy chọn số sao bên dưới 👇"
        )
        keyboard = {
            "inline_keyboard": [[
                {"text": f"{n}⭐", "callback_data": f"SURVEY:RATE:{order_id}:{n}"}
                for n in range(1, 6)
            ]]
        }
        return self.send_message(text, reply_markup=keyboard)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    n = TelegramNotifier()
    print("Bot:", n.get_me()["username"])
    n.notify("INFO", "Test thông báo", "Bot đã kết nối thành công!", service="demo")
