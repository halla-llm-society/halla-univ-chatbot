package com.hallachatbot.backend.global.client.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.io.IOException;
import java.util.Collections;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.reactive.function.client.WebClient;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.global.client.dto.AiServiceResponse;

import okhttp3.mockwebserver.MockResponse;
import okhttp3.mockwebserver.MockWebServer;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

class AiServiceClientTest {

	private AiServiceClient aiServiceClient;
	private MockWebServer mockWebServer;
	private ObjectMapper objectMapper;

	@BeforeEach
	void setUp() throws IOException {
		mockWebServer = new MockWebServer();
		mockWebServer.start();

		WebClient.Builder webClientBuilder = WebClient.builder();

		aiServiceClient = new AiServiceClientImpl(webClientBuilder);

		objectMapper = new ObjectMapper();

		// 테스트용 Mock Server URL 주입
		ReflectionTestUtils.setField(aiServiceClient, "aiServiceUrl", mockWebServer.url("/").toString());
	}

	@AfterEach
	void tearDown() throws IOException {
		mockWebServer.shutdown();
	}

	@Test
	@DisplayName("AI 서비스가 정상적으로 스트리밍 응답을 반환한다")
	void streamChat_Success() throws Exception {
		// given
		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "질문");
		ReflectionTestUtils.setField(request, "language", ChatRequest.Language.KOR);

		// Mock Server 응답 설정 (NDJSON 형태 시뮬레이션)
		String responseBody = """
			{"type": "delta", "content": "안녕"}
			{"type": "delta", "content": "하세요"}
			{"type": "metadata", "data": {"token_usage": {"total_tokens": 10}}}
			""";

		mockWebServer.enqueue(new MockResponse()
			.setResponseCode(200)
			.setHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
			.setBody(responseBody));

		// when
		Flux<AiServiceResponse> responseFlux = aiServiceClient.streamChat(request, Collections.emptyList());

		// then
		StepVerifier.create(responseFlux)
			.assertNext(res -> {
				assertThat(res.getType()).isEqualTo("delta");
				assertThat(res.getContent()).isEqualTo("안녕");
			})
			.assertNext(res -> {
				assertThat(res.getType()).isEqualTo("delta");
				assertThat(res.getContent()).isEqualTo("하세요");
			})
			.assertNext(res -> {
				assertThat(res.getType()).isEqualTo("metadata");
				assertThat(res.getData()).containsEntry("token_usage", java.util.Map.of("total_tokens", 10));
			})
			.verifyComplete();
	}
}
