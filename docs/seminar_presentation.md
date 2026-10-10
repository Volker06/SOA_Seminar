# Cấu Trúc Bài Thuyết Trình Seminar: Telegram Bot API

Dựa trên phiếu đánh giá Seminar môn Kiến trúc Hướng Dịch vụ (SOA) và source code `MyTelegramBot.java`, dưới đây là kịch bản chi tiết và dàn ý để nhóm bạn (SOA.26-27) đạt điểm tối đa (10/10).

---

## 1. WHAT - Technology Understanding (1.5 Điểm)
**Mục tiêu:** Giải thích đúng, rõ Telegram Bot API là gì, các khái niệm/thành phần chính.

*   **Giới thiệu chung:** Telegram Bot là các ứng dụng bên thứ ba chạy bên trong nền tảng Telegram. Người dùng có thể tương tác với bot bằng cách gửi tin nhắn, lệnh (commands), hoặc các request inline.
*   **Thành phần chính:**
    *   **BotFather:** "Chúa tể" của các loại bot trên Telegram, dùng để tạo bot mới, lấy `Token` xác thực, và cấu hình các thông tin cơ bản (tên, avatar, description).
    *   **Bot API:** Giao diện HTTP-based giúp ứng dụng của chúng ta (code Java/Spring Boot) giao tiếp với máy chủ Telegram.
    *   **Token:** Chuỗi định danh duy nhất (ví dụ: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`) dùng để authorize các API request.
    *   **Updates:** Bất kỳ tương tác nào của user với bot (tin nhắn mới, nhấn nút, etc.) đều được Telegram đóng gói thành một đối tượng `Update`.

## 2. WHY - Purpose & Use Cases (1.0 Điểm)
**Mục tiêu:** Giải thích công nghệ giải quyết vấn đề gì, khi nào nên sử dụng.

*   **Vấn đề giải quyết:** 
    *   Cung cấp một kênh giao tiếp nhanh, tiện lợi giữa hệ thống (hậu cảnh) và con người mà không cần phải build/maintian một ứng dụng mobile/web riêng biệt.
    *   Tự động hóa các tác vụ lặp đi lặp lại (hỗ trợ khách hàng, lấy thông tin tự động).
*   **Use Cases tiêu biểu (Áp dụng cho bài):**
    *   **System notifications (Thông báo hệ thống):** Bot có thể đẩy cảnh báo lỗi server, thông báo đơn hàng mới, hay trạng thái thanh toán thẳng vào máy điện thoại của quản trị viên theo thời gian thực (ví dụ như một pub/sub consumer).
    *   **Chatbot basics (Chatbot cơ bản):** Trả lời các câu hỏi thường gặp (FAQ), tra cứu thông tin nhanh dựa trên từ khóa. (Tương ứng với `ChatResponder` trong code).
    *   **Command handling (Xử lý lệnh):** Người dùng gửi các lệnh bắt đầu bằng `/` (như `/start`, `/help`, `/status`) để ra lệnh cho hệ thống thực hiện một action cụ thể. (Tương ứng với `CommandHandler`).

## 3. HOW - Architecture & Integration (2.5 Điểm) - Trọng tâm
**Mục tiêu:** Giải thích rõ workflow/architecture và cách tích hợp vào microservice/application.

*   **Hai mô hình kiến trúc nhận Update:**
    1.  **Long Polling (Đang sử dụng trong code):** Client (Spring Boot app) liên tục hỏi Server Telegram "Có tin nhắn mới không?". Phù hợp cho môi trường dev, hoặc server đứng sau tường lửa không có Public IP/SSL. (Class `TelegramLongPollingBot`).
    2.  **Webhooks:** Cấu hình cho Telegram Server chủ động gọi HTTP POST đến ứng dụng của chúng ta khi có event mới. Phù hợp cho Production, cần Public HTTPS URL.
*   **Workflow Integration (Dựa vào `MyTelegramBot.java`):**
    1.  Khởi tạo Spring Boot App, inject `botToken` và `botUsername` từ file properties/yaml (bảo mật không hardcode).
    2.  Hệ thống nhận `Update` qua method `onUpdateReceived(Update update)`.
    3.  Lọc dữ liệu: Kiểm tra xem update có text hay không (`hasMessage()` và `hasText()`).
    4.  **Routing logic (Microservice design pattern):** Bot chỉ đóng vai trò Controller (nhận request & trả response). Việc xử lý nghiệp vụ được tách ra (Decoupled):
        *   Nếu tin nhắn bắt đầu bằng `/` -> Chuyển cho `CommandHandler`.
        *   Nếu là text thường -> Chuyển cho `ChatResponder`.
    5.  Sử dụng đối tượng `SendMessage` để phản hồi ngược lại `chatId` của người dùng qua hàm `execute()`.

## 4. Hands-on Demo (2.0 Điểm)
**Mục tiêu:** Demo hoạt động, minh họa chức năng chính phù hợp với nội dung.

*   **Kịch bản Demo:**
    1.  Show BotFather trên Telegram, chỉ cách lấy Token.
    2.  Chạy ứng dụng Spring Boot.
    3.  **Demo System Notifications:** Tạo một API endpoint phụ (ví dụ: POST `/api/notify`), dùng Postman gọi vào API đó, và app sẽ chủ động gọi hàm gửi tin nhắn (Telegram bot) đến người dùng (admin). 
    4.  **Demo Command Handling:** Gõ `/start` hoặc `/help` để xem bot phản hồi theo logic của `CommandHandler`.
    5.  **Demo Chatbot Basics:** Nhập chữ "Xin chào", bot sẽ dùng `ChatResponder` để đáp lại.

## 5. Reusability (1.0 Điểm)
**Mục tiêu:** Có source code, hướng dẫn rõ ràng để sinh viên khác chạy lại.

*   Nên tạo một file `README.md` trong project với các bước:
    1.  Tạo bot bằng BotFather và lấy Token.
    2.  Cách thay thế `<YOUR_BOT_TOKEN>` trong file `application.properties`.
    3.  Lệnh chạy app (vd: `./mvnw spring-boot:run`).
*   **Thiết kế code tái sử dụng:** Nhấn mạnh việc trong `MyTelegramBot.java`, logic được tiêm (inject) qua constructor (`CommandHandler` và `ChatResponder`). Bất kỳ ai clone code về cũng có thể dễ dàng thay thế logic chat hoặc command mà không cần sửa core của class bot.

## 6. Presentation & Q&A (1.0 Điểm)
*   **Tip thuyết trình:** Đi thẳng vào vấn đề, vẽ một mô hình (diagram) mũi tên luồng đi của tin nhắn từ Điện thoại -> Telegram Server -> Ứng dụng Spring Boot.
*   **Câu hỏi dự kiến (Chuẩn bị trước để trả lời):**
    *   *Hỏi:* Làm sao để gửi tin nhắn chủ động cho user (System notification) thay vì chờ user chat trước? 
        *Đáp:* Hệ thống cần lưu lại `chatId` của user khi họ tương tác lần đầu (vd: lưu vào DB khi họ gõ `/start`). Sau đó, dùng `chatId` này để gửi `SendMessage` bất cứ khi nào có event từ hệ thống.
    *   *Hỏi:* Nếu số lượng tin nhắn quá lớn, Long Polling có đáp ứng được không?
        *Đáp:* Long Polling có thể bị nghẽn (bottleneck). Giải pháp là chuyển sang Webhook kết hợp với Message Queue (như RabbitMQ/Kafka) để scale ra nhiều instance xử lý song song.

## 7. Best Practices & Limitations (1.0 Điểm)
**Mục tiêu:** Lưu ý triển khai, hạn chế, lỗi thực tế.

*   **Best Practices:**
    *   **Bảo mật Token:** Tuyệt đối KHÔNG commit Bot Token lên GitHub public. Luôn dùng biến môi trường (Environment variables).
    *   **Tách biệt logic:** Giữ class Bot chỉ làm nhiệm vụ giao tiếp (gửi/nhận). Mọi tính toán nghiệp vụ phải nằm ở các class Service (đúng như kiến trúc các bạn đã làm).
    *   **Xử lý ngoại lệ:** Bắt lỗi `TelegramApiException` kĩ càng, nếu bot gặp lỗi gửi tin nhắn không được crash toàn bộ app.
*   **Limitations (Hạn chế):**
    *   Phụ thuộc hoàn toàn vào uptime của máy chủ Telegram.
    *   Bị giới hạn (Rate Limit): API không cho phép spam quá nhiều tin nhắn trong 1 giây (thường là 30 msg/sec). Nếu vượt quá sẽ bị Telegram block tạm thời (Lỗi 429 Too Many Requests).
