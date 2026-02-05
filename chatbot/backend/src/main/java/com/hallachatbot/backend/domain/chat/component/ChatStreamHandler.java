package com.hallachatbot.backend.domain.chat.component;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import lombok.RequiredArgsConstructor;

/**
 * <b>채팅 스트림 응답 처리 핸들러</b>
 *
 * <p>
 * AI 서비스로부터 들어오는 스트리밍 응답({@link AiServiceResponse})을 실시간으로 분석하여
 * 클라이언트에게 전송할 SSE 이벤트({@link ServerSentEvent})로 변환
 * </p>
 *
 * <ul>
 * <li><b>Context 업데이트:</b> 스트리밍되는 답변 조각(Delta)과 메타데이터를 {@link ChatStreamContext}에 누적</li>
 * <li><b>이벤트 생성:</b> Delta, Metadata, Error 등 타입에 맞는 SSE 이벤트를 생성</li>
 * </ul>
 * @author pwk0131
 */

@Component
@RequiredArgsConstructor
public class ChatStreamHandler {

	private final SseEventFactory sseEventFactory;

	public ServerSentEvent<String> processAiResponse(AiServiceResponse response, ChatStreamContext context) {
		String type = response.type();

		if ("delta".equals(type)) {
			String content = response.content();
			if (content != null) {
				context.appendAnswer(content);
			}
			return sseEventFactory.createDelta(content);

		} else if ("metadata".equals(type)) {
			Map<String, Object> data = response.data();
			context.updateMetadata(data);

			Map<String, Object> eventData = data != null ? new HashMap<>(data) : new HashMap<>();
			eventData.put("chatId", context.getChatId());

			return sseEventFactory.createMetadata(eventData);

		} else if ("error".equals(type)) {
			return sseEventFactory.createError(response.data(), response.message());
		}

		return sseEventFactory.createKeepAlive();
	}
}
