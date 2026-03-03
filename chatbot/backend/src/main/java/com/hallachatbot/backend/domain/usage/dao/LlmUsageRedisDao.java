package com.hallachatbot.backend.domain.usage.dao;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.Duration;
import java.time.LocalDateTime;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Repository;

import lombok.RequiredArgsConstructor;

/**
 * <b>월별 LLM 사용량(비용) 데이터 제어 DAO</b>
 * * <ul>
 * <li><b>저장소:</b> Redis Hash</li>
 * <li><b>동시성 제어:</b> 원자적 증가 연산 적용</li>
 * <li><b>오차 방지:</b> 부동소수점 오차 방지를 위해 마이크로 단위(1,000,000) 정수형 스케일링 적용</li>
 * </ul>
 */
@Repository
@RequiredArgsConstructor
public class LlmUsageRedisDao {

	private final StringRedisTemplate redisTemplate;

	private static final BigDecimal SCALE_FACTOR = new BigDecimal("1000000");
	private static final String KEY_PREFIX = "monthly_llm_cost:";
	private static final long EXPIRE_DAYS = 60;

	/**
	 * <b>월별 누적 사용량 조회</b>
	 *
	 * <ul>
	 * <li>Redis에 저장된 정수형 스케일 데이터를 다시 일반 USD 기준의 {@link BigDecimal}로 복원하여 반환</li>
	 * </ul>
	 *
	 * @param period 대상 연월 (Format: YYYY-MM)
	 * @return 누적 사용액 (데이터 부재 시 {@code BigDecimal.ZERO} 반환)
	 */
	public BigDecimal getUsage(String period) {
		String key = KEY_PREFIX + period;
		Object value = redisTemplate.opsForHash().get(key, "totalUsage");

		if (value == null) {
			return BigDecimal.ZERO;
		}

		BigDecimal microCents = new BigDecimal(value.toString());
		return microCents.divide(SCALE_FACTOR, 6, RoundingMode.HALF_UP);
	}

	/**
	 * <b>사용량 누적 및 데이터 수명 연장</b>
	 *
	 * <ul>
	 * <li>동시성 이슈를 원천 차단하기 위해 Redis 내부 연산({@code HINCRBY}) 수행</li>
	 * <li>데이터 갱신 시 만료 시간을 초기화하여 영구 적재로 인한 메모리 누수 방지</li>
	 * </ul>
	 *
	 * @param period 대상 연월 (Format: YYYY-MM)
	 * @param cost 추가할 비용 (USD)
	 */
	public void incrementUsage(String period, BigDecimal cost) {
		String key = KEY_PREFIX + period;
		long microCentsToAdd = cost.multiply(SCALE_FACTOR).longValue();

		redisTemplate.opsForHash().increment(key, "totalUsage", microCentsToAdd);
		redisTemplate.opsForHash().put(key, "lastUpdated", LocalDateTime.now().toString());
		redisTemplate.expire(key, Duration.ofDays(EXPIRE_DAYS));
	}

	/**
	 * <b>사용량 강제 동기화</b>
	 *
	 * <ul>
	 * <li>외부 API에서 가져온 정확한 과금 데이터로 내부 추정치를 덮어쓰기 위해 사용</li>
	 * </ul>
	 *
	 * @param period 대상 연월 (Format: YYYY-MM)
	 * @param exactCost 동기화할 정확한 누적 비용 (USD)
	 */
	public void setUsage(String period, BigDecimal exactCost) {
		String key = KEY_PREFIX + period;
		long exactMicroCents = exactCost.multiply(SCALE_FACTOR).longValue();

		redisTemplate.opsForHash().put(key, "totalUsage", String.valueOf(exactMicroCents));
		redisTemplate.opsForHash().put(key, "lastUpdated", LocalDateTime.now().toString());
		redisTemplate.expire(key, Duration.ofDays(EXPIRE_DAYS));
	}
}
