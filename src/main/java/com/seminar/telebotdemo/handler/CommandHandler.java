package com.seminar.telebotdemo.handler;

import org.springframework.stereotype.Component;

/** Chức năng 1 - Command Handling: xử lý các lệnh bắt đầu bằng "/". */
@Component
public class CommandHandler {

    public String handle(String command) {
        // Lấy phần lệnh chính, đề phòng user nhập "/start 123"
        String base = command.split(" ")[0].toLowerCase();

        return switch (base) {
            case "/start" -> "Xin chào! Mình là bot SOA. Gõ /help để xem danh sách lệnh.";
            case "/help" -> "Danh sách lệnh hỗ trợ:\n/start - Khởi động bot\n/status - Kiểm tra trạng thái hệ thống";
            case "/status" -> "Hệ thống Backend (Spring Boot) đang hoạt động bình thường \uD83D\uDFE2";
            default -> "Lệnh không hợp lệ. Vui lòng gõ /help.";
        };
    }
}
