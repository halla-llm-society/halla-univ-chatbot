package com.hallachatbot.backend.global.exception;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

import java.util.Map;
import java.util.concurrent.TimeoutException;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.codec.ServerSentEvent;

import com.hallachatbot.backend.global.errorcode.ChatErrorCode;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ChatStreamErrorHandlerTest {

	@InjectMocks
	private ChatStreamErrorHandler chatStreamErrorHandler;

	@Mock
	private SseEventFactory sseEventFactory;

	@Test
	@DisplayName("TimeoutException이 발생하면 AI_SERVICE_UNAVAILABLE 에러 이벤트로 변환된다")
	void handleStreamError_Timeout() {
		// given
		TimeoutException error = new TimeoutException("Time out occurred");

		ServerSentEvent<String> expectedEvent = ServerSentEvent.<String>builder()
			.event("error")
			.data("{\"code\":\"AI_SERVICE_UNAVAILABLE\"}")
			.build();

		given(sseEventFactory.createError(anyMap(), any()))
			.willReturn(expectedEvent);

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatStreamErrorHandler.handleStreamError(error);

		// then
		StepVerifier.create(resultFlux)
			.expectNext(expectedEvent)
			.verifyComplete();

		// Verify: factory가 올바른 에러 코드로 호출되었는지 검증
		verify(sseEventFactory).createError(
			argThat(map -> "AI_SERVICE_UNAVAILABLE".equals(map.get("code"))),
			eq(ChatErrorCode.AI_SERVICE_UNAVAILABLE.getMessage())
		);
	}

	@Test
	@DisplayName("알 수 없는 예외가 발생하면 AI_SERVICE_ERROR 에러 이벤트로 변환된다")
	void handleStreamError_UnknownException() {
		// given
		RuntimeException error = new RuntimeException("Something went wrong");

		ServerSentEvent<String> expectedEvent = ServerSentEvent.<String>builder()
			.event("error")
			.data("{\"code\":\"AI_SERVICE_ERROR\"}")
			.build();

		given(sseEventFactory.createError(anyMap(), any()))
			.willReturn(expectedEvent);

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatStreamErrorHandler.handleStreamError(error);

		// then
		StepVerifier.create(resultFlux)
			.expectNext(expectedEvent)
			.verifyComplete();
	}

	// Mockito ArgumentMatcher를 위한 헬퍼 메서드
	private Map<String, Object> argThat(java.util.function.Predicate<Map<String, Object>> predicate) {
		return org.mockito.ArgumentMatchers.argThat(predicate::test);
	}
}
