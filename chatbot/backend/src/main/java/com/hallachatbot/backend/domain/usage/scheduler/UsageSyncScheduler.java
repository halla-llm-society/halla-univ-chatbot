package com.hallachatbot.backend.domain.usage.scheduler;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.YearMonth;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.usage.client.OpenAiUsageClient;
import com.hallachatbot.backend.domain.usage.dao.LlmUsageRedisDao;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * <b>OpenAI 누적 사용량 자동 동기화 스케줄러</b>
 *
 * <p>
 * 서버 내부에서 자체적으로 계산한 LLM 사용 추정치와 실제 OpenAI 플랫폼의 청구 비용 간의 차를 보정하기 위해 매일 00시에 배치 작업을 수행.
 * </p>
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class UsageSyncScheduler {

	private final LlmUsageRedisDao llmUsageRedisDao;
	private final OpenAiUsageClient openAiUsageClient;

	/**
	 * 매일 자정 OpenAI 서버에서 당월 정확한 누적 비용을 조회하여 Redis 캐시 데이터를 갱신
	 */
	@Scheduled(cron = "0 0 0 * * *", zone = "Asia/Seoul")
	public void syncMonthlyLlmUsage() {
		LocalDate syncDate = LocalDate.now();

		try {
			// OpenAI 서버에서 누적 비용 조회
			BigDecimal exactUsage = openAiUsageClient.fetchMonthlyTotalUsageAmount();

			// 현재 연월 문자열 생성
			String currentPeriod = YearMonth.now().toString();

			// Redis에 저장된 기존 추정치를 정확한 값으로 갱신
			llmUsageRedisDao.setUsage(currentPeriod, exactUsage);

			log.info("[UsageSync] OpenAI LLM 비용 동기화 완료 (Date: {}, Period: {}, Exact Cost: ${})",
				syncDate, currentPeriod, exactUsage);

		} catch (Exception e) {
			log.error("[UsageSync] OpenAI LLM 비용 동기화 실패 (Date: {}) - {}",
				syncDate, e.getMessage(), e);
		}
	}
}
