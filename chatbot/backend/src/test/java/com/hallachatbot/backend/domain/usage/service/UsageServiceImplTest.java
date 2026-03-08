package com.hallachatbot.backend.domain.usage.service;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

import java.math.BigDecimal;
import java.time.YearMonth;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.hallachatbot.backend.domain.usage.dao.LlmUsageRedisDao;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

@ExtendWith(MockitoExtension.class)
class UsageServiceImplTest {

	@InjectMocks
	private UsageServiceImpl usageService;

	@Mock
	private LlmUsageRedisDao llmUsageRedisDao;

	private final BigDecimal limitAmount = new BigDecimal("100.00");
	private String currentPeriod;

	@BeforeEach
	void setUp() {
		// 테스트 실행 시점의 현재 연월 세팅
		currentPeriod = YearMonth.now().toString();

		// @Value로 주입받는 한도 값을 ReflectionTestUtils를 통해 강제 주입
		ReflectionTestUtils.setField(usageService, "monthlyLlmUsageLimit", limitAmount);
	}

	@Test
	@DisplayName("한도 체크: 현재 사용량이 한도 미만일 경우 예외가 발생하지 않는다")
	void checkMonthlyLlmUsage_UnderLimit_DoesNotThrow() {
		// given
		BigDecimal currentUsage = new BigDecimal("99.99");
		when(llmUsageRedisDao.getUsage(currentPeriod)).thenReturn(currentUsage);

		// when & then
		assertDoesNotThrow(() -> usageService.checkMonthlyLlmUsage());
	}

	@Test
	@DisplayName("한도 체크: 현재 사용량이 한도와 정확히 같을 경우 예외가 발생한다")
	void checkMonthlyLlmUsage_EqualToLimit_ThrowsException() {
		// given
		BigDecimal currentUsage = new BigDecimal("100.00");
		when(llmUsageRedisDao.getUsage(currentPeriod)).thenReturn(currentUsage);

		// when & then
		UsageException exception = assertThrows(UsageException.class, () -> usageService.checkMonthlyLlmUsage());
		assertEquals(UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED, exception.getErrorCode());
	}

	@Test
	@DisplayName("한도 체크: 현재 사용량이 한도를 초과했을 경우 예외가 발생한다")
	void checkMonthlyLlmUsage_OverLimit_ThrowsException() {
		// given
		BigDecimal currentUsage = new BigDecimal("100.01");
		when(llmUsageRedisDao.getUsage(currentPeriod)).thenReturn(currentUsage);

		// when & then
		UsageException exception = assertThrows(UsageException.class, () -> usageService.checkMonthlyLlmUsage());
		assertEquals(UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED, exception.getErrorCode());
	}

	@Test
	@DisplayName("비용 누적: 정상적으로 DAO의 increment 메서드를 호출한다")
	void addMonthlyLlmUsage_Success() {
		// given
		BigDecimal cost = new BigDecimal("1.50");

		// when
		usageService.addMonthlyLlmUsage(cost);

		// then
		// 현재 월을 기준으로 정확히 1번 호출되었는지 검증
		verify(llmUsageRedisDao, times(1)).incrementUsage(currentPeriod, cost);
	}

	@Test
	@DisplayName("비용 누적: DAO에서 예외가 발생해도 로직이 중단되지 않고 catch 블록을 타며 정상 종료된다")
	void addMonthlyLlmUsage_DaoThrowsException_CatchesGracefully() {
		// given
		BigDecimal cost = new BigDecimal("1.50");

		// 레디스 통신 장애 등 예외가 발생한 상황을 가정 (catch 블록 커버리지 확보용)
		doThrow(new RuntimeException("Redis Connection Error"))
			.when(llmUsageRedisDao).incrementUsage(currentPeriod, cost);

		// when & then
		// 메서드 밖으로 예외가 던져지지 않고 내부에서 로깅 후 안전하게 삼켜지는지(catch) 확인
		assertDoesNotThrow(() -> usageService.addMonthlyLlmUsage(cost));
		verify(llmUsageRedisDao, times(1)).incrementUsage(currentPeriod, cost);
	}
}
