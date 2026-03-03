package com.hallachatbot.backend.domain.usage.dao;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

import java.math.BigDecimal;
import java.time.Duration;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.data.redis.core.HashOperations;
import org.springframework.data.redis.core.StringRedisTemplate;

@ExtendWith(MockitoExtension.class)
class LlmUsageRedisDaoTest {

	@InjectMocks
	private LlmUsageRedisDao llmUsageRedisDao;

	@Mock
	private StringRedisTemplate redisTemplate;

	// redisTemplate.opsForHash()의 반환값을 대체할 가짜 객체 (메서드 체이닝 방어용)
	@Mock
	private HashOperations<String, Object, Object> hashOperations;

	private final String period = "2026-03";
	private final String expectedKey = "monthly_llm_cost:2026-03";

	@BeforeEach
	void setUp() {
		// DAO 내부에서 redisTemplate.opsForHash()가 호출되면 우리가 만든 mock 객체를 반환하도록 설정
		when(redisTemplate.opsForHash()).thenReturn(hashOperations);
	}

	@Test
	@DisplayName("사용량 조회: Redis에 데이터가 없으면 0을 반환한다 (if문 분기 커버리지)")
	void getUsage_NullValue_ReturnsZero() {
		// given: 아직 이번 달 누적 비용이 없어서 null이 반환되는 상황 가정
		when(hashOperations.get(expectedKey, "totalUsage")).thenReturn(null);

		// when
		BigDecimal result = llmUsageRedisDao.getUsage(period);

		// then
		assertEquals(BigDecimal.ZERO, result);
	}

	@Test
	@DisplayName("사용량 조회: Redis에 정수로 저장된 값이 있으면 디스케일링되어 반환된다")
	void getUsage_HasValue_ReturnsConvertedBigDecimal() {
		// given: Redis에 1.25 달러가 백만 배(SCALE_FACTOR) 곱해진 "1250000"으로 저장되어 있다고 가정
		when(hashOperations.get(expectedKey, "totalUsage")).thenReturn("1250000");

		// when
		BigDecimal result = llmUsageRedisDao.getUsage(period);

		// then: 1,000,000으로 나뉘고 소수점 6자리까지 표현된 1.250000 반환 검증
		assertEquals(new BigDecimal("1.250000"), result);
	}

	@Test
	@DisplayName("비용 누적: 달러가 마이크로 단위 정수로 변환되어 원자적 증가(increment)와 TTL 갱신이 수행된다")
	void incrementUsage_Success() {
		// given
		BigDecimal cost = new BigDecimal("1.50");
		long expectedMicroCents = 1500000L; // 예상되는 변환 값 (1.50 * 1,000,000)

		// when
		llmUsageRedisDao.incrementUsage(period, cost);

		// then
		// 1. 원자적 증가 연산이 정확한 값으로 호출되었는지 검증
		verify(hashOperations, times(1)).increment(expectedKey, "totalUsage", expectedMicroCents);

		// 2. 마지막 업데이트 시간이 기록되었는지 검증 (시간은 계속 변하므로 anyString() 사용)
		verify(hashOperations, times(1)).put(eq(expectedKey), eq("lastUpdated"), anyString());

		// 3. 만료 시간이 60일로 갱신되었는지 검증
		verify(redisTemplate, times(1)).expire(expectedKey, Duration.ofDays(60));
	}

	@Test
	@DisplayName("비용 덮어쓰기: 동기화 시 강제로 값을 덮어쓰고 TTL을 갱신한다")
	void setUsage_Success() {
		// given
		BigDecimal exactCost = new BigDecimal("5.75");
		String expectedMicroCentsStr = "5750000"; // put 연산은 String으로 들어감

		// when
		llmUsageRedisDao.setUsage(period, exactCost);

		// then
		// increment 대신 put 연산으로 덮어쓰기가 일어났는지 검증
		verify(hashOperations, times(1)).put(expectedKey, "totalUsage", expectedMicroCentsStr);
		verify(hashOperations, times(1)).put(eq(expectedKey), eq("lastUpdated"), anyString());
		verify(redisTemplate, times(1)).expire(expectedKey, Duration.ofDays(60));
	}
}
