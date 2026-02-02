package com.hallachatbot.backend.global.sse;

import java.util.HashMap;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * SSE(Server-Sent Events) 프로토콜 표준화 및 생성 팩토리
 * <p>
 * 모든 도메인에서 공통으로 사용할 수 있도록
 * 이벤트 포맷(type, data, content)과 JSON 직렬화를 담당합니다.
 * </p>
 *
 * @author pwk0131
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SseEventFactory {

	private final ObjectMapper objectMapper;

	/**
	 * 텍스트 조각(Delta) 이벤트 생성
	 */
	public ServerSentEvent<String> createDelta(String content) {
		return createEvent("delta", null, content);
	}

	/**
	 * 메타데이터(Metadata) 이벤트 생성
	 */
	public ServerSentEvent<String> createMetadata(Map<String, Object> data) {
		return createEvent("metadata", data, null);
	}

	/**
	 * 에러(Error) 이벤트 생성
	 */
	public ServerSentEvent<String> createError(Map<String, Object> data, String message) {
		return createEvent("error", data, message);
	}

	/**
	 * 빈 Keep-Alive 이벤트 생성
	 */
	public ServerSentEvent<String> createKeepAlive() {
		return ServerSentEvent.<String>builder()
			.comment("keep-alive")
			.build();
	}

	/**
	 * 공통 이벤트 빌더 (JSON 직렬화 포함)
	 */
	private ServerSentEvent<String> createEvent(String type, Map<String, Object> data, String content) {
		Map<String, Object> jsonMap = new HashMap<>();
		jsonMap.put("type", type);

		if (data != null) {
			jsonMap.put("data", data);
		}
		if (content != null) {
			jsonMap.put("content", content);
		}

		try {
			String jsonString = objectMapper.writeValueAsString(jsonMap);
			return ServerSentEvent.builder(jsonString).build();
		} catch (JsonProcessingException e) {
			log.error("SSE JSON 직렬화 실패: type={}", type, e);
			// 에러 발생 시 빈 이벤트라도 보내서 스트림 끊김 방지 (혹은 에러 이벤트 전송)
			return ServerSentEvent.builder("{\"type\":\"error\", \"content\":\"Internal Serialization Error\"}")
				.build();
		}
	}
}
