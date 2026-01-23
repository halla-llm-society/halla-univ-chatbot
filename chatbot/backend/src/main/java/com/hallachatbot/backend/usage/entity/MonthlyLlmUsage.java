package com.hallachatbot.backend.usage.entity;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.LocalDateTime;

import org.springframework.data.annotation.Id;
import org.springframework.data.redis.core.RedisHash;

import jakarta.validation.constraints.Pattern;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 월별 LLM 사용 비용 관리 엔티티
 *
 * <p>
 * 키 : {@code monthly_llm_cost:{YYYY-MM}}<br>
 * TTL: 60일
 * </p>
 *
 * @author dryflowery
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@RedisHash(value = "monthly_llm_usage", timeToLive = 60 * 60 * 24 * 60)
public class MonthlyLlmUsage implements Serializable {

	/**
	 * 월별 키 식별자 (Format: "YYYY-MM")
	 */
	@Id
	@Pattern(regexp = "^\\d{4}-\\d{2}$", message = "기간 형식은 YYYY-MM 이어야 합니다 (e.g., 2026-01)")
	private String period;

	private BigDecimal totalUsage;

	private LocalDateTime lastUpdated;

	@Builder
	public MonthlyLlmUsage(String period, BigDecimal totalUsage, LocalDateTime lastUpdated) {
		this.period = period;
		this.totalUsage = totalUsage;
		this.lastUpdated = lastUpdated;
	}

	/**
	 * 해당 월의 새로운 비용 객체를 생성
	 * @param period "YYYY-MM" 형태의 문자열
	 * @return 초기화된 {@link MonthlyLlmUsage} 객체
	 */
	public static MonthlyLlmUsage init(String period) {
		return MonthlyLlmUsage.builder()
			.period(period)
			.totalUsage(BigDecimal.ZERO)
			.lastUpdated(LocalDateTime.now())
			.build();
	}

	/**
	 * 비용 누적 및 상태 갱신
	 * @param cost 추가할 비용 (USD)
	 */
	public void addCost(BigDecimal cost) {
		if (this.totalUsage == null) {
			this.totalUsage = BigDecimal.ZERO;
		}

		this.totalUsage = this.totalUsage.add(cost);
		this.lastUpdated = LocalDateTime.now();
	}
}
