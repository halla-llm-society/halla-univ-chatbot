package com.hallachatbot.backend.domain.chat.service;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.entity.ChatMetadata;
import com.hallachatbot.backend.domain.chat.entity.ChatTokenUsage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.domain.usage.service.UsageService;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;
import com.hallachatbot.backend.global.client.service.AiServiceClient;

import lombok.Getter;
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
	private final ChatMessageRepository chatMessageRepository;
	private final ChatTokenUsageRepository chatTokenUsageRepository;
	private final ChatMetadataRepository chatMetadataRepository;
	private final ObjectMapper objectMapper;

	/**
	 * 채팅 스트리밍 시작
	 *
	 * @param request 사용자 요청 DTO
	 * @param chatId 세션 ID (쿠키)
	 * @return SSE 스트림
	 */
	public Flux<ServerSentEvent<String>> startChat(ChatRequest request, String chatId) {
		// 1. 비용 한도 확인 (예외 발생 시 GlobalExceptionHandler 처리)
		usageService.checkLlmUsage();

		// 2. 대화 히스토리 조회
		List<ChatHistoryResponse> history = getChatHistory(chatId);

		// 스트림 동안 상태(답변, 메타데이터 등)를 누적할 객체 생성
		StreamState state = new StreamState(chatId, request.getUserInput());

		// 3. AI 서비스 호출 및 스트리밍 변환
		Flux<ServerSentEvent<String>> eventFlux = aiServiceClient.streamChat(request, history)
			.map(aiResponse -> processAiResponse(aiResponse, state))
			.doOnComplete(() -> saveChatData(state)); // 스트림 완료 시 DB 저장

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
		// 1. DB 조회 (최신순 6개)
		List<ChatMessage> rawHistory = chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId);

		// 2. 변환 (역순 정렬 및 DTO 매핑)
		return convertToHistoryResponse(rawHistory);
	}

	/**
	 * AI 응답 하나를 처리하고 SSE 이벤트로 변환
	 */
	private ServerSentEvent<String> processAiResponse(AiServiceResponse response, StreamState state) {
		String type = response.getType();

		if ("delta".equals(type)) {
			String content = response.getContent();
			if (content != null) {
				state.appendAnswer(content);
			}
			return createSseEvent("delta", null, content);
		} else if ("metadata".equals(type)) {
			Map<String, Object> data = response.getData();
			state.updateMetadata(data);

			// 클라이언트에 보낼 때는 chatId를 포함
			Map<String, Object> eventData = data != null ? new HashMap<>(data) : new HashMap<>();
			eventData.put("chatId", state.getChatId());

			return createSseEvent("metadata", eventData, null);
		} else if ("error".equals(type)) {
			return createSseEvent("error", response.getData(), response.getMessage());
		}

		return ServerSentEvent.<String>builder().comment("keep-alive").build();
	}

	/**
	 * 스트림 완료 후 누적된 데이터를 DB에 저장 (비동기)
	 */
	private void saveChatData(StreamState state) {
		if (state.getAnswerBuilder().isEmpty()
			&& (state.getMetadataMap() == null || state.getMetadataMap().isEmpty())
			&& (state.getTotalTokens() == null || state.getTotalTokens() == 0)) {
			return;
		}

		// 1. ChatMessage 저장
		ChatMessage chatMessage = ChatMessage.builder()
			.chatId(state.getChatId())
			.question(state.getQuestion())
			.answer(state.getAnswer())
			.decision(state.getDecision())
			.build();

		// blocking IO를 별도 스레드에서 실행 (Reactor 권장)
		// 실제 운영 시에는 ReactiveMongoRepository를 쓰거나 subscribeOn 사용
		Flux.just(chatMessage)
			.publishOn(Schedulers.boundedElastic())
			.doOnNext(msg -> {
				ChatMessage savedMsg = chatMessageRepository.save(msg);
				String messageId = savedMsg.getId();
				saveTokenAndMetadata(state, messageId);
			})
			.subscribe(
				success -> {
				},
				error -> log.error("채팅 데이터 저장 실패: chatId={}", state.getChatId(), error)
			);
	}

	private void saveTokenAndMetadata(StreamState state, String messageId) {
		// 2. TokenUsage 저장
		ChatTokenUsage tokenUsage = ChatTokenUsage.builder()
			.messageId(messageId)
			.preset(state.getPreset())
			.totalTokens(state.getTotalTokens())
			.build();
		chatTokenUsageRepository.save(tokenUsage);

		// 3. Metadata 저장
		ChatMetadata metadata = ChatMetadata.builder()
			.messageId(messageId)
			.metadata(state.getMetadataMap())
			.build();
		chatMetadataRepository.save(metadata);
	}

	private List<ChatHistoryResponse> convertToHistoryResponse(List<ChatMessage> rawHistory) {
		// DB에서 최신순으로 가져온 후 시간순(과거->현재)으로 역순 정렬
		Collections.reverse(rawHistory);

		return rawHistory.stream()
			.flatMap(msg -> java.util.stream.Stream.of(
				ChatHistoryResponse.user(msg.getQuestion()),
				ChatHistoryResponse.assistant(msg.getAnswer())
			))
			.toList();
	}

	private Flux<ServerSentEvent<String>> injectInitialEvents(
		Flux<ServerSentEvent<String>> mainFlux,
		String chatId
	) {
		// 메타데이터 이벤트 (chatId 전송용)
		ServerSentEvent<String> metaEvent = createSseEvent("metadata", Map.of("chatId", chatId), null);

		Flux<ServerSentEvent<String>> prefixFlux = Flux.just(metaEvent);

		return prefixFlux.concatWith(mainFlux);
	}

	/**
	 * SSE 이벤트 생성 유틸 (JSON 문자열 직렬화 포함)
	 */
	private ServerSentEvent<String> createSseEvent(String type, Map<String, Object> data, String content) {
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
			log.error("SSE JSON 직렬화 오류", e);
			return ServerSentEvent.builder("").build();
		}
	}

	/**
	 * 스트림 내부 상태 관리용 내부 클래스
	 */
	@Getter
	private static class StreamState {
		private final String chatId;
		private final String question;
		private final StringBuilder answerBuilder = new StringBuilder();
		private Map<String, Object> metadataMap = new HashMap<>();

		// 추출된 주요 메타데이터
		private String decision = "";
		private String preset = "";
		private Integer totalTokens = 0;

		public StreamState(String chatId, String question) {
			this.chatId = chatId;
			this.question = question;
		}

		public void appendAnswer(String chunk) {
			this.answerBuilder.append(chunk);
		}

		public String getAnswer() {
			return this.answerBuilder.toString();
		}

		@SuppressWarnings("unchecked")
		public void updateMetadata(Map<String, Object> data) {
			if (data == null) {
				return;
			}
			this.metadataMap = data;

			// RAG Decision 추출
			if (data.get("rag") instanceof Map<?, ?> rag) {
				Object gateReason = rag.get("gate_reason");
				this.decision = gateReason != null ? gateReason.toString() : "";
			}

			// Token Usage 추출
			if (data.get("token_usage") instanceof Map<?, ?> usage) {
				Object presetObj = usage.get("preset");
				this.preset = presetObj != null ? presetObj.toString() : "";
				Object tokens = usage.get("total_tokens");
				if (tokens instanceof Number n) {
					this.totalTokens = n.intValue();
				} else if (tokens instanceof String s) {
					this.totalTokens = Integer.parseInt(s);
				}
			}
		}
	}
}
