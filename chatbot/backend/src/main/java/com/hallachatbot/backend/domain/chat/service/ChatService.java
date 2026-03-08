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
import com.hallachatbot.backend.global.exception.ChatStreamErrorHandler;
import com.hallachatbot.backend.global.sse.SseEventFactory;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

/**
 * <b>채팅 도메인 메인 서비스</b>
 *
 * <p>
 * 사용자 요청부터 AI 응답 스트리밍, 그리고 데이터 저장까지의 전체 흐름(Flow)을 조율
 * </p>
 *
 * <ul>
 * <li><b>흐름 제어:</b> 비용 확인 &rarr; 히스토리 조회 &rarr; AI 요청 &rarr; 응답 핸들링 &rarr; 결과 저장</li>
 * <li><b>비동기 처리:</b> Reactor(Flux)를 활용한 논블로킹 스트리밍을 구현하며, DB 저장은 스트림 완료 후 별도 스레드에서 수행</li>
 * </ul>
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
	private final ChatStreamErrorHandler chatStreamErrorHandler;

	/**
	 * 채팅 프로세스 시작 (스트리밍)
	 *
	 * <p>
	 * 1. 월간 사용량 한도를 체크<br>
	 * 2. 현재 세션의 과거 대화 내역을 가져와 문맥을 형성<br>
	 * 3. AI 서비스에 요청을 보내고 실시간 응답(SSE) 스트림을 생성<br>
	 * 4. 스트리밍이 정상적으로 완료되면, 수집된 대화 데이터를 DB에 비동기로 저장
	 * </p>
	 *
	 * @param request 사용자 질문 및 설정이 담긴 요청 객체
	 * @param chatId 사용자 식별을 위한 세션 ID (쿠키)
	 * @return 클라이언트로 전송될 Server-Sent Events 스트림
	 */
	public Flux<ServerSentEvent<String>> startChat(ChatRequest request, String chatId) {
		// 1. 비용 한도 확인
		usageService.checkMonthlyLlmUsage();

		// 2. 대화 히스토리 조회
		List<ChatHistoryResponse> history = getChatHistory(chatId);

		// 스트림 동안 상태(답변, 메타데이터 등)를 누적할 객체 생성
		ChatStreamContext context = new ChatStreamContext(chatId, request.userInput());

		// 3. AI 서비스 호출 및 스트리밍 변환
		Flux<ServerSentEvent<String>> eventFlux = aiServiceClient.streamChat(request, history)
			.map(aiResponse -> chatStreamHandler.processAiResponse(aiResponse, context))
			.onErrorResume(chatStreamErrorHandler::handleStreamError)
			.doOnComplete(() -> {
				// 저장 로직 비동기 실행
				if (context.hasAnswer()) {
					Flux.just(context)
						.publishOn(Schedulers.boundedElastic())
						.subscribe(chatWriter::saveChatData);
				}
			});

		// 4. 초기 이벤트 주입 (Metadata, Warning)
		return injectInitialEvents(eventFlux, chatId);
	}

	/**
	 * 대화 히스토리 조회
	 *
	 * <p>
	 * 주어진 chatId에 해당하는 최근 대화 내역(6개)을 조회하여 반환<br>
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
