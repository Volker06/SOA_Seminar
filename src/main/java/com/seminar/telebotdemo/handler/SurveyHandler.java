package com.seminar.telebotdemo.handler;

import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Component;
import com.seminar.telebotdemo.survey.SurveyResultStore;

@Component
public class SurveyHandler {

    public static final String PREFIX = "SURVEY:";

    public record Reply(String text, String buttonLabel, String buttonData) {
        public static Reply of(String text) {
            return new Reply(text, null, null);
        }
    }

    public record CallbackResult(String toast, String editedText, Reply next) {
    }

    private enum Step {
        AWAITING_REASON, AWAITING_FEEDBACK
    }

    private record Session(String orderId, int stars, Step step) {
    }

    private final Map<Long, Session> sessions = new ConcurrentHashMap<>();
    private final Set<String> rated = ConcurrentHashMap.newKeySet();

    private final SurveyResultStore store;

    public SurveyHandler(SurveyResultStore store) {
        this.store = store;
    }

    public CallbackResult handleCallback(long chatId, String data) {
        String[] p = data.split(":");
        if (p.length == 4 && "RATE".equals(p[1])) {
            return onRate(chatId, p[2], parseStars(p[3]));
        }
        if (p.length == 3 && "NOFB".equals(p[1])) {
            return onNoFeedback(chatId, p[2]);
        }
        return new CallbackResult("Nút không hợp lệ", null, null);
    }

    private CallbackResult onRate(long chatId, String orderId, int stars) {
        if (stars < 1 || stars > 5) {
            return new CallbackResult("Số sao không hợp lệ", null, null);
        }
        if (!rated.add(chatId + ":" + orderId)) {
            return new CallbackResult("Bạn đã đánh giá đơn này rồi", null, null);
        }

        String edited = "Bạn đã đánh giá đơn " + orderId + ": " + "⭐".repeat(stars) + " (" + stars + "/5)";

        if (stars <= 2) {
            sessions.put(chatId, new Session(orderId, stars, Step.AWAITING_REASON));
            return new CallbackResult("Đã ghi nhận " + stars + "⭐", edited, Reply.of(
                    "Rất tiếc vì trải nghiệm của bạn chưa tốt.\n"
                            + "Bạn có thể cho mình biết vì sao bạn chưa hài lòng không? "
                            + "Hãy nhắn lý do bên dưới (hoặc gõ /skip để bỏ qua)."));
        }

        sessions.put(chatId, new Session(orderId, stars, Step.AWAITING_FEEDBACK));
        return new CallbackResult("Đã ghi nhận " + stars + "⭐", edited, new Reply(
                "Cảm ơn bạn đã hài lòng với dịch vụ!\n"
                        + "Bạn có muốn góp ý gì thêm để chúng mình phục vụ tốt hơn không? "
                        + "Hãy nhắn góp ý bên dưới, hoặc bấm nút nếu không có.",
                "Không, cảm ơn", PREFIX + "NOFB:" + orderId));
    }

    private CallbackResult onNoFeedback(long chatId, String orderId) {
        Session s = sessions.get(chatId);
        if (s == null || !s.orderId().equals(orderId) || s.step() != Step.AWAITING_FEEDBACK) {
            return new CallbackResult("Khảo sát đã hoàn tất", "Khảo sát này đã hoàn tất.", null);
        }
        sessions.remove(chatId);
        return new CallbackResult("Đã ghi nhận", "Bạn không có góp ý thêm.", Reply.of(finish(chatId, s, null)));
    }

    public boolean hasPending(long chatId) {
        return sessions.containsKey(chatId);
    }

    public String handleText(long chatId, String text) {
        Session s = sessions.remove(chatId);
        if (s == null) {
            return "Hiện không có khảo sát nào đang chờ.";
        }
        return finish(chatId, s, text.trim());
    }

    public String skip(long chatId) {
        Session s = sessions.remove(chatId);
        if (s == null) {
            return "Hiện không có khảo sát nào đang chờ.";
        }
        return finish(chatId, s, null);
    }

    private String finish(long chatId, Session s, String comment) {
        store.save(chatId, s.orderId(), s.stars(), comment);

        if (s.stars() <= 2) {
            return "Cảm ơn bạn đã chia sẻ. Chúng mình đã ghi nhận phản hồi của bạn và sẽ cải thiện dịch vụ.";
        }
        return "💙 Cảm ơn bạn đã dành thời gian đánh giá! Hẹn gặp lại bạn ở lần sử dụng tiếp theo.";
    }

    private static int parseStars(String raw) {
        try {
            return Integer.parseInt(raw);
        } catch (NumberFormatException e) {
            return -1;
        }
    }
}
