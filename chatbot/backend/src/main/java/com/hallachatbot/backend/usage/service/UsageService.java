package com.hallachatbot.backend.usage.service;

import java.math.BigDecimal;

import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;
import com.hallachatbot.backend.usage.entity.MonthlyLlmUsage;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;

/**
 * <b>월 단위 서비스 가용량 및 예산 관리 서비스</b>
 *
 * <p>주요 설계 원칙:</p>
 * <ul>
 * <li><b>자동 초기화:</b> 시스템 시각 기준, 매달 1일 00:00 시점에 별도 배치 없이 예산 집계 단위를 자동 전환</li>
 * <li><b>회로 차단:</b> 설정된 임계치 도달 시 즉시 예외를 송출하여 인프라 비용 폭주 방지</li>
 * </ul>
 *
 * @author dryflowery
 */
// todo: 기타 인프라 비용 체크
// todo: 스케줄러로 하루 한 번 OpenAPI 서버에서 정확한 값 가져오기
public interface UsageService {

	/**
	 * <b>현재 월의 LLM 사용량 임계치 초과 여부 검증</b>
	 *
	 * <p>
	 * LLM API 요청 수행 직전 호출하여, 현시점 누적 사용액과 {@code app.monthly-llm-usage-limit} 설정값을 비교
	 * </p>
	 *
	 * <ul>
	 * <li><b>검증 대상:</b> {@link MonthlyLlmUsage#getTotalUsage()}</li>
	 * <li><b>판단 기준:</b> 누적 사용액 >= 설정 한도</li>
	 * <li><b>발생 에러:</b> {@link UsageErrorCode#MONTHLY_LLM_BUDGET_EXCEEDED} (HTTP 403)</li>
	 * </ul>
	 *
	 * @throws UsageException 한도 초과 상태에서 호출될 경우 발생
	 */
	void checkLlmUsage();

	/**
	 * <b>LLM API 사용 비용 누적 기록</b>
	 *
	 * @param cost 발생한 사용 비용 (USD 단위)
	 */
	void addLlmUsage(@NotNull @PositiveOrZero BigDecimal cost);
}
