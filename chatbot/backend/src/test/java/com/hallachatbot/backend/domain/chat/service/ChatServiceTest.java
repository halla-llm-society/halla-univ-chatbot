package com.hallachatbot.backend.domain.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.BDDMockito.given;
import static org.mockito.BDDMockito.willThrow;
import static org.mockito.Mockito.doNothing;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.timeout;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.codec.ServerSentEvent;

import com.hallachatbot.backend.domain.chat.component.ChatReader;
import com.hallachatbot.backend.domain.chat.component.ChatStreamHandler;
import com.hallachatbot.backend.domain.chat.component.ChatWriter;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.usage.service.UsageService;
import com.hallachatbot.backend.domain.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.domain.chat.client.service.AiServiceClient;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.ChatStreamErrorHandler;
import com.hallachatbot.backend.global.exception.UsageException;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

@ExtendWith(MockitoExtension.class)
class ChatServiceTest {

	@InjectMocks
	private ChatService chatService;

	@Mock
	private UsageService usageService;

	@Mock
	private AiServiceClient aiServiceClient;

	@Mock
	private ChatReader chatReader;

	@Mock
	private ChatWriter chatWriter;

	@Mock
	private ChatStreamHandler chatStreamHandler;

	@Mock
	private SseEventFactory sseEventFactory;

	@Mock
	private ChatStreamErrorHandler chatStreamErrorHandler;

	@Test
	@DisplayName("비용 한도를 초과하면 채팅을 시작하지 않고 예외가 발생한다")
	void startChat_Fail_CostExceeded() {
		// given
		ChatRequest request = new ChatRequest("질문", ChatRequest.Language.KOR);
		String chatId = "test-chat-id";

		// void 메서드에 대한 BDDMockito 예외 발생 설정
		willThrow(new UsageException(UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED))
			.given(usageService).checkMonthlyLlmUsage();

		// when & then
		assertThatThrownBy(() -> chatService.startChat(request, chatId))
			.isInstanceOf(UsageException.class)
			.hasFieldOrPropertyWithValue("errorCode", UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED);

		// AI 서비스는 호출되지 않아야 함
		verify(aiServiceClient, never()).streamChat(any(), any());
	}

	@Test
	@DisplayName("정상적인 채팅 요청 시 스트림을 반환하고 메타데이터 이벤트를 먼저 전송한다")
	void startChat_Success() {
		// given
		String chatId = "valid-chat-id";
		ChatRequest request = new ChatRequest("안녕하세요", ChatRequest.Language.KOR);

		// 1. 히스토리 조회 Mock
		given(chatReader.getChatHistory(chatId))
			.willReturn(Collections.emptyList());

		// 2. 초기 Metadata 이벤트 Mock (SseEventFactory)
		String metadataJson = "{\"type\":\"metadata\",\"chatId\":\"" + chatId + "\"}";
		given(sseEventFactory.createMetadata(anyMap()))
			.willReturn(ServerSentEvent.builder(metadataJson).build());

		// 3. AI 응답 및 핸들러 Mock
		AiServiceResponse deltaResponse = new AiServiceResponse("delta", "반갑습니다.", null, null, null);

		// 4. AI 클라이언트가 응답을 방출
		given(aiServiceClient.streamChat(any(ChatRequest.class), anyList()))
			.willReturn(Flux.just(deltaResponse));

		// 5. ChatStreamHandler가 null이 아닌 SSE 이벤트를 반환하도록 Stubbing 추가
		String deltaJson = "{\"type\":\"delta\",\"content\":\"반갑습니다.\"}";
		given(chatStreamHandler.processAiResponse(any(), any()))
			.willAnswer(invocation -> {
				AiServiceResponse response = invocation.getArgument(0);
				ChatStreamContext context = invocation.getArgument(1);

				// Mock이지만 실제 로직처럼 context에 답변을 넣어줘야 hasAnswer()가 true가 됨
				if ("delta".equals(response.type())) {
					context.appendAnswer(response.content());
				}

				return ServerSentEvent.builder(deltaJson).build();
			});

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId);

		// then
		StepVerifier.create(resultFlux)
			// 1. 첫 번째 이벤트는 메타데이터(chatId) 여야 함
			.assertNext(event -> {
				assertThat(event.data()).contains("\"type\":\"metadata\"");
				assertThat(event.data()).contains(chatId);
			})
			// 2. 두 번째 이벤트는 AI 응답(delta) 여야 함
			.assertNext(event -> {
				assertThat(event.data()).contains("\"type\":\"delta\"");
				assertThat(event.data()).contains("반갑습니다.");
			})
			.verifyComplete();

		// 검증
		verify(usageService).checkMonthlyLlmUsage();
		verify(chatWriter, timeout(1000)).saveChatData(any());
	}

	@Test
	@DisplayName("AI 응답에 메타데이터와 에러 타입이 포함된 경우를 처리하고 DB에 저장한다")
	void startChat_WithMetadataAndError() {
		// given
		String chatId = "test-chat-id";
		ChatRequest request = new ChatRequest("질문", ChatRequest.Language.KOR);

		given(chatReader.getChatHistory(chatId))
			.willReturn(Collections.emptyList());

		// 초기 이벤트 Mock
		given(sseEventFactory.createMetadata(anyMap()))
			.willReturn(ServerSentEvent.builder("{\"type\":\"metadata\"}").build());

		// 다양한 타입의 AI 응답 시뮬레이션
		AiServiceResponse delta = new AiServiceResponse("delta", null, null, null, null);
		AiServiceResponse metadata = new AiServiceResponse("metadata", null, null, null, null);
		AiServiceResponse error = new AiServiceResponse("error", null, null, null, null);

		// AI Client Mock
		given(aiServiceClient.streamChat(any(), anyList()))
			.willReturn(Flux.just(delta, metadata, error));

		// Handler Mock - 각 응답에 대해 적절한 SSE 반환 설정
		given(chatStreamHandler.processAiResponse(eq(delta), any()))
			.willAnswer(invocation -> {
				ChatStreamContext context = invocation.getArgument(1);
				context.appendAnswer("답변내용"); // Context 업데이트
				return ServerSentEvent.builder("{\"type\":\"delta\",\"content\":\"답변내용\"}").build();
			});

		given(chatStreamHandler.processAiResponse(eq(metadata), any()))
			.willReturn(
				ServerSentEvent.builder("{\"type\":\"metadata\",\"rag\":\"retrieval_needed\",\"preset\":\"gpt-4\"}")
					.build());

		given(chatStreamHandler.processAiResponse(eq(error), any()))
			.willReturn(ServerSentEvent.builder("{\"type\":\"error\",\"message\":\"일시적 오류\"}").build());

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId);

		// then
		StepVerifier.create(resultFlux)
			.expectNextCount(1) // 초기 metadata
			.assertNext(event -> assertThat(event.data()).contains("delta").contains("답변내용"))
			.assertNext(event -> {
				assertThat(event.data()).contains("metadata");
				assertThat(event.data()).contains("retrieval_needed");
				assertThat(event.data()).contains("gpt-4");
			})
			.assertNext(event -> {
				assertThat(event.data()).contains("error");
				assertThat(event.data()).contains("일시적 오류");
			})
			.verifyComplete();

		// ChatWriter(저장 담당)가 호출되었는지 검증
		verify(chatWriter, timeout(1000).times(1)).saveChatData(any());
	}

	@Test
	@DisplayName("스트리밍이 정상 종료되고 비용이 0보다 크면 UsageService가 비동기로 호출되어야 한다.")
	void startChat_CallsUsageService_WhenCostIsGreaterThanZero() {
		// given
		String chatId = "test-chat-session";
		ChatRequest request = new ChatRequest("안녕", ChatRequest.Language.KOR);

		// 의존성 Mocking 세팅
		doNothing().when(usageService).checkMonthlyLlmUsage();
		when(chatReader.getChatHistory(chatId)).thenReturn(Collections.emptyList());
		when(sseEventFactory.createMetadata(any())).thenReturn(
			ServerSentEvent.<String>builder().event("metadata").build());

		// AI 서비스 응답 조작 (비용이 포함된 메타데이터 응답을 시뮬레이션)
		AiServiceResponse fakeDelta = new AiServiceResponse("delta", "반가워요", null, null, null);
		AiServiceResponse fakeMeta = new AiServiceResponse("metadata", null,
			Map.of("token_usage", Map.of("total_cost_usd", "0.0055")), null, null);

		when(aiServiceClient.streamChat(eq(request), anyList())).thenReturn(Flux.just(fakeDelta, fakeMeta));

		// Handler가 Context를 업데이트 하도록 조작
		when(chatStreamHandler.processAiResponse(any(), any())).thenAnswer(invocation -> {
			AiServiceResponse resp = invocation.getArgument(0);
			ChatStreamContext ctx = invocation.getArgument(1);
			if ("delta".equals(resp.type())) {
				ctx.appendAnswer(resp.content());
			}
			if ("metadata".equals(resp.type())) {
				ctx.updateMetadata(resp.data());
			}
			return ServerSentEvent.<String>builder().build();
		});

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId);

		// then
		StepVerifier.create(resultFlux)
			.expectNextCount(3) // 초기 메타데이터 1개 + delta 1개 + meta 1개
			.verifyComplete();

		// Schedulers.boundedElastic()을 타고 비동기로 실행되므로 timeout으로 대기 후 검증
		verify(chatWriter, timeout(1000).times(1)).saveChatData(any(ChatStreamContext.class));
		verify(usageService, timeout(1000).times(1)).addMonthlyLlmUsage(any(BigDecimal.class));
	}
}
