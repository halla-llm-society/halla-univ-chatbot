package com.hallachatbot.backend.domain.usage.client;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Instant;
import java.time.YearMonth;
import java.time.ZoneId;
import java.time.ZonedDateTime;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Component;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import com.fasterxml.jackson.databind.JsonNode;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

import lombok.extern.slf4j.Slf4j;

/**
 * <b>OpenAI 공식 비용 추적 API 클라이언트</b>
 *
 * <p>
 * OpenAI 관리자 권한을 이용하여 조직단위의 과금 데이터를 조회.
 * </p>
 *
 * @see <a href="https://developers.openai.com/api/reference/resources/organization/subresources/audit_logs/methods/get_costs">OpenAI API Reference - Costs</a>
 */
@Slf4j
@Component
public class OpenAiUsageClient {

	private final String openAiAdminKey;
	private final String costsApiUrl;
	private final RestTemplate restTemplate;

	public OpenAiUsageClient(
		RestTemplateBuilder restTemplateBuilder,
		@Value("${app.openai-admin-key}") String openAiAdminKey,
		@Value("${app.costs-api-url}") String costsApiUrl) {
		this.restTemplate = restTemplateBuilder.build();
		this.openAiAdminKey = openAiAdminKey;
		this.costsApiUrl = costsApiUrl;
	}

	/**
	 * <b>이번 달 누적 사용 비용 조회</b>
	 *
	 * @return 당월 총 과금액 (USD)
	 * @throws UsageException OpenAI API 상태 코드에 따른 커스텀 예외
	 */
	public BigDecimal fetchMonthlyTotalUsageAmount() {
		try {
			// 날짜 계산 (KST 기준 당월 1일 ~ 현재)
			long[] timeRange = calculateMonthlyTimeRange();

			// URL 및 인증 헤더 조립
			String requestUrl = buildRequestUrl(timeRange[0], timeRange[1]);
			HttpEntity<Void> requestEntity = createAuthHeader();

			// API 호출
			ResponseEntity<JsonNode> response = restTemplate.exchange(
				requestUrl,
				HttpMethod.GET,
				requestEntity,
				JsonNode.class
			);

			// 데이터 파싱 및 합산
			BigDecimal totalCost = parseTotalCost(response.getBody());

			log.info("[OpenAiClient] 당월 누적 비용 조회 (StartTime: {}, EndTime: {}) - 완료 (Total: ${})",
				timeRange[0], timeRange[1], totalCost);

			return totalCost;

		} catch (HttpClientErrorException e) {
			log.warn("[OpenAiClient] API 요청 실패 (Status: {}, ErrorBody: {})",
				e.getStatusCode(), e.getResponseBodyAsString());
			throw new UsageException(UsageErrorCode.OPENAI_COST_FETCH_FAILED);

		} catch (Exception e) {
			log.error("[OpenAiClient] 서버 통신 장애 (Message: {})", e.getMessage());
			throw new UsageException(UsageErrorCode.OPENAI_COST_FETCH_FAILED);
		}
	}

	/**
	 * 한국 시간 기준 당월 1일 00시부터 현재까지의 Unix Timestamp 계산
	 */
	private long[] calculateMonthlyTimeRange() {
		ZoneId seoulZone = ZoneId.of("Asia/Seoul");
		ZonedDateTime startOfMonth = YearMonth.now(seoulZone).atDay(1).atStartOfDay(seoulZone);
		return new long[]{startOfMonth.toEpochSecond(), Instant.now().getEpochSecond()};
	}

	/**
	 * 조회 기간을 포함한 API 요청 URL 조립
	 */
	private String buildRequestUrl(long startTime, long endTime) {
		return UriComponentsBuilder.fromUriString(costsApiUrl)
			.queryParam("start_time", startTime)
			.queryParam("end_time", endTime)
			.queryParam("limit", 31)
			.toUriString();
	}

	/**
	 * Admin API Key가 포함된 HTTP 인증 헤더 생성
	 */
	private HttpEntity<Void> createAuthHeader() {
		HttpHeaders headers = new HttpHeaders();
		headers.setBearerAuth(openAiAdminKey);
		return new HttpEntity<>(headers);
	}

	/**
	 * 응답 JSON 노드를 순회하며 달러(USD) 기준 총 사용 금액 합산
	 */
	private BigDecimal parseTotalCost(JsonNode rootNode) {
		BigDecimal totalUsageUsd = BigDecimal.ZERO;

		if (rootNode == null || !rootNode.has("data")) {
			return totalUsageUsd;
		}

		for (JsonNode bucket : rootNode.path("data")) {
			for (JsonNode result : bucket.path("results")) {
				JsonNode valueNode = result.path("amount").path("value");
				if (!valueNode.isMissingNode()) {
					totalUsageUsd = totalUsageUsd.add(new BigDecimal(valueNode.asText()));
				}
			}
		}

		return totalUsageUsd.setScale(6, RoundingMode.HALF_UP);
	}
}
