package com.hallachatbot.backend.domain.usage.service;

import java.math.BigDecimal;
import java.time.YearMonth;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import com.hallachatbot.backend.domain.usage.dao.LlmUsageRedisDao;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * <b>월 단위 서비스 예산 및 가용량 관리 서비스</b>
 *
 * <ul>
 * <li><b>예산 통제:</b> 설정된 월별 임계치 도달 시 서비스 차단</li>
 * <li><b>비용 누적:</b> 비용 기록 수행</li>
 * </ul>
 */
@Slf4j
@Service
@Validated
@RequiredArgsConstructor
public class UsageServiceImpl implements UsageService {

	private final LlmUsageRedisDao llmUsageRedisDao;

	@Value("${app.monthly-llm-usage-limit}")
	private BigDecimal monthlyLlmUsageLimit;

	/**
	 * <b>당월 LLM 사용 한도 초과 여부 검증</b>
	 *
	 * <ul>
	 * <li>AI 요청 수행 전 호출되어 현재 누적 비용과 임계치({@code app.monthly-llm-usage-limit})를 대조</li>
	 * </ul>
	 *
	 * @throws UsageException 누적 사용액이 설정된 한도 이상일 경우 발생
	 */
	@Override
	public void checkMonthlyLlmUsage() {
		String currentPeriod = YearMonth.now().toString();
		BigDecimal currentUsage = llmUsageRedisDao.getUsage(currentPeriod);

		if (currentUsage.compareTo(monthlyLlmUsageLimit) >= 0) {
			throw new UsageException(UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED);
		}
	}

	/**
	 * <b>LLM API 호출 비용 누적 처리</b>
	 *
	 * <ul>
	 * <li>메인 스레드의 응답 지연 방지를 위해 {@link Async} 환경에서 동작</li>
	 * </ul>
	 *
	 * @param cost 1회 요청 시 발생한 산출 비용 (USD)
	 */
	@Override
	@Async
	public void addMonthlyLlmUsage(@NotNull @PositiveOrZero BigDecimal cost) {
		try {
			String currentPeriod = YearMonth.now().toString();
			llmUsageRedisDao.incrementUsage(currentPeriod, cost);

		} catch (Exception e) {
			log.error("LLM 비용 저장 실패 (Cost: {})", cost, e);
		}
	}
}
