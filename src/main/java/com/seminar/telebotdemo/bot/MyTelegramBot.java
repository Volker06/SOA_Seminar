package com.seminar.telebotdemo.bot;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.telegram.telegrambots.bots.TelegramLongPollingBot;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;

@Component
@SuppressWarnings("deprecation")
public class MyTelegramBot extends TelegramLongPollingBot {

    @Value("${telegram.bot.username}")
    private String botUsername;

    @Value("${telegram.bot.token}")
    private String botToken;

    @Override
    public String getBotUsername() {
        return botUsername;
    }

    @Override
    public String getBotToken() {
        return botToken;
    }
@Override
    public void onUpdateReceived(Update update) {
        if (update.hasMessage() && update.getMessage().hasText()) {
            String text = update.getMessage().getText();
            long chatId = update.getMessage().getChatId();

            // SỬA Ở ĐÂY: Phân loại tin nhắn
            if (text.startsWith("/")) {
                // Nếu là lệnh (bắt đầu bằng "/") -> Gọi hàm của Tân
                handleCommand(chatId, text);
            } else {
                // Nếu là tin nhắn chữ bình thường -> Gọi hàm của Việt
                String reply = generateResponse(text);
                sendReply(chatId, reply);
            }
        }
    }

    private String generateResponse(String input) {
        String lower = input.toLowerCase();
        if (lower.contains("hello") || lower.contains("chào")) {
            return "Chào bạn! Mình là bot demo cho seminar 😄";
        }
        return "Bạn vừa gửi: " + input;
    }
    private void handleCommand(long chatId, String command) {
        String response;
        // Cắt chuỗi để lấy phần lệnh chính, đề phòng user nhập "/start 123"
        String baseCommand = command.split(" ")[0].toLowerCase();

        switch (baseCommand) {
            case "/start":
                response = "Xin chào! Mình là bot SOA. Gõ /help để xem danh sách lệnh.";
                break;
            case "/help":
                response = "Danh sách lệnh hỗ trợ:\n/start - Khởi động bot\n/status - Kiểm tra trạng thái hệ thống";
                break;
            case "/status":
                response = "Hệ thống Backend (Spring Boot) đang hoạt động bình thường \uD83D\uDFE2";
                break;
            default:
                response = "Lệnh không hợp lệ. Vui lòng gõ /help.";
                break;
        }
        sendReply(chatId, response);
    }

    private void sendReply(long chatId, String text) {
        SendMessage message = new SendMessage();
        message.setChatId(String.valueOf(chatId));
        message.setText(text);
        try {
            execute(message);
        } catch (TelegramApiException e) {
            e.printStackTrace();
        }
    }

}