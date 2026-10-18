# SOA Seminar – Telegram Bot API

Seminar môn SOA: Telegram Bot API gồm 3 chức năng, mỗi chức năng nằm ở một chỗ riêng.

| # | Chức năng | Vị trí | Công nghệ |
|---|-----------|--------|-----------|
| 1 | Command Handling (`/start`, `/help`, `/status`, `/skip`) | `src/.../handler/CommandHandler.java` | Spring Boot |
| 2 | Chatbot Basics (trả lời tin nhắn thường, hội thoại khảo sát, tự lưu khách) | `ChatResponder.java`, `SurveyHandler.java`, `CustomerStore.java` | Spring Boot |
| 3 | System Notifications (cảnh báo CPU/RAM/Disk, REST `/notify`, `/survey`) | `notification-service/` | Python + FastAPI |

## Flow demo: Post-sale Survey

Sau khi dùng xong dịch vụ, bot **chủ động** gửi phiếu khảo sát 5 sao tới khách (không cần gõ `/start`):

- Chấm **≤ 2 sao** (không hài lòng): bot hỏi lý do rồi lưu kết quả.
- Chấm **≥ 3 sao** (hài lòng): bot hỏi khách có muốn góp ý gì không, rồi lưu kết quả.
- Gõ `/skip` để bỏ qua câu hỏi lý do / góp ý (số sao vẫn được lưu).

**Quản lý khách hàng:** mỗi người nhắn bot lần đầu sẽ được bot tự lưu vào `data/customers.csv` và cấp một **mã khách** (`KH001`, `KH002`, ...). Telegram bot không gửi được theo số điện thoại mà chỉ gửi theo `chat_id`, nên mã khách đóng vai trò thay thế. Khi gửi khảo sát chỉ cần chỉ định mã khách, có thể gửi cho một người, nhiều người hoặc tất cả.

**Mã đơn tự động:** mỗi phiếu khảo sát gửi đi được hệ thống tự đánh số `ORD-01`, `ORD-02`, ..., `ORD-99`, rồi quay lại `ORD-01`. Mỗi khách nhận một số riêng, ghép với mã khách thành `<số đơn>-<mã khách>` (vd: `ORD-06-KH001`, `ORD-07-KH002`). Không cần và không thể nhập mã đơn bằng tay.

## Các trường hợp khách phản hồi (Use case)

Sau khi nhận phiếu 5 sao, khách có thể phản hồi theo nhiều cách. Tất cả đều đi qua `MyTelegramBot` → `SurveyHandler` và kết thúc bằng một dòng trong `data/survey_results.csv` (trừ trường hợp UC6, UC7, UC8).

### Nhóm 1: Khách hoàn thành khảo sát

| # | Khách làm gì | Bot phản hồi | Kết quả lưu trong CSV |
|---|---|---|---|
| UC1 | Bấm **1 hoặc 2 sao**, rồi nhắn lý do chưa hài lòng | Hiện thông báo "Đã ghi nhận n⭐", sửa phiếu thành "Bạn đã đánh giá đơn ...", hỏi lý do. Sau khi khách nhắn thì cảm ơn và cam kết cải thiện dịch vụ | `stars` = 1 hoặc 2, `sentiment` = `UNSATISFIED`, `comment` = lý do |
| UC2 | Bấm **1 hoặc 2 sao**, rồi gõ `/skip` | Như UC1 nhưng bỏ qua lý do, vẫn cảm ơn | `UNSATISFIED`, `comment` rỗng |
| UC3 | Bấm **3 đến 5 sao**, rồi nhắn góp ý | Hỏi góp ý (kèm nút "Không, cảm ơn"). Sau khi khách nhắn thì cảm ơn và hẹn gặp lại | `stars` = 3 đến 5, `sentiment` = `SATISFIED`, `comment` = góp ý |
| UC4 | Bấm **3 đến 5 sao**, rồi gõ `/skip` | Bỏ qua góp ý, cảm ơn | `SATISFIED`, `comment` rỗng |
| UC5 | Bấm **3 đến 5 sao**, rồi bấm nút **"Không, cảm ơn"** | Sửa tin thành "Bạn không có góp ý thêm.", rồi cảm ơn | `SATISFIED`, `comment` rỗng |

Quy tắc phân nhánh: `stars <= 2` là không hài lòng (bot hỏi **lý do**), `stars >= 3` là hài lòng (bot hỏi **góp ý**). Số sao luôn được lưu dù khách có trả lời câu hỏi tiếp theo hay không.

### Nhóm 2: Khách thao tác lặp hoặc ngoài luồng

| # | Tình huống | Bot xử lý | Có ghi thêm vào CSV? |
|---|---|---|---|
| UC6 | Bấm sao **lần thứ hai** trên cùng một phiếu khảo sát | Hiện thông báo "Bạn đã đánh giá đơn này rồi", không đổi kết quả (chặn bằng tập `rated` với khóa `chatId:messageId`, tức theo từng tin nhắn phiếu) | Không |
| UC7 | Bấm "Không, cảm ơn" khi khảo sát đã hoàn tất (hoặc bấm lần hai) | Hiện "Khảo sát đã hoàn tất", sửa tin thành "Khảo sát này đã hoàn tất." | Không |
| UC8 | Gõ `/skip` khi **không có** khảo sát nào đang chờ | Trả lời "Hiện không có khảo sát nào đang chờ." | Không |
| UC9 | Đang chờ lý do/góp ý, khách gõ **lệnh khác** (ví dụ `/help`) | Lệnh chạy bình thường, phiên khảo sát vẫn giữ nguyên để khách trả lời tiếp | Chưa (chờ khách trả lời) |
| UC10 | Đang chờ lý do/góp ý, khách gõ **chữ bất kỳ** (kể cả "hello") | Chữ đó được hiểu là lý do/góp ý và lưu lại | Có |
| UC11 | Khách bấm sao cho **đơn khác** khi phiên cũ còn dở | Phiên cũ bị ghi đè, phiên mới bắt đầu. Phiên cũ không được lưu | Chỉ lưu phiên mới |
| UC12 | Bot **khởi động lại** giữa chừng | Phiên đang dở mất (lưu trong RAM). Chữ khách nhắn sau đó rơi vào chat thường (bot nhại lại), và phiếu cũ có thể chấm lại | Không |
| UC13 | Bộ đếm mã đơn **quay vòng** (`ORD-99` → `ORD-01`) và khách nhận lại phiếu có mã trùng với vòng trước | Khách vẫn chấm bình thường, vì mỗi phiếu là một tin nhắn riêng (chống trùng theo `messageId`, không theo mã đơn) | Có (cột `time` phân biệt các vòng) |

### Ví dụ nội dung `data/survey_results.csv`

```
time,chat_id,order_id,stars,sentiment,comment
2026-10-14T10:05:12,123456789,"ORD-01-KH001",2,UNSATISFIED,"Giao trễ 2 tiếng"
2026-10-14T10:06:40,987654321,"ORD-01-KH002",5,SATISFIED,""
2026-10-14T10:08:03,555000111,"ORD-01-KH003",4,SATISFIED,"Nhân viên thân thiện, giặt sạch"
```

Cột `comment` luôn nằm trong dấu nháy kép nên khách nhắn có dấu phẩy vẫn không làm hỏng file. Cột `chat_id` đối chiếu được với `data/customers.csv` để biết khách nào đã phản hồi. Cột `order_id` lặp lại sau mỗi 99 đơn, dùng cột `time` để phân biệt.

## Cấu trúc thư mục

```
SOA_Seminar/
├── src/main/java/com/seminar/telebotdemo/
│   ├── TelebotdemoApplication.java
│   ├── bot/MyTelegramBot.java          # nhận update + điều hướng + gửi tin + lưu khách
│   ├── config/TelegramBotConfig.java   # đăng ký bot
│   ├── handler/
│   │   ├── CommandHandler.java         # xử lý lệnh "/" (có /skip)
│   │   ├── ChatResponder.java          # chat thường
│   │   └── SurveyHandler.java          # máy trạng thái khảo sát sau bán
│   └── survey/
│       ├── CustomerStore.java          # lưu khách + cấp mã khách -> data/customers.csv
│       └── SurveyResultStore.java      # lưu kết quả -> data/survey_results.csv
├── src/assembly/
│   ├── distribution.xml                # quy định nội dung file zip phân phối (Maven)
│   └── HUONG_DAN_CHAY.txt              # hướng dẫn chạy, nằm trong zip phân phối
├── notification-service/               # System Notification (Python)
│   ├── notifier.py                     # thư viện gửi Telegram (retry, 429, cắt 4096 ký tự)
│   ├── notification_service.py         # REST: POST /notify, POST /survey, GET /health
│   ├── customers.py                    # đọc data/customers.csv (mã khách -> chat_id)
│   ├── monitor.py                      # giám sát tài nguyên
│   ├── trigger_survey.py               # gửi phiếu khảo sát + tự đánh số mã đơn (--list, --to, --all)
│   ├── get_chat_id.py                  # (không còn cần thiết, bot đã tự lưu chat_id)
│   └── requirements.txt
├── data/                               # tự tạo khi chạy, không nằm trong Git
│   ├── customers.csv                   # danh sách khách + mã khách
│   ├── survey_results.csv              # kết quả khảo sát
│   └── order_counter.txt               # bộ đếm mã đơn (ORD-01 đến ORD-99)
├── docs/
│   ├── tech-stack.md
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
| `TELEGRAM_CHAT_ID` | chat_id của quản trị: là nơi nhận phiếu khi gửi thử mà không chỉ định khách. Mở bot trên Telegram, bấm **Start** một lần, rồi nhắn `@userinfobot` để biết |
| `SERVICE_API_KEY` | Khóa bí mật cho REST của Notification Service, tự đặt |
| `CUSTOMERS_FILE` | (Tuỳ chọn) Đường dẫn tới `customers.csv` nếu để khác chỗ mặc định |

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

**Bước 4. Chạy bot Java (và Notification Service nếu cần)**

```
# Terminal 1: bot Java (đứng ở thư mục có file .env, giữ mở suốt quá trình demo)
java -jar target/telebotdemo-0.0.1-SNAPSHOT.jar

# Terminal 2 (tuỳ chọn): Notification Service
cd notification-service
pip install -r requirements.txt
uvicorn notification_service:app --port 8000
```

Notification Service là **tuỳ chọn** với luồng khảo sát: chỉ cần chạy khi muốn dùng REST `/notify`, `/survey`. Gửi phiếu bằng `trigger_survey.py` (Bước 6) và `monitor.py` không cần chạy `uvicorn`.

**Bước 5. Thu thập khách hàng (làm trên Telegram)**

Mỗi khách (hoặc mỗi tài khoản Telegram dùng để thử) mở bot và nhắn `/start`. Bot trả lời kèm mã khách:

```
Mã khách hàng của bạn: KH001
```

Người thứ hai là `KH002`, người thứ ba là `KH003`, và cứ thế tiếp tục. Một người nhắn nhiều lần vẫn chỉ có một mã. Bot tự ghi vào `data/customers.csv`:

```
code,chat_id,name,username,registered_at
KH001,123456789,Nguyen Van A,vana,2026-10-14T10:00:00
```

Có thể mở file này để kiểm tra, hoặc sửa cột `code` thành tên dễ nhớ (vd: `AN`, `BINH`).

**Bước 6. Gửi phiếu khảo sát (Terminal 3)**

```
cd notification-service

# Xem danh sách khách đã lưu
python trigger_survey.py --list

# Gửi cho 1 khách (mã đơn tự động: ORD-01-KH001, lần sau ORD-02-KH001, ...)
python trigger_survey.py --service "Giặt ủi" --to KH001

# Gửi cho nhiều khách (cách nhau bằng dấu cách): ORD-03-KH001, ORD-03-KH002
python trigger_survey.py --service "Giặt ủi" --to KH001 KH002

# Gửi cho tất cả khách đã lưu
python trigger_survey.py --service "Giặt ủi" --all

# Không chỉ định khách: gửi về TELEGRAM_CHAT_ID của bạn (test nhanh), mã dạng ORD-04-ADMIN
python trigger_survey.py --service "Giặt ủi"
```

| Tham số | Ý nghĩa |
|---|---|
| `--service` | Tên dịch vụ khách vừa dùng |
| `--to MÃ [MÃ ...]` | Gửi cho các khách chỉ định |
| `--all` | Gửi cho toàn bộ khách đã lưu |
| `--list` | Xem danh sách khách đã lưu (không làm tăng số đếm mã đơn) |
| `--delay N` | Chờ N giây trước khi gửi |

Mỗi phiếu gửi đi lấy một số kế tiếp từ bộ đếm, nên khách nào cũng có số đơn riêng. Số đếm hiện tại nằm trong `data/order_counter.txt`, xóa file này để đếm lại từ `ORD-01`. Nếu gửi lỗi cho một khách, số đó vẫn bị tiêu, nên dãy số có thể nhảy cóc.

Nếu một khách chặn bot hoặc bị lỗi, chương trình báo lỗi riêng người đó rồi gửi tiếp cho những người còn lại.

Kết quả khảo sát được ghi vào `data/survey_results.csv` (cột `chat_id` đối chiếu được với `data/customers.csv`). Muốn bật thêm giám sát tài nguyên: `python monitor.py`.

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
| Cách lưu kết quả khảo sát (CSV sang database) | `survey/SurveyResultStore.java` |
| Cách lưu khách / quy tắc đặt mã khách | `survey/CustomerStore.java` và `notification-service/customers.py` |
| Cách đánh số mã đơn, giá trị tối đa (mặc định 99) | `notification-service/trigger_survey.py` (hàm `next_order_id`, hằng `MAX_ORDER`) |
| Kích hoạt khảo sát từ hệ thống khác | `POST /survey` trong `notification_service.py` (header `X-API-Key`) |

Thêm chức năng mới: tạo một class `@Component` trong `handler/` rồi gọi nó từ `MyTelegramBot.onUpdateReceived`.

## Lưu ý

- **Không commit `.env`** (chứa token bot). Nếu lỡ lộ token, vào `@BotFather` dùng `/revoke` để đổi.
- Telegram chỉ cho bot nhắn trước với người **đã bấm Start ít nhất một lần**. Người đã nhắn bot từ trước khi có tính năng lưu khách cần nhắn lại 1 lần để được lưu.
- Thư mục `data/` nằm trong `.gitignore`. Muốn xóa sạch để demo lại từ đầu, xóa `data/customers.csv`, `data/survey_results.csv` và `data/order_counter.txt`.
- Python mặc định đọc `data/customers.csv` ở thư mục cha của `notification-service` (cùng chỗ với file `.jar`). Nếu để khác chỗ, đặt `CUSTOMERS_FILE` trong `.env`.
- Mỗi cặp (khách + phiếu) chỉ được chấm một lần. Bộ nhớ chống chấm trùng nằm trong RAM nên restart bot thì phiếu cũ có thể chấm lại.
- Trạng thái hội thoại khảo sát lưu trong RAM nên restart bot thì mất phiên đang dở. Kết quả lưu CSV chỉ để demo.
- `get_chat_id.py` không còn cần dùng vì bot đã tự lưu `chat_id`. Nếu chạy mà báo lỗi 409, hãy tắt bot Java trước (cả hai cùng dùng `getUpdates`).