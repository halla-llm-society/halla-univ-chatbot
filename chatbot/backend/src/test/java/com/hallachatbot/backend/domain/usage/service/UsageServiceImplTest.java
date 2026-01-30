package com.hallachatbot.backend.domain.usage.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.BDDMockito.times;
import static org.mockito.BDDMockito.verify;

import java.math.BigDecimal;
import java.time.YearMonth;
import java.util.Optional;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.hallachatbot.backend.domain.usage.entity.MonthlyLlmUsage;
import com.hallachatbot.backend.domain.usage.repository.MonthlyLlmUsageRepository;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

@ExtendWith(MockitoExtension.class)
class UsageServiceImplTest {

	@InjectMocks
	private UsageServiceImpl usageService;

	@Mock
	private MonthlyLlmUsageRepository usageRepository;

	private static final BigDecimal LIMIT_AMOUNT = new BigDecimal("100.0"); // 100달러 한도

	@BeforeEach
	void setUp() {
		// @Value 값을 Mock 객체에 주입
		ReflectionTestUtils.setField(usageService, "monthlyLlmUsageLimit", LIMIT_AMOUNT);
	}

	@Test
	@DisplayName("예산 한도 내라면 검증을 통과한다")
	void checkLlmUsage_Success() {
		// given
		String period = YearMonth.now().toString();
		MonthlyLlmUsage safeUsage = MonthlyLlmUsage.builder()
			.period(period)
			.totalUsage(new BigDecimal("50.0")) // 한도(100)보다 적음
			.build();

		given(usageRepository.findById(period)).willReturn(Optional.of(safeUsage));

		// when & then (예외가 발생하지 않아야 함)
		assertThatCode(() -> usageService.checkLlmUsage())
			.doesNotThrowAnyException();
	}

	@Test
	@DisplayName("예산 한도를 초과하면 예외를 발생시킨다")
	void checkLlmUsage_Fail_Exceed() {
		// given
		String period = YearMonth.now().toString();
		MonthlyLlmUsage exceededUsage = MonthlyLlmUsage.builder()
			.period(period)
			.totalUsage(new BigDecimal("100.1")) // 한도(100) 초과
			.build();

		given(usageRepository.findById(period)).willReturn(Optional.of(exceededUsage));

		// when & then
		assertThatThrownBy(() -> usageService.checkLlmUsage())
			.isInstanceOf(UsageException.class)
			.hasFieldOrPropertyWithValue("errorCode", UsageErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED);
	}

	@Test
	@DisplayName("이번 달 기록이 없으면(월초) 0원으로 간주하여 통과한다")
	void checkLlmUsage_NewMonth() {
		// given
		String period = YearMonth.now().toString();
		given(usageRepository.findById(period)).willReturn(Optional.empty()); // 데이터 없음

		// when & then
		assertThatCode(() -> usageService.checkLlmUsage())
			.doesNotThrowAnyException();
	}

	@Test
	@DisplayName("비용 추가 시 Repository save가 호출되어야 한다")
	void addLlmUsage() {
		// given
		String period = YearMonth.now().toString();
		BigDecimal newCost = new BigDecimal("0.5");

		// Mock: 기존에 10달러 썼던 기록이 있다고 가정
		MonthlyLlmUsage existingUsage = MonthlyLlmUsage.builder()
			.period(period)
			.totalUsage(new BigDecimal("10.0"))
			.build();

		given(usageRepository.findById(period)).willReturn(Optional.of(existingUsage));

		// when
		usageService.addLlmUsage(newCost);

		// then
		// 1. save 메서드가 호출되었는지 검증
		verify(usageRepository, times(1)).save(any(MonthlyLlmUsage.class));

		// 2. 값이 제대로 더해졌는지 검증 (10.0 + 0.5 = 10.5)
		assertThat(existingUsage.getTotalUsage()).isEqualTo(new BigDecimal("10.5"));
	}
}
