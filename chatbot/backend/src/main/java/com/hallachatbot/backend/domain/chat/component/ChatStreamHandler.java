package com.hallachatbot.backend.domain.chat.component;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
public class ChatStreamHandler {

	private final SseEventFactory sseEventFactory;

	public ServerSentEvent<String> processAiResponse(AiServiceResponse response, ChatStreamContext context) {
		String type = response.getType();

		if ("delta".equals(type)) {
			String content = response.getContent();
			if (content != null) {
				context.appendAnswer(content);
			}
			return sseEventFactory.createDelta(content);

		} else if ("metadata".equals(type)) {
			Map<String, Object> data = response.getData();
			context.updateMetadata(data);

			Map<String, Object> eventData = data != null ? new HashMap<>(data) : new HashMap<>();
			eventData.put("chatId", context.getChatId());

			return sseEventFactory.createMetadata(eventData);

		} else if ("error".equals(type)) {
			return sseEventFactory.createError(response.getData(), response.getMessage());
		}

		return sseEventFactory.createKeepAlive();
	}
}
