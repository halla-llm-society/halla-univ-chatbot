package com.hallachatbot.backend.global.client;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.global.client.dto.AiChatRequest;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

/**
 * AI 서비스 연동 클라이언트
 *
 * <p>
 * Python의 httpx 로직을 WebClient로 이식<br>
 * SSE(또는 NDJSON) 스트림을 받아 처리함
 * </p>
 *
 * @author pwk0131
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AiServiceClient {

	private final WebClient.Builder webClientBuilder;

	@Value("${app.ai-service-url}")
	private String aiServiceUrl;

	/**
	 * AI 챗봇 스트리밍 요청
	 *
	 * @param request 사용자 요청 정보
	 * @param history 대화 히스토리
	 * @return AI 응답 스트림 (Flux)
	 */
	public Flux<AiServiceResponse> streamChat(ChatRequest request, List<ChatHistoryResponse> history) {
		String endpoint = aiServiceUrl + "/api/chat";

		AiChatRequest aiBody = AiChatRequest.builder()
			.userInput(request.getUserInput())
			.messageHistory(history)
			.language(request.getLanguage())
			.build();

		// 성능 측정용 변수 (로그)
		long startTime = System.nanoTime();
		AtomicBoolean firstTokenReceived = new AtomicBoolean(false);

		return webClientBuilder.build()
			.post()
			.uri(endpoint)
			.contentType(MediaType.APPLICATION_JSON)
			.bodyValue(aiBody)
			.retrieve()
			.bodyToFlux(AiServiceResponse.class)
			.timeout(Duration.ofSeconds(120))
			.doOnNext(response -> {
				// 첫 번째 토큰("delta") 수신 시 시간 로깅
				if ("delta".equals(response.getType()) && !firstTokenReceived.get() && response.getContent() != null) {
					firstTokenReceived.set(true);
					double durationSeconds = (System.nanoTime() - startTime) / 1_000_000_000.0;
					log.info("[AI 첫 응답 소요 시간]: {}초 | 첫 토큰: {}", String.format("%.4f", durationSeconds),
						response.getContent());
				}
			})
			.doOnComplete(() -> {
				// 전체 완료 시간 로깅
				double totalDuration = (System.nanoTime() - startTime) / 1_000_000_000.0;
				log.info("[AI 완료 총 소요 시간]: {}초", String.format("%.4f", totalDuration));
			})
			.doOnError(WebClientResponseException.class, e -> {
				log.error("AI Service HTTP Error: {} {}", e.getStatusCode(), e.getResponseBodyAsString());
			})
			.doOnError(e -> {
				if (!(e instanceof WebClientResponseException)) {
					log.error("스트리밍 중 예상치 못한 오류: ", e);
				}
			});
	}
}
