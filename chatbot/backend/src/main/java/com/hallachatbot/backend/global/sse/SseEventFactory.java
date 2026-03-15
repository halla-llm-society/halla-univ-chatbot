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
 * <b>SSE(Server-Sent Events) 이벤트 생성 팩토리</b>
 *
 * <p>
 * 애플리케이션 전역에서 사용되는 SSE 이벤트 객체를 표준화된 포맷으로 생성하는 컴포넌트.
 * 각 도메인(채팅, 알림 등)은 이 팩토리를 통해 규격화된 이벤트(type, data, content)를 발행함.
 * </p>
 *
 * <ul>
 * <li><b>역할:</b> 이벤트 타입별 구조 정의 및 JSON 직렬화 수행</li>
 * <li><b>포맷:</b> { "type": "...", "data": {...}, "content": "..." }</li>
 * </ul>
 *
 * @author pwk0131
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SseEventFactory {

	private final ObjectMapper objectMapper;

	/**
	 * <b>텍스트 조각(Delta) 이벤트 생성</b>
	 *
	 * <p>
	 * AI 답변 스트리밍 시, 생성된 문장의 일부 조각을 전송하기 위해 사용.
	 * </p>
	 *
	 * @param content 전송할 텍스트 조각
	 * @return type="delta"인 SSE 이벤트 객체
	 */
	public ServerSentEvent<String> createDelta(String content) {
		return createEvent("delta", null, content);
	}

	/**
	 * <b>메타데이터(Metadata) 이벤트 생성</b>
	 *
	 * <p>
	 * 토큰 사용량, RAG 검색 결과, 모델 정보 등 부가 정보를 전송하기 위해 사용.
	 * 주로 스트리밍 시작 직후 또는 종료 시점에 발행됨.
	 * </p>
	 *
	 * @param data 메타데이터 키-값 맵
	 * @return type="metadata"인 SSE 이벤트 객체
	 */
	public ServerSentEvent<String> createMetadata(Map<String, Object> data) {
		return createEvent("metadata", data, null);
	}

	/**
	 * <b>에러(Error) 이벤트 생성</b>
	 *
	 * <p>
	 * 스트리밍 도중 발생한 예외 상황을 클라이언트에 알리기 위해 사용.
	 * HTTP 연결을 즉시 끊지 않고, 에러 정보를 담은 이벤트를 보낸 후 우아하게 종료 처리함.
	 * </p>
	 *
	 * @param data    에러 관련 상세 데이터 (코드 등)
	 * @param message 사용자에게 보여줄 에러 메시지
	 * @return type="error"인 SSE 이벤트 객체
	 */
	public ServerSentEvent<String> createError(Map<String, Object> data, String message) {
		return createEvent("error", data, message);
	}

	/**
	 * <b>Keep-Alive 이벤트 생성</b>
	 *
	 * <p>
	 * 연결 타임아웃 방지를 위해 주기적으로 전송하는 빈 이벤트(Heartbeat).
	 * 데이터 필드 없이 주석(Comment) 필드만 포함함.
	 * </p>
	 *
	 * @return comment="keep-alive"인 SSE 이벤트 객체
	 */
	public ServerSentEvent<String> createKeepAlive() {
		return ServerSentEvent.<String>builder()
			.comment("keep-alive")
			.build();
	}

	/**
	 * <b>공통 이벤트 빌더 (내부 메서드)</b>
	 *
	 * <p>
	 * 입력된 필드들을 조합하여 JSON 문자열로 직렬화하고, 최종적인 {@link ServerSentEvent} 객체를 생성.
	 * </p>
	 *
	 * @param type    이벤트 유형 (delta, metadata, error 등)
	 * @param data    구조화된 데이터 맵 (Nullable)
	 * @param content 단순 텍스트 데이터 (Nullable)
	 * @return JSON 문자열을 포함한 SSE 이벤트
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
