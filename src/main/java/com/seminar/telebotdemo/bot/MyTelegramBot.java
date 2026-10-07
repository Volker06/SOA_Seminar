package com.seminar.telebotdemo.bot;

import com.seminar.telebotdemo.handler.ChatResponder;
import com.seminar.telebotdemo.handler.CommandHandler;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.telegram.telegrambots.bots.TelegramLongPollingBot;
import org.telegram.telegrambots.meta.api.methods.send.SendMessage;
import org.telegram.telegrambots.meta.api.objects.Update;
import org.telegram.telegrambots.meta.exceptions.TelegramApiException;

/**
 * Chỉ làm 2 việc: nhận update từ Telegram -> chuyển cho handler phù hợp -> gửi kết quả.
 * Logic nghiệp vụ nằm ở package handler.
 */
@Component
@SuppressWarnings("deprecation")
public class MyTelegramBot extends TelegramLongPollingBot {

    private static final Logger log = LoggerFactory.getLogger(MyTelegramBot.class);

    private final CommandHandler commandHandler;
    private final ChatResponder chatResponder;

    @Value("${telegram.bot.username}")
    private String botUsername;

    @Value("${telegram.bot.token}")
    private String botToken;

    public MyTelegramBot(CommandHandler commandHandler, ChatResponder chatResponder) {
        this.commandHandler = commandHandler;
        this.chatResponder = chatResponder;
    }

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
        if (!update.hasMessage() || !update.getMessage().hasText()) {
            return;
        }
        String text = update.getMessage().getText();
        long chatId = update.getMessage().getChatId();

        String reply = text.startsWith("/")
                ? commandHandler.handle(text)
                : chatResponder.respond(text);
        sendReply(chatId, reply);
    }

    private void sendReply(long chatId, String text) {
        SendMessage message = new SendMessage(String.valueOf(chatId), text);
        try {
            execute(message);
        } catch (TelegramApiException e) {
            log.error("Gửi tin nhắn thất bại (chatId={})", chatId, e);
        }
    }
}
