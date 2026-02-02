package com.hallachatbot.backend.domain.chat.service;

import java.util.List;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;

import com.hallachatbot.backend.domain.chat.component.ChatReader;
import com.hallachatbot.backend.domain.chat.component.ChatStreamHandler;
import com.hallachatbot.backend.domain.chat.component.ChatWriter;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.usage.service.UsageService;
import com.hallachatbot.backend.global.client.service.AiServiceClient;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

/**
 * 챗봇 서비스 로직
 *
 * <p>
 * 비용 확인 -> 히스토리 조회 -> AI 요청 -> 스트리밍 -> DB 저장
 * </p>
 *
 * @author pwk0131
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class ChatService {

	private final UsageService usageService;
	private final AiServiceClient aiServiceClient;
	private final SseEventFactory sseEventFactory;

	private final ChatReader chatReader;
	private final ChatWriter chatWriter;
	private final ChatStreamHandler chatStreamHandler;

	/**
	 * 채팅 스트리밍 시작
	 *
	 * @param request 사용자 요청 DTO
	 * @param chatId 세션 ID (쿠키)
	 * @return SSE 스트림
	 */
	public Flux<ServerSentEvent<String>> startChat(ChatRequest request, String chatId) {
		// 1. 비용 한도 확인
		usageService.checkLlmUsage();

		// 2. 대화 히스토리 조회
		List<ChatHistoryResponse> history = getChatHistory(chatId);

		// 스트림 동안 상태(답변, 메타데이터 등)를 누적할 객체 생성
		ChatStreamContext context = new ChatStreamContext(chatId, request.getUserInput());

		// 3. AI 서비스 호출 및 스트리밍 변환
		Flux<ServerSentEvent<String>> eventFlux = aiServiceClient.streamChat(request, history)
			.map(aiResponse -> chatStreamHandler.processAiResponse(aiResponse, context))
			.doOnComplete(() -> {
				// 저장 로직 비동기 실행
				Flux.just(context)
					.publishOn(Schedulers.boundedElastic())
					.subscribe(chatWriter::saveChatData);
			});

		// 4. 초기 이벤트 주입 (Metadata, Warning)
		return injectInitialEvents(eventFlux, chatId);
	}

	/**
	 * 대화 히스토리 조회
	 *
	 * <p>
	 * 주어진 chatId에 해당하는 최근 대화 내역(최대 6개)을 조회하여 반환<br>
	 * 컨트롤러의 히스토리 조회 API와 내부 AI 요청 시 대화 문맥 제공용으로 공통 사용
	 * </p>
	 *
	 * @param chatId 사용자 식별 ID (쿠키 값)
	 * @return 시간순(과거 - > 현재)으로 정렬된 대화 내역 리스트 (User/Assistant 쌍)
	 */
	public List<ChatHistoryResponse> getChatHistory(String chatId) {
		return chatReader.getChatHistory(chatId);
	}

	private Flux<ServerSentEvent<String>> injectInitialEvents(Flux<ServerSentEvent<String>> mainFlux, String chatId) {
		ServerSentEvent<String> metaEvent = sseEventFactory.createMetadata(Map.of("chatId", chatId));
		return Flux.just(metaEvent).concatWith(mainFlux);
	}
}
