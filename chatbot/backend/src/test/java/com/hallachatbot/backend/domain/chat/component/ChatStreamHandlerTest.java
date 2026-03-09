package com.hallachatbot.backend.domain.chat.component;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.codec.ServerSentEvent;

import com.hallachatbot.backend.domain.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;
import com.hallachatbot.backend.global.sse.SseEventFactory;

@ExtendWith(MockitoExtension.class)
class ChatStreamHandlerTest {

	@InjectMocks
	private ChatStreamHandler chatStreamHandler;

	@Mock
	private SseEventFactory sseEventFactory;

	@Test
	@DisplayName("Delta 타입 응답이 오면 Context에 답변을 누적하고 SSE 이벤트를 생성한다")
	void processAiResponse_Delta() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-1", "질문");
		AiServiceResponse response = new AiServiceResponse("delta", "안녕", null, null, null);

		given(sseEventFactory.createDelta(anyString()))
			.willReturn(ServerSentEvent.builder("data").build());

		// when
		chatStreamHandler.processAiResponse(response, context);

		// then
		assertThat(context.getAnswer()).isEqualTo("안녕");
	}

	@Test
	@DisplayName("Metadata 타입 응답이 오면 Context에 메타데이터를 파싱하여 업데이트한다")
	void processAiResponse_Metadata() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-1", "질문");

		// 복잡한 맵 구조 생성 (Token Usage, RAG Decision)
		Map<String, Object> usage = Map.of("total_tokens", 100, "preset", "gpt-4");
		Map<String, Object> rag = Map.of("gate_reason", "search_needed");
		Map<String, Object> data = Map.of("token_usage", usage, "rag", rag);

		AiServiceResponse response = new AiServiceResponse("metadata", null, data, null, null);

		given(sseEventFactory.createMetadata(anyMap()))
			.willReturn(ServerSentEvent.builder("meta").build());

		// when
		chatStreamHandler.processAiResponse(response, context);

		// then
		assertThat(context.getTotalTokens()).isEqualTo(100);
		assertThat(context.getPreset()).isEqualTo("gpt-4");
		assertThat(context.getDecision()).isEqualTo("search_needed");
	}

	@Test
	@DisplayName("Error 타입 응답이 오면 에러 SSE 이벤트를 반환한다")
	void processAiResponse_Error() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-1", "질문");
		AiServiceResponse response = new AiServiceResponse("error", null, null, "문제가 발생했습니다", null);

		given(sseEventFactory.createError(any(), anyString()))
			.willReturn(ServerSentEvent.builder("error-event").build());

		// when
		chatStreamHandler.processAiResponse(response, context);

		// then
		// createError가 호출되었는지 검증
		verify(sseEventFactory).createError(any(), eq("문제가 발생했습니다"));
	}

	@Test
	@DisplayName("알 수 없는 타입의 응답이 오면 KeepAlive(Ping) 이벤트를 반환한다")
	void processAiResponse_UnknownType() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-1", "질문");
		AiServiceResponse response = new AiServiceResponse("unknown_custom_type", null, null, null, null);

		given(sseEventFactory.createKeepAlive())
			.willReturn(ServerSentEvent.builder("ping").build());

		// when
		ServerSentEvent<String> result = chatStreamHandler.processAiResponse(response, context);

		// then
		verify(sseEventFactory).createKeepAlive();
		assertThat(result.data()).isEqualTo("ping");
	}
}
