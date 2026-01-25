package com.hallachatbot.backend.chat.service;

import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.chat.client.AiServiceClient;
import com.hallachatbot.backend.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.chat.entity.ChatMessage;
import com.hallachatbot.backend.chat.entity.ChatMetadata;
import com.hallachatbot.backend.chat.entity.ChatTokenUsage;
import com.hallachatbot.backend.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.usage.service.UsageService;

import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

/**
 * 챗봇 서비스 로직
 *
 * <p>
 * Python의 stream_chat_response 로직을 이식<br>
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
	 * @param isTampered 쿠키 변조 여부
	 * @return SSE 스트림
	 */
	public Flux<ServerSentEvent<String>> startChat(ChatRequest request, String chatId, boolean isTampered) {
		// 1. 비용 한도 확인 (예외 발생 시 GlobalExceptionHandler 처리)
		usageService.checkLlmUsage();

		// 2. 대화 히스토리 조회
		List<ChatMessage> rawHistory = chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId);
		List<ChatHistoryResponse> history = convertToHistoryResponse(rawHistory);

		// 스트림 동안 상태(답변, 메타데이터 등)를 누적할 객체 생성
		StreamState state = new StreamState(chatId, request.getUserInput());

		// 3. AI 서비스 호출 및 스트리밍 변환
		Flux<ServerSentEvent<String>> eventFlux = aiServiceClient.streamChat(request, history)
			.map(aiResponse -> processAiResponse(aiResponse, state))
			.doOnComplete(() -> saveChatData(state)); // 스트림 완료 시 DB 저장

		// 4. 초기 이벤트 주입 (Metadata, Warning)
		return injectInitialEvents(eventFlux, chatId, isTampered);
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
			if (data != null) {
				data.put("chatId", state.getChatId());
			}
			return createSseEvent("metadata", data, null);
		} else if ("error".equals(type)) {
			return createSseEvent("error", response.getData(), response.getMessage());
		}

		return ServerSentEvent.<String>builder().comment("keep-alive").build();
	}

	/**
	 * 스트림 완료 후 누적된 데이터를 DB에 저장 (비동기)
	 */
	private void saveChatData(StreamState state) {
		if (state.getAnswerBuilder().isEmpty()) {
			return;
		}

		// 1. ChatMessage 저장
		ChatMessage chatMessage = ChatMessage.builder()
			.chatId(state.getChatId())
			.question(state.getQuestion())
			.answer(state.getAnswerBuilder().toString())
			.decision(state.getDecision())
			.build();

		// blocking IO를 별도 스레드에서 실행 (Reactor 권장)
		// 실제 운영 시에는 ReactiveMongoRepository를 쓰거나 subscribeOn 사용
		Flux.just(chatMessage)
			.publishOn(Schedulers.boundedElastic())
			.doOnNext(savedMsg -> {
				String messageId = savedMsg.getId(); // MongoDB _id
				chatMessageRepository.save(savedMsg);
				saveTokenAndMetadata(state, messageId);
			})
			.subscribe();
	}

	private void saveTokenAndMetadata(StreamState state, String messageId) {
		// 2. TokenUsage 저장
		ChatTokenUsage tokenUsage = ChatTokenUsage.builder()
			.messageId(messageId) // Python 코드에서 'chatId' 필드에 message_id 저장함
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
		// DB에서 최신순으로 가져온 후 역순 정렬
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
		String chatId,
		boolean isTampered
	) {
		// 메타데이터 이벤트 (chatId 전송용)
		ServerSentEvent<String> metaEvent = createSseEvent("metadata", Map.of("chatId", chatId), null);

		Flux<ServerSentEvent<String>> prefixFlux = Flux.just(metaEvent);

		// 쿠키 변조 경고 메시지
		if (isTampered) {
			String warningMsg = "유효하지 않은 쿠키가 감지되어 새로운 대화가 시작되었습니다. "
				+ "쿠키를 임의로 변경하면 이전 대화를 기억하지 못해 응답 품질이 떨어질 수 있습니다.\n\n";
			ServerSentEvent<String> warningEvent = createSseEvent("delta", null, warningMsg);
			prefixFlux = prefixFlux.concatWith(Flux.just(warningEvent));
		}

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

		@SuppressWarnings("unchecked")
		public void updateMetadata(Map<String, Object> data) {
			if (data == null) {
				return;
			}
			this.metadataMap = data;

			// RAG Decision 추출
			if (data.containsKey("rag")) {
				Map<String, Object> rag = (Map<String, Object>)data.get("rag");
				this.decision = (String)rag.getOrDefault("gate_reason", "");
			}

			// Token Usage 추출
			if (data.containsKey("token_usage")) {
				Map<String, Object> usage = (Map<String, Object>)data.get("token_usage");
				this.preset = (String)usage.getOrDefault("preset", "");
				// 숫자가 Integer 혹은 String으로 올 수 있으므로 안전하게 파싱 필요하나 여기선 단순 캐스팅
				Object tokens = usage.get("total_tokens");
				if (tokens instanceof Number) {
					this.totalTokens = ((Number)tokens).intValue();
				}
			}
		}
	}
}
