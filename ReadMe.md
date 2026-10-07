# SOA Seminar – Telegram Bot API

Seminar môn SOA: Telegram Bot API gồm 3 chức năng, mỗi chức năng nằm ở một chỗ riêng.

| # | Chức năng | Vị trí | Công nghệ |
|---|-----------|--------|-----------|
| 1 | Command Handling (`/start`, `/help`, `/status`) | `src/.../handler/CommandHandler.java` | Spring Boot |
| 2 | Chatbot Basics (trả lời tin nhắn thường) | `src/.../handler/ChatResponder.java` | Spring Boot |
| 3 | System Notifications (cảnh báo CPU/RAM/Disk, REST `/notify`) | `notification-service/` | Python + FastAPI |

## Cấu trúc thư mục
```
SOA_Seminar/
├── src/main/java/com/seminar/telebotdemo/
│   ├── TelebotdemoApplication.java
│   ├── bot/MyTelegramBot.java        # chỉ nhận update + điều hướng + gửi
│   ├── config/TelegramBotConfig.java # đăng ký bot
│   └── handler/
│       ├── CommandHandler.java       # xử lý lệnh "/"
│       └── ChatResponder.java        # chat thường
├── notification-service/             # System Notification (Python)
│   ├── notifier.py                   # thư viện gửi Telegram (retry, 429, cắt 4096 ký tự)
│   ├── notification_service.py       # REST: POST /notify, GET /health
│   ├── monitor.py                    # giám sát tài nguyên
│   ├── get_chat_id.py
│   └── requirements.txt
├── docs/
│   ├── tech-stack.md
│   └── python-notification-guide.txt
├── .env.example
└── pom.xml
```

## Chạy nhanh
1. `cp .env.example .env` rồi điền token/chat id (**không commit `.env`**).
2. **Bot (Java):** `./mvnw spring-boot:run`
3. **Notification (Python):**
   ```
   cd notification-service
   pip install -r requirements.txt
   uvicorn notification_service:app --port 8000
   python monitor.py
   ```

## Thêm chức năng mới
Thêm 1 class `@Component` trong `handler/` rồi gọi nó từ `MyTelegramBot.onUpdateReceived`.
