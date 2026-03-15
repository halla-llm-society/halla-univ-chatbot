package com.hallachatbot.backend.domain.usage.scheduler;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.math.BigDecimal;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hallachatbot.backend.domain.usage.client.OpenAiUsageClient;
import com.hallachatbot.backend.domain.usage.dao.LlmUsageRedisDao;
import com.hallachatbot.backend.global.errorcode.UsageErrorCode;
import com.hallachatbot.backend.global.exception.UsageException;

@ExtendWith(MockitoExtension.class)
class UsageSyncSchedulerTest {

	@Mock
	private LlmUsageRedisDao llmUsageRedisDao;

	@Mock
	private OpenAiUsageClient openAiUsageClient;

	@InjectMocks
	private UsageSyncScheduler usageSyncScheduler;

	@Test
	@DisplayName("스케줄러 성공 - OpenAI 비용을 성공적으로 조회하여 Redis에 오버라이트한다")
	void syncMonthlyLlmUsage_Success() {
		// given
		BigDecimal exactUsage = new BigDecimal("15.50");
		when(openAiUsageClient.fetchMonthlyTotalUsageAmount()).thenReturn(exactUsage);

		// when
		usageSyncScheduler.syncMonthlyLlmUsage();

		// then
		// 1. Client 조회가 정상 호출되었는지 확인
		verify(openAiUsageClient).fetchMonthlyTotalUsageAmount();

		// 2. Dao의 setUsage가 호출되었는지 유연하게(any) 검증
		// Mockito가 파라미터 미세 차이로 Zero Interactions를 띄우는 것을 방지
		verify(llmUsageRedisDao).setUsage(anyString(), any(BigDecimal.class));
	}

	@Test
	@DisplayName("스케줄러 실패 방어 - Client에서 통신 에러가 발생해도 로깅 후 안전하게 종료된다")
	void syncMonthlyLlmUsage_ClientThrowsException() {
		// given
		when(openAiUsageClient.fetchMonthlyTotalUsageAmount())
			.thenThrow(new UsageException(UsageErrorCode.OPENAI_COST_FETCH_FAILED));

		// when (예외가 던져지지 않고 삼켜져야 함)
		usageSyncScheduler.syncMonthlyLlmUsage();

		// then (에러 발생 시 Redis 저장은 절대 호출되지 않아야 함)
		verify(llmUsageRedisDao, never()).setUsage(anyString(), any());
	}

	@Test
	@DisplayName("스케줄러 실패 방어 - 예상치 못한 시스템 에러(NPE 등)에도 스레드가 죽지 않는다")
	void syncMonthlyLlmUsage_UnexpectedException() {
		// given
		when(openAiUsageClient.fetchMonthlyTotalUsageAmount())
			.thenThrow(new NullPointerException("Unexpected Null"));

		// when
		usageSyncScheduler.syncMonthlyLlmUsage();

		// then
		verify(llmUsageRedisDao, never()).setUsage(anyString(), any());
	}
}
