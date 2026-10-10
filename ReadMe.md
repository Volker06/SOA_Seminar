# SOA Seminar – Telegram Bot API

Seminar môn SOA: Telegram Bot API gồm 3 chức năng, mỗi chức năng nằm ở một chỗ riêng.

| # | Chức năng | Vị trí | Công nghệ |
|---|-----------|--------|-----------|
| 1 | Command Handling (`/start`, `/help`, `/status`, `/skip`) | `src/.../handler/CommandHandler.java` | Spring Boot |
| 2 | Chatbot Basics (trả lời tin nhắn thường, hội thoại khảo sát) | `src/.../handler/ChatResponder.java`, `SurveyHandler.java` | Spring Boot |
| 3 | System Notifications (cảnh báo CPU/RAM/Disk, REST `/notify`, `/survey`) | `notification-service/` | Python + FastAPI |

## Flow demo: Post-sale Survey

Sau khi dùng xong dịch vụ, bot **chủ động** gửi phiếu khảo sát 5 sao tới khách (không cần gõ `/start`):

- Chấm **≤ 2 sao** (không hài lòng): bot hỏi lý do, lưu kết quả và cảnh báo đội CSKH qua Telegram.
- Chấm **≥ 3 sao** (hài lòng): bot hỏi khách có muốn góp ý gì không, rồi lưu kết quả.
- Gõ `/skip` để bỏ qua câu hỏi lý do / góp ý (số sao vẫn được lưu).

Chi tiết, sơ đồ tuần tự và kịch bản test: [docs/survey-flow.md](docs/survey-flow.md).

## Cấu trúc thư mục

```
SOA_Seminar/
├── src/main/java/com/seminar/telebotdemo/
│   ├── TelebotdemoApplication.java
│   ├── bot/MyTelegramBot.java          # nhận update + điều hướng + gửi tin
│   ├── config/TelegramBotConfig.java   # đăng ký bot
│   ├── handler/
│   │   ├── CommandHandler.java         # xử lý lệnh "/" (có /skip)
│   │   ├── ChatResponder.java          # chat thường
│   │   └── SurveyHandler.java          # máy trạng thái khảo sát sau bán
│   └── survey/
│       ├── SurveyResultStore.java      # lưu data/survey_results.csv
│       └── NotificationClient.java     # gọi REST /notify để cảnh báo CSKH
├── src/assembly/
│   ├── distribution.xml                # quy định nội dung file zip phân phối (Maven)
│   └── HUONG_DAN_CHAY.txt              # hướng dẫn chạy, nằm trong zip phân phối
├── notification-service/               # System Notification (Python)
│   ├── notifier.py                     # thư viện gửi Telegram (retry, 429, cắt 4096 ký tự)
│   ├── notification_service.py         # REST: POST /notify, POST /survey, GET /health
│   ├── monitor.py                      # giám sát tài nguyên
│   ├── trigger_survey.py               # giả lập "dùng xong dịch vụ" -> gửi phiếu khảo sát
│   ├── get_chat_id.py
│   └── requirements.txt
├── docs/
│   ├── tech-stack.md
│   ├── survey-flow.md
│   └── python-notification-guide.txt
├── pom.xml                             # cấu hình Maven: thư viện, plugin, đóng gói
├── mvnw, mvnw.cmd, .mvn/               # Maven Wrapper (không cần cài Maven)
└── .env.example                        # mẫu cấu hình (không chứa token thật)
```

## Yêu cầu

- **Java JDK 17 trở lên** (kiểm tra: `java -version`). Biến `JAVA_HOME` phải trỏ tới *thư mục* JDK, không phải file `java.exe`.
- **Python 3.9 trở lên** (kiểm tra: `python --version`).
- Một **bot Telegram riêng** của bạn, tạo bằng `@BotFather`. Không dùng chung token với người khác, vì Telegram sẽ báo lỗi 409.

## Cách 1: tải bản build sẵn (chỉ muốn chạy thử)

1. Vào mục [Releases](https://github.com/Volker06/SOA_Seminar/releases) và tải **`SOA_Seminar-dist.zip`**.
2. Giải nén, làm theo file `HUONG_DAN_CHAY.txt` bên trong.

Không cần cài Maven, chỉ cần Java 17 trở lên và Python.

## Cách 2: clone code và tự build (muốn sửa, dùng lại code)

**Bước 1. Clone**

```
git clone https://github.com/Volker06/SOA_Seminar.git
cd SOA_Seminar
```

**Bước 2. Tạo file `.env`** (không commit file này)

```
copy .env.example .env        (Windows)
cp .env.example .env          (Mac/Linux)
```

Điền các biến sau:

| Biến | Ý nghĩa |
|---|---|
| `BOT_TOKEN`, `TELEGRAM_BOT_TOKEN` | Token bot từ `@BotFather` (hai biến cùng một giá trị) |
| `BOT_USERNAME` | Username của bot |
| `TELEGRAM_CHAT_ID` | chat_id của bạn. Mở bot trên Telegram, bấm **Start** một lần, rồi nhắn `@userinfobot` để biết |
| `SERVICE_API_KEY` | Khóa bí mật cho REST của Notification Service, tự đặt |

**Bước 3. Build bằng Maven**

```
mvnw.cmd clean package -DskipTests        (Windows)
./mvnw clean package -DskipTests          (Mac/Linux)
```

Lần đầu Maven tải thư viện nên cần có mạng. `-DskipTests` bỏ qua bài test mặc định (bài này cần cấu hình token để khởi động ứng dụng). Kết quả nằm trong thư mục `target/`:

| File | Là gì |
|---|---|
| `target/telebotdemo-0.0.1-SNAPSHOT.jar` | Bot Java đã gói sẵn thư viện, chạy bằng `java -jar` |
| `target/SOA_Seminar-dist.zip` | Gói phân phối: JAR + `notification-service/` + `.env.example` + hướng dẫn |

Muốn chạy thử ngay mà không tạo JAR: `mvnw.cmd spring-boot:run`.

**Bước 4. Chạy (mở 3 cửa sổ terminal)**

```
# Terminal 1: bot Java (đứng ở thư mục có file .env)
java -jar target/telebotdemo-0.0.1-SNAPSHOT.jar

# Terminal 2: Notification Service
cd notification-service
pip install -r requirements.txt
uvicorn notification_service:app --port 8000

# Terminal 3: giả lập khách dùng xong dịch vụ -> gửi phiếu khảo sát
cd notification-service
python trigger_survey.py --order ORD-1001 --service "Giặt ủi"
```

Kết quả khảo sát được ghi vào `data/survey_results.csv`. Muốn bật thêm giám sát tài nguyên: `python monitor.py`.

## Maven dùng để làm gì

Maven chỉ phục vụ **phần Java**, ở bước build và đóng gói, không chạy khi bot hoạt động.

| Thành phần | Vai trò |
|---|---|
| `pom.xml` | Khai báo Java 17, thư viện (Spring Boot, telegrambots, spring-dotenv) và plugin |
| `spring-boot-maven-plugin` | Gói code và thư viện thành một file JAR chạy được |
| `maven-assembly-plugin` + `src/assembly/distribution.xml` | Gom JAR cùng `notification-service/` thành `SOA_Seminar-dist.zip` |
| `mvnw`, `mvnw.cmd`, `.mvn/` | Maven Wrapper: chạy Maven mà không cần cài sẵn |

Thư mục `target/` (kết quả build) **không nằm trong Git**. Mỗi người tự tạo lại bằng lệnh ở Bước 3. Phần Python không được Maven xử lý, Maven chỉ chép thư mục `notification-service/` vào gói zip.

## Dùng lại và mở rộng

| Muốn đổi | Sửa file |
|---|---|
| Nội dung phiếu khảo sát, số nút sao | `notification-service/notifier.py` (hàm `send_survey`) |
| Luồng hỏi lý do / góp ý | `handler/SurveyHandler.java` |
| Thêm lệnh `/...` | `handler/CommandHandler.java` |
| Cách lưu kết quả (CSV sang database) | `survey/SurveyResultStore.java` |
| Kích hoạt khảo sát từ hệ thống khác | `POST /survey` trong `notification_service.py` |

Thêm chức năng mới: tạo một class `@Component` trong `handler/` rồi gọi nó từ `MyTelegramBot.onUpdateReceived`.

## Lưu ý

- **Không commit `.env`** (chứa token bot). Nếu lỡ lộ token, vào `@BotFather` dùng `/revoke` để đổi.
- Telegram chỉ cho bot nhắn trước với người **đã bấm Start ít nhất một lần**.
- Trạng thái hội thoại khảo sát lưu trong RAM nên restart bot thì mất phiên đang dở. Kết quả lưu CSV chỉ để demo.
- Nếu `get_chat_id.py` báo lỗi 409, hãy tắt bot Java trước khi chạy file này (cả hai cùng dùng `getUpdates`).
