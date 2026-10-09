# SOA Seminar – Telegram Bot API

Seminar môn SOA: Telegram Bot API gồm 3 chức năng, mỗi chức năng nằm ở một chỗ riêng.

| # | Chức năng | Vị trí | Công nghệ |
|---|-----------|--------|-----------|
| 1 | Command Handling (`/start`, `/help`, `/status`) | `src/.../handler/CommandHandler.java` | Spring Boot |
| 2 | Chatbot Basics (trả lời tin nhắn thường) | `src/.../handler/ChatResponder.java` | Spring Boot |
| 3 | System Notifications (cảnh báo CPU/RAM/Disk, REST `/notify`) | `notification-service/` | Python + FastAPI |

## Flow demo: Post-sale Survey
Sau khi dùng xong dịch vụ, bot **chủ động** gửi phiếu 5 sao (≤2⭐ hỏi lý do, ≥3⭐ hỏi góp ý).
Chạy thử: `python notification-service/trigger_survey.py`. Chi tiết, sơ đồ và kịch bản test: [docs/survey-flow.md](docs/survey-flow.md).

## Cấu trúc thư mục
```
SOA_Seminar/
├── src/main/java/com/seminar/telebotdemo/
│   ├── TelebotdemoApplication.java
│   ├── bot/MyTelegramBot.java        # chỉ nhận update + điều hướng + gửi
│   ├── config/TelegramBotConfig.java # đăng ký bot
│   └── handler/
│       ├── CommandHandler.java       # xử lý lệnh "/" (có /skip)
│       ├── ChatResponder.java        # chat thường
│       └── SurveyHandler.java        # máy trạng thái khảo sát sau bán
│   └── survey/
│       ├── SurveyResultStore.java    # lưu data/survey_results.csv
│       └── NotificationClient.java   # gọi REST /notify để cảnh báo CSKH
├── notification-service/             # System Notification (Python)
│   ├── notifier.py                   # thư viện gửi Telegram (retry, 429, cắt 4096 ký tự)
│   ├── notification_service.py       # REST: POST /notify, POST /survey, GET /health
│   ├── monitor.py                    # giám sát tài nguyên
│   ├── trigger_survey.py             # giả lập "dùng xong dịch vụ" -> gửi phiếu khảo sát
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
