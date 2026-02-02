package com.hallachatbot.backend.global.sse;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.codec.ServerSentEvent;

import com.fasterxml.jackson.databind.ObjectMapper;

class SseEventFactoryTest {

	// 실제 ObjectMapper 사용
	private final SseEventFactory sseEventFactory = new SseEventFactory(new ObjectMapper());

	@Test
	@DisplayName("createDelta: JSON 데이터 내부에 type='delta'와 content가 포함된다")
	void createDelta() {
		// given
		String content = "안녕하세요";

		// when
		ServerSentEvent<String> event = sseEventFactory.createDelta(content);

		// then
		// 1. SSE 이벤트 이름은 null이어야 함 (구현상 설정하지 않음)
		assertThat(event.event()).isNull();

		// 2. Data(JSON) 내부에 type과 content가 있어야 함
		assertThat(event.data()).contains("\"type\":\"delta\"");
		assertThat(event.data()).contains("\"content\":\"안녕하세요\"");
	}

	@Test
	@DisplayName("createMetadata: JSON 데이터 내부에 type='metadata'와 data 객체가 포함된다")
	void createMetadata() {
		// given
		Map<String, Object> data = Map.of("chatId", "123", "tokens", 100);

		// when
		ServerSentEvent<String> event = sseEventFactory.createMetadata(data);

		// then
		assertThat(event.event()).isNull();
		assertThat(event.data()).contains("\"type\":\"metadata\"");
		assertThat(event.data()).contains("\"chatId\":\"123\"");
		assertThat(event.data()).contains("\"tokens\":100");
	}

	@Test
	@DisplayName("createError: JSON 데이터 내부에 type='error'와 메시지가 포함된다")
	void createError() {
		// given
		Map<String, Object> data = Map.of("code", "500");
		String message = "Internal Server Error";

		// when
		ServerSentEvent<String> event = sseEventFactory.createError(data, message);

		// then
		assertThat(event.event()).isNull();
		assertThat(event.data()).contains("\"type\":\"error\"");
		assertThat(event.data()).contains("Internal Server Error");
		assertThat(event.data()).contains("\"code\":\"500\"");
	}

	@Test
	@DisplayName("createKeepAlive: comment 필드에 'keep-alive'가 설정된다")
	void createKeepAlive() {
		// when
		ServerSentEvent<String> event = sseEventFactory.createKeepAlive();

		// then
		// Keep-Alive는 data나 event가 아니라 comment로 전송됨
		assertThat(event.event()).isNull();
		assertThat(event.data()).isNull();
		assertThat(event.comment()).isEqualTo("keep-alive");
	}
}
