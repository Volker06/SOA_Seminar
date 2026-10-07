package com.seminar.telebotdemo.handler;

import org.springframework.stereotype.Component;

/** Chức năng 2 - Chatbot Basics: trả lời tin nhắn văn bản thường. */
@Component
public class ChatResponder {

    public String respond(String input) {
        String lower = input.toLowerCase();
        if (lower.contains("hello") || lower.contains("chào")) {
            return "Chào bạn! Mình là bot demo cho seminar 😄";
        }
        return "Bạn vừa gửi: " + input;
    }
}
