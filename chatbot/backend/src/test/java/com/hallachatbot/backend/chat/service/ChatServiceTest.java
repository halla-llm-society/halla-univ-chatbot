package com.hallachatbot.backend.chat.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.BDDMockito.given;
import static org.mockito.BDDMockito.willThrow;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import java.util.Collections;
import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.Spy;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.test.util.ReflectionTestUtils;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.chat.client.AiServiceClient;
import com.hallachatbot.backend.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.chat.entity.ChatMessage;
import com.hallachatbot.backend.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.global.errorcode.CostErrorCode;
import com.hallachatbot.backend.global.exception.CostException;
import com.hallachatbot.backend.usage.service.UsageService;

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
	private ChatMessageRepository chatMessageRepository;

	@Mock
	private ChatTokenUsageRepository chatTokenUsageRepository;

	@Mock
	private ChatMetadataRepository chatMetadataRepository;

	@Spy
	private ObjectMapper objectMapper = new ObjectMapper();

	@Test
	@DisplayName("비용 한도를 초과하면 채팅을 시작하지 않고 예외가 발생한다")
	void startChat_Fail_CostExceeded() {
		// given
		ChatRequest request = new ChatRequest();
		String chatId = "test-chat-id";

		// [수정됨] void 메서드에 대한 BDDMockito 예외 발생 설정
		willThrow(new CostException(CostErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED))
			.given(usageService).checkLlmUsage();

		// when & then
		assertThatThrownBy(() -> chatService.startChat(request, chatId, false))
			.isInstanceOf(CostException.class)
			.hasFieldOrPropertyWithValue("errorCode", CostErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED);

		// AI 서비스는 호출되지 않아야 함
		verify(aiServiceClient, never()).streamChat(any(), any());
	}

	@Test
	@DisplayName("정상적인 채팅 요청 시 스트림을 반환하고 메타데이터 이벤트를 먼저 전송한다")
	void startChat_Success() {
		// given
		String chatId = "valid-chat-id";
		String userInput = "안녕하세요";
		ChatRequest request = new ChatRequest();

		ReflectionTestUtils.setField(request, "userInput", userInput);
		ReflectionTestUtils.setField(request, "language", ChatRequest.Language.KOR);

		// 1. 히스토리 조회 Mock
		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(Collections.emptyList());

		// 2. AI 서비스 응답 Mock (Flux)
		AiServiceResponse deltaResponse = new AiServiceResponse();
		ReflectionTestUtils.setField(deltaResponse, "type", "delta");
		ReflectionTestUtils.setField(deltaResponse, "content", "반갑습니다.");

		given(aiServiceClient.streamChat(any(ChatRequest.class), anyList()))
			.willReturn(Flux.just(deltaResponse));

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId, false);

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

		// 검증: 비용 체크가 호출되었는지
		verify(usageService, times(1)).checkLlmUsage();
	}

	@Test
	@DisplayName("쿠키가 변조된 경우 경고 메시지 이벤트가 포함된다")
	void startChat_TamperedCookie() {
		// given
		String chatId = "new-chat-id";
		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "질문");

		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(Collections.emptyList());

		given(aiServiceClient.streamChat(any(), any()))
			.willReturn(Flux.empty()); // AI 응답 없음

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId, true);

		// then
		StepVerifier.create(resultFlux)
			.expectNextCount(1) // metadata
			.assertNext(event -> {
				// 경고 메시지 이벤트 확인
				assertThat(event.data()).contains("유효하지 않은 쿠키가 감지되어");
			})
			.verifyComplete();
	}

	@Test
	@DisplayName("AI 응답에 메타데이터와 에러 타입이 포함된 경우를 처리하고 DB에 저장한다")
	void startChat_WithMetadataAndError() {
		// given
		String chatId = "test-chat-id";
		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "질문");
		ReflectionTestUtils.setField(request, "language", ChatRequest.Language.KOR);

		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(Collections.emptyList());

		// 다양한 타입의 응답 시뮬레이션
		AiServiceResponse delta = new AiServiceResponse();
		ReflectionTestUtils.setField(delta, "type", "delta");
		ReflectionTestUtils.setField(delta, "content", "답변내용");

		AiServiceResponse metadata = new AiServiceResponse();
		ReflectionTestUtils.setField(metadata, "type", "metadata");
		// RAG 및 Token 정보가 있는 복잡한 맵 구조
		Map<String, Object> ragMap = Map.of("gate_reason", "retrieval_needed");
		Map<String, Object> usageMap = Map.of("preset", "gpt-4", "total_tokens", 150);
		Map<String, Object> dataMap = new java.util.HashMap<>(); // 가변 Map
		dataMap.put("rag", ragMap);
		dataMap.put("token_usage", usageMap);
		ReflectionTestUtils.setField(metadata, "data", dataMap);

		AiServiceResponse error = new AiServiceResponse();
		ReflectionTestUtils.setField(error, "type", "error");
		ReflectionTestUtils.setField(error, "message", "일시적 오류");

		// 순서대로 방출
		given(aiServiceClient.streamChat(any(), anyList()))
			.willReturn(Flux.just(delta, metadata, error));

		// when
		Flux<ServerSentEvent<String>> resultFlux = chatService.startChat(request, chatId, false);

		// then
		StepVerifier.create(resultFlux)
			.expectNextCount(1) // 초기 metadata(chatId)
			.assertNext(event -> assertThat(event.data()).contains("delta").contains("답변내용"))
			.assertNext(event -> {
				assertThat(event.data()).contains("metadata");
				assertThat(event.data()).contains("retrieval_needed"); // RAG 정보 확인
				assertThat(event.data()).contains("gpt-4"); // Token 정보 확인
			})
			.assertNext(event -> {
				assertThat(event.data()).contains("error");
				assertThat(event.data()).contains("일시적 오류");
			})
			.verifyComplete();

		// 비동기 저장 로직 검증 (조금 기다렸다가 확인하거나 verify timeout 사용)
		// 주의: Schedulers.boundedElastic() 때문에 약간의 지연이 있을 수 있음
		verify(chatMessageRepository, org.mockito.Mockito.timeout(1000).times(1)).save(any(ChatMessage.class));
		verify(chatTokenUsageRepository, org.mockito.Mockito.timeout(1000).times(1)).save(any());
		verify(chatMetadataRepository, org.mockito.Mockito.timeout(1000).times(1)).save(any());
	}
}
