package com.hallachatbot.backend.global.exception;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.TimeoutException;

import org.springframework.core.codec.DecodingException;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.hallachatbot.backend.global.errorcode.ChatErrorCode;
import com.hallachatbot.backend.global.errorcode.ErrorCode;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

/**
 * <b>채팅 스트리밍 중 발생하는 예외를 처리하는 핸들러.</b>
 * <p>
 * GlobalExceptionHandler는 응답 헤더가 전송된 이후(스트리밍 시작 후)의 에러를 잡지 못하므로,
 * Flux 내부에서 발생하는 에러는 이 핸들러를 통해 SSE 'error' 이벤트로 변환하여 전송함.
 * </p>
 * @author pwk0131
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ChatStreamErrorHandler {

	private final SseEventFactory sseEventFactory;

	/**
	 * 예외(Throwable)를 받아 에러 정보를 담은 SSE 이벤트 Flux로 반환
	 * (onErrorResume 연산자에서 사용)
	 */
	public Flux<ServerSentEvent<String>> handleStreamError(Throwable error) {
		ErrorCode errorCode = determineErrorCode(error);

		// 1. 에러 로그 출력
		log.error("[Stream Error] Cause: {}, Message: {}", error.getClass().getSimpleName(), error.getMessage());

		// 2. 클라이언트에 전달할 에러 데이터 구성
		Map<String, Object> errorData = Map.of(
			"code", errorCode.name(),
			"message", errorCode.getMessage()
		);

		// 3. 'error' 타입의 SSE 이벤트 생성 및 반환
		// 스트림을 끊지 않고 마지막으로 에러 이벤트를 보낸 후 정상 종료(Complete) 처리됨
		return Flux.just(sseEventFactory.createError(errorData, errorCode.getMessage()));
	}

	/**
	 * 예외 타입에 따라 적절한 ErrorCode를 매핑.
	 */
	private ErrorCode determineErrorCode(Throwable error) {

		// 1. 타임아웃 (AI 서비스 응답 지연)
		if (error instanceof TimeoutException) {
			return ChatErrorCode.AI_SERVICE_UNAVAILABLE;
		}

		// 2. 데이터 파싱/디코딩 실패 (JSON 형식 오류 등)
		if (error instanceof DecodingException || error instanceof JsonProcessingException) {
			return ChatErrorCode.AI_RESPONSE_PARSING_FAILED;
		}

		// 3. 입출력/네트워크 중단
		if (error instanceof IOException) {
			return ChatErrorCode.STREAMING_INTERRUPTED;
		}

		// 기본값: AI 서비스 내부 오류
		return ChatErrorCode.AI_SERVICE_ERROR;
	}
}
