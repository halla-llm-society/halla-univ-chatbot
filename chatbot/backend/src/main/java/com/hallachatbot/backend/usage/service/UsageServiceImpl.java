package com.hallachatbot.backend.usage.service;

import java.math.BigDecimal;
import java.time.YearMonth;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.validation.annotation.Validated;

import com.hallachatbot.backend.global.errorcode.CostErrorCode;
import com.hallachatbot.backend.global.exception.CostException;
import com.hallachatbot.backend.usage.entity.MonthlyLlmUsage;
import com.hallachatbot.backend.usage.repository.MonthlyLlmUsageRepository;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@Validated
@RequiredArgsConstructor
public class UsageServiceImpl implements UsageService {

	private final MonthlyLlmUsageRepository monthlyLlmUsageRepository;

	@Value("${app.monthly-llm-usage-limit}")
	private BigDecimal monthlyLlmUsageLimit;

	@Override
	public void checkLlmUsage() {
		MonthlyLlmUsage usage = getMonthlyLlmUsage();

		if (usage.getTotalUsage().compareTo(monthlyLlmUsageLimit) >= 0) {
			throw new CostException(CostErrorCode.MONTHLY_LLM_BUDGET_EXCEEDED);
		}
	}

	@Override
	@Async
	public void addLlmUsage(@NotNull @PositiveOrZero BigDecimal cost) {
		try {
			MonthlyLlmUsage usage = getMonthlyLlmUsage();
			usage.addCost(cost);

			monthlyLlmUsageRepository.save(usage);
		} catch (Exception e) {
			log.error("LLM 비용 저장 실패 (Cost: {})", cost, e);
		}
	}

	private MonthlyLlmUsage getMonthlyLlmUsage() {
		String currentPeriod = YearMonth.now().toString();

		return monthlyLlmUsageRepository.findById(currentPeriod)
			.orElseGet(() -> MonthlyLlmUsage.init(currentPeriod));
	}
}
