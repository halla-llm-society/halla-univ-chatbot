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
import org.springframework.web.reactive.function.client.WebClientResponseException;

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

	@Test
	@DisplayName("AI 서비스가 4xx/5xx 에러를 반환하면 WebClientResponseException이 전파된다")
	void streamChat_HttpError() {
		// given: AI 서버가 400 Bad Request를 반환하도록 설정
		mockWebServer.enqueue(new MockResponse()
			.setResponseCode(400)
			.setHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
			.setBody("{\"error\": \"Bad Request\"}"));

		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "질문");

		// when
		Flux<AiServiceResponse> responseFlux = aiServiceClient.streamChat(request, Collections.emptyList());

		// then: 에러가 발생해야 하며, doOnError(WebClientResponseException) 로직이 타게 됨
		StepVerifier.create(responseFlux)
			.expectError(WebClientResponseException.class)
			.verify();
	}

	@Test
	@DisplayName("AI 응답이 올바른 JSON 형식이 아니면 파싱 에러가 발생한다")
	void streamChat_ParsingError() {
		// given: 유효하지 않은 JSON 본문 반환
		mockWebServer.enqueue(new MockResponse()
			.setResponseCode(200)
			.setHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
			.setBody("{invalid-json-body...}"));

		ChatRequest request = new ChatRequest();
		ReflectionTestUtils.setField(request, "userInput", "질문");

		// when
		Flux<AiServiceResponse> responseFlux = aiServiceClient.streamChat(request, Collections.emptyList());

		// then: JSON 디코딩 실패로 에러 발생 (doOnError의 '그 외 에러' 로직 커버)
		StepVerifier.create(responseFlux)
			.expectError()
			.verify();
	}
}
