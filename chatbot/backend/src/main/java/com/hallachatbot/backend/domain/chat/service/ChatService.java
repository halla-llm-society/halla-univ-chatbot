package com.hallachatbot.backend.domain.chat.service;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.http.MediaType;
import org.springframework.http.codec.ServerSentEvent;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.domain.chat.dto.AiRequest;
import com.hallachatbot.backend.domain.chat.dto.ChatRequest;
import com.hallachatbot.backend.domain.chat.entity.Chat;
import com.hallachatbot.backend.domain.chat.entity.Token;
import com.hallachatbot.backend.domain.chat.repository.ChatRepository;
import com.hallachatbot.backend.domain.chat.repository.TokenRepository;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

@Slf4j
@Service
@RequiredArgsConstructor
public class ChatService {

	private final ChatRepository chatRepository;
	private final TokenRepository tokenRepository;
	private final WebClient.Builder webClientBuilder;
	private final ObjectMapper objectMapper;

	@Value("${ai.service.url:http://localhost:8000}") // 기본값 설정, 실제론 application.yml에서 주입
	private String aiServiceUrl;

	public Flux<ServerSentEvent<String>> streamChat(String chatId, ChatRequest request, boolean isTampered) {

		// 1. 히스토리 조회 (최근 6개)
		return chatRepository.findByChatIdOrderByDateDesc(chatId, PageRequest.of(0, 6))
			.collectList()
			.flatMapMany(historyList -> {
				// 최신순 -> 오래된순으로 다시 뒤집어서 AI에게 문맥 제공
				Collections.reverse(historyList);

				List<Map<String, String>> formattedHistory = new ArrayList<>();
				for (Chat chat : historyList) {
					if (chat.getQuestion() != null) {
						formattedHistory.add(Map.of("role", "user", "content", chat.getQuestion()));
					}
					if (chat.getAnswer() != null) {
						formattedHistory.add(Map.of("role", "assistant", "content", chat.getAnswer()));
					}
				}

				// 2. AI 서버 요청 데이터 생성
				AiRequest aiBody = AiRequest.builder()
					.userInput(request.getUserInput())
					.messageHistory(formattedHistory)
					.language(request.getLanguage())
					.build();

				// 답변 및 메타데이터 누적을 위한 Atomic 객체 (Lambda 내부에서 사용)
				AtomicReference<StringBuilder> fullAnswer = new AtomicReference<>(new StringBuilder());
				AtomicReference<String> decision = new AtomicReference<>("");
				AtomicReference<String> preset = new AtomicReference<>("");
				AtomicReference<String> totalTokens = new AtomicReference<>("");
				AtomicReference<String> totalCostUsd = new AtomicReference<>("");

				// 3. AI 서비스 호출 (WebClient)
				Flux<ServerSentEvent<String>> aiStream = webClientBuilder.build()
					.post()
					.uri(aiServiceUrl + "/api/chat")
					.contentType(MediaType.APPLICATION_JSON)
					.bodyValue(aiBody)
					.retrieve()
					.bodyToFlux(String.class) // JSON String 라인 단위 수신
					.flatMap(line -> parseAndMapToSSE(line, fullAnswer, decision, preset, totalTokens, totalCostUsd))
					.onErrorResume(e -> {
						log.error("AI Service Error", e);
						return Flux.just(ServerSentEvent.<String>builder()
							.event("error")
							.data("{\"message\": \"AI 서비스 연결 중 오류가 발생했습니다.\"}")
							.build());
					});

				// 4. 쿠키 변조 경고 메시지 처리 (필요시)
				Flux<ServerSentEvent<String>> warningStream = Flux.empty();
				if (isTampered) {
					String warningMsg = "⚠️ [시스템 알림] 유효하지 않은 쿠키가 감지되어 새로운 대화가 시작되었습니다.";
					Map<String, String> warningData = Map.of("content", warningMsg);
					try {
						warningStream = Flux.just(ServerSentEvent.<String>builder()
							.event("delta")
							.data(objectMapper.writeValueAsString(warningData))
							.build());
					} catch (JsonProcessingException e) {
						log.error("Warning msg json error", e);
					}
				}

				// 5. 스트림 합치기 및 완료 후 DB 저장
				return Flux.concat(warningStream, aiStream)
					.doOnComplete(() -> {
						// 스트림이 정상 종료되면 DB에 저장 (비동기 Fire-and-Forget)
						String answerText = fullAnswer.get().toString();
						if (!answerText.isEmpty()) {
							saveChatLog(chatId, request.getUserInput(), answerText, decision.get(), preset.get(),
								totalTokens.get(), totalCostUsd.get());
						}
					});
			});
	}

	// JSON 라인 파싱 및 SSE 변환 로직
	private Flux<ServerSentEvent<String>> parseAndMapToSSE(
		String line,
		AtomicReference<StringBuilder> fullAnswer,
		AtomicReference<String> decision,
		AtomicReference<String> preset,
		AtomicReference<String> totalTokens,
		AtomicReference<String> totalCostUsd
	) {
		if (line == null || line.isBlank()) {
			return Flux.empty();
		}

		try {
			Map<String, Object> payload = objectMapper.readValue(line, Map.class);
			String type = (String)payload.get("type");

			if ("delta".equals(type)) {
				String content = (String)payload.get("content");
				if (content != null) {
					fullAnswer.get().append(content);
				}
				return Flux.just(ServerSentEvent.<String>builder()
					.event("delta")
					.data(line.trim()) // 원본 JSON 그대로 전달
					.build());

			} else if ("metadata".equals(type)) {
				// 메타데이터 추출
				Map<String, Object> data = (Map<String, Object>)payload.get("data");
				if (data != null) {
					Map<String, Object> rag = (Map<String, Object>)data.get("rag");
					if (rag != null) {
						decision.set((String)rag.get("gate_reason"));
					}
					Map<String, Object> tokenUsage = (Map<String, Object>)data.get("token_usage");
					if (tokenUsage != null) {
						totalTokens.set(String.valueOf(tokenUsage.get("total_tokens")));
						preset.set((String)tokenUsage.get("preset"));
						totalCostUsd.set(String.valueOf(tokenUsage.get("total_cost_usd")));
					}
				}
				return Flux.just(ServerSentEvent.<String>builder()
					.event("metadata")
					.data(line.trim())
					.build());
			} else if ("error".equals(type)) {
				return Flux.just(ServerSentEvent.<String>builder()
					.event("error")
					.data(line.trim())
					.build());
			}
		} catch (Exception e) {
			log.error("JSON Parsing Error: {}", line, e);
		}
		return Flux.empty();
	}

	// DB 저장 로직 (비동기)
	private void saveChatLog(String chatId, String question, String answer, String decision, String preset,
		String totalTokens, String totalCostUsd) {
		Chat chat = Chat.builder()
			.chatId(chatId)
			.question(question)
			.answer(answer)
			.decision(decision)
			.date(LocalDateTime.now())
			.build();

		chatRepository.save(chat)
			.flatMap(savedChat -> {
				// Chat 저장 후 Token 정보 저장
				Token token = Token.builder()
					.relatedChatId(savedChat.getId()) // Chat Document의 ID 참조
					.preset(preset)
					.totalTokens(totalTokens)
					.totalCostUsd(totalCostUsd)
					.date(LocalDateTime.now())
					.build();
				return tokenRepository.save(token);
			})
			.subscribe(
				success -> log.info("Chat & Token saved successfully for chat: {}", chatId),
				error -> log.error("Failed to save chat log", error)
			);
	}
}
