package com.hallachatbot.backend.domain.chat.client.service;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;

import com.hallachatbot.backend.domain.chat.client.dto.AiChatRequest;
import com.hallachatbot.backend.domain.chat.client.dto.AiServiceResponse;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;

/**
 * <b>AI 서비스 연동 클라이언트 구현체</b>
 *
 * <p>
 * Spring WebClient를 활용하여 외부 AI API와 비동기 통신을 수행.
 * </p>
 *
 * <ul>
 * <li><b>타임아웃:</b> 120초 (응답 지연 시 연결 종료)</li>
 * <li><b>모니터링:</b> 첫 토큰 수신 시간(TTFT) 및 전체 응답 시간 로깅</li>
 * <li><b>에러 처리:</b> HTTP 상태 코드에 따른 예외 로깅</li>
 * </ul>
 *
 * @author pwk0131
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AiServiceClientImpl implements AiServiceClient {

	private final WebClient.Builder webClientBuilder;

	@Value("${app.ai-service-url}")
	private String aiServiceUrl;

	/**
	 * {@inheritDoc}
	 *
	 * <p>
	 * <b>동작 과정:</b><br>
	 * 1. 요청 DTO 생성 및 엔드포인트 설정<br>
	 * 2. POST 요청 전송 (Content-Type: application/json)<br>
	 * 3. 응답 본문을 {@link AiServiceResponse} 스트림으로 변환<br>
	 * 4. 첫 번째 데이터(Delta) 수신 시점과 완료 시점의 소요 시간을 계산하여 로깅
	 * </p>
	 */
	public Flux<AiServiceResponse> streamChat(String chatId, ChatRequest request, List<ChatHistoryResponse> history) {
		String endpoint = aiServiceUrl + "/api/chat";

		AiChatRequest aiBody = new AiChatRequest(
			request.userInput(),
			history,
			request.language()
		);

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
				if ("delta".equals(response.type()) && !firstTokenReceived.get() && response.content() != null) {
					firstTokenReceived.set(true);
					double durationSeconds = (System.nanoTime() - startTime) / 1_000_000_000.0;
					log.info("[AI] 스트리밍 첫 응답 수신 성공 (ChatId: {}, Duration: {}초)",
						chatId, String.format("%.4f", durationSeconds));
				}
			})
			.doOnComplete(() -> {
				// 전체 완료 시간 로깅
				double totalDuration = (System.nanoTime() - startTime) / 1_000_000_000.0;
				log.info("[AI] 스트리밍 응답 완료 (ChatId: {}, TotalDuration: {}초, HistorySize: {})",
					chatId, String.format("%.4f", totalDuration), history.size());
			})
			.doOnError(WebClientResponseException.class, e -> {
				log.error("[AI] HTTP 통신 에러 발생 (ChatId: {}, Status: {}, ResponseBody: {})",
					chatId, e.getStatusCode(), e.getResponseBodyAsString());
			})
			.doOnError(e -> {
				if (!(e instanceof WebClientResponseException)) {
					log.error("[AI] 스트리밍 중 예상치 못한 오류 발생 (ChatId: {}, Message: {})",
						chatId, e.getMessage(), e);
				}
			});
	}
}
