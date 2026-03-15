package com.hallachatbot.backend.domain.usage.service;

import java.math.BigDecimal;

import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

/**
 * <b>월 단위 서비스 가용량 및 예산 관리 서비스</b>
 *
 * <ul>
 * <li><b>예산 제어:</b> 설정된 월별 임계치를 기준으로 인프라 비용 폭주 방지</li>
 * <li><b>자동 갱신:</b> 매달 1일 00:00 시점에 별도 처리 없이 집계 단위 자동 전환</li>
 * </ul>
 */
public interface UsageService {

	/**
	 * <b>당월 LLM 사용량 임계치 초과 여부 검증</b>
	 *
	 * <ul>
	 * <li>LLM API 요청 직전 호출하여 현재 누적 사용액과 한도({@code app.monthly-llm-usage-limit}) 비교</li>
	 * <li><b>판단 기준:</b> 누적 사용액 >= 설정 한도</li>
	 * </ul>
	 *
	 * @throws UsageException 한도 초과 상태에서 호출될 경우 발생 ({@link UsageErrorCode#MONTHLY_LLM_BUDGET_EXCEEDED})
	 */
	void checkMonthlyLlmUsage();

	/**
	 * <b>LLM API 사용 비용 누적 기록</b>
	 *
	 * <ul>
	 * <li>발생한 API 호출 비용을 당월 누적 합계에 가산</li>
	 * <li>동시성 이슈를 방지하기 위해 원자적 연산으로 수행</li>
	 * </ul>
	 *
	 * @param cost 발생한 사용 비용 (USD 단위)
	 */
	void addMonthlyLlmUsage(@NotNull @PositiveOrZero BigDecimal cost);
}
