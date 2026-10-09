package com.seminar.telebotdemo.handler;

import org.springframework.stereotype.Component;

/** Chức năng 1 - Command Handling: xử lý các lệnh bắt đầu bằng "/". */
@Component
public class CommandHandler {

    private final SurveyHandler surveyHandler;

    public CommandHandler(SurveyHandler surveyHandler) {
        this.surveyHandler = surveyHandler;
    }

    public String handle(long chatId, String command) {
        // Lấy phần lệnh chính, đề phòng user nhập "/start 123"
        String base = command.split(" ")[0].toLowerCase();

        return switch (base) {
            case "/start" -> "Xin chào! Mình là bot SOA. Gõ /help để xem danh sách lệnh.";
            case "/help" -> "Danh sách lệnh hỗ trợ:\n/start - Khởi động bot\n/status - Kiểm tra trạng thái hệ thống\n"
                    + "/skip - Bỏ qua câu hỏi khảo sát đang chờ";
            case "/status" -> "Hệ thống Backend (Spring Boot) đang hoạt động bình thường \uD83D\uDFE2";
            case "/skip" -> surveyHandler.skip(chatId);
            default -> "Lệnh không hợp lệ. Vui lòng gõ /help.";
        };
    }
}
