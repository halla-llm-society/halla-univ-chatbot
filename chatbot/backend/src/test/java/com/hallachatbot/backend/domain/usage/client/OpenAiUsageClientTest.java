package com.hallachatbot.backend.domain.usage.client;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;
import java.math.RoundingMode;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

@ExtendWith(MockitoExtension.class)
class OpenAiUsageClientTest {

	@Mock
	private RestTemplateBuilder restTemplateBuilder;

	@Mock
	private RestTemplate restTemplate;

	private OpenAiUsageClient openAiUsageClient;
	private final ObjectMapper objectMapper = new ObjectMapper();

	@BeforeEach
	void setUp() {
		when(restTemplateBuilder.build()).thenReturn(restTemplate);
		openAiUsageClient = new OpenAiUsageClient(
			restTemplateBuilder,
			"test-admin-key",
			"https://api.openai.com/v1/organization/costs"
		);
	}

	@Test
	@DisplayName("당월 비용 조회 성공 - 유효한 JSON 데이터가 주어지면 금액을 합산하여 반환한다")
	void fetchMonthlyTotalUsageAmount_Success() {
		// given
		ObjectNode rootNode = objectMapper.createObjectNode();
		ArrayNode dataArray = rootNode.putArray("data");

		ObjectNode bucket1 = dataArray.addObject();
		ArrayNode results1 = bucket1.putArray("results");
		results1.addObject().putObject("amount").put("value", 0.05);
		results1.addObject().putObject("amount").put("value", 0.01);

		ResponseEntity<JsonNode> responseEntity = new ResponseEntity<>(rootNode, HttpStatus.OK);
		when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(JsonNode.class)))
			.thenReturn(responseEntity);

		// when
		BigDecimal totalCost = openAiUsageClient.fetchMonthlyTotalUsageAmount();

		// then
		BigDecimal expected = new BigDecimal("0.06").setScale(6, RoundingMode.HALF_UP);
		assertThat(totalCost).isEqualTo(expected);
	}

	@Test
	@DisplayName("당월 비용 조회 성공 - 응답에 data 배열이 없으면 0.000000을 반환한다")
	void fetchMonthlyTotalUsageAmount_EmptyData() {
		// given
		ObjectNode emptyNode = objectMapper.createObjectNode();
		ResponseEntity<JsonNode> responseEntity = new ResponseEntity<>(emptyNode, HttpStatus.OK);

		when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(JsonNode.class)))
			.thenReturn(responseEntity);

		// when
		BigDecimal totalCost = openAiUsageClient.fetchMonthlyTotalUsageAmount();

		// then
		BigDecimal expected = new BigDecimal("0.000000");
		// isEqualByComparingTo는 0과 0.000000을 같다고 판단합니다.
		assertThat(totalCost).isEqualByComparingTo(expected);
	}

	@Test
	@DisplayName("당월 비용 조회 실패 - 401 인증 에러 발생 시 UsageException을 던진다")
	void fetchMonthlyTotalUsageAmount_Unauthorized() {
		// given
		when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(JsonNode.class)))
			.thenThrow(new HttpClientErrorException(HttpStatus.UNAUTHORIZED));

		// when & then (메시지 비교가 아닌 ErrorCode 일치 여부로 정확하게 검증)
		assertThatThrownBy(() -> openAiUsageClient.fetchMonthlyTotalUsageAmount())
			.isInstanceOf(UsageException.class)
			.extracting(e -> ((UsageException) e).getErrorCode())
			.isEqualTo(UsageErrorCode.OPENAI_COST_FETCH_FAILED);
	}

	@Test
	@DisplayName("당월 비용 조회 실패 - 500 서버 에러 등 통신 장애 시 UsageException을 던진다")
	void fetchMonthlyTotalUsageAmount_ServerError() {
		// given
		when(restTemplate.exchange(anyString(), eq(HttpMethod.GET), any(), eq(JsonNode.class)))
			.thenThrow(new HttpServerErrorException(HttpStatus.INTERNAL_SERVER_ERROR));

		// when & then
		assertThatThrownBy(() -> openAiUsageClient.fetchMonthlyTotalUsageAmount())
			.isInstanceOf(UsageException.class)
			.extracting(e -> ((UsageException) e).getErrorCode())
			.isEqualTo(UsageErrorCode.OPENAI_COST_FETCH_FAILED);
	}
}
