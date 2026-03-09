package com.hallachatbot.backend.domain.chat.service;

import static org.assertj.core.api.Assertions.assertThat;

import java.math.BigDecimal;
import java.util.HashMap;
import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

class ChatStreamContextTest {

	@Test
	@DisplayName("total_cost_usd 키에 공백이 포함되어 있어도 비용이 정상적으로 추출되어야 한다.")
	void updateMetadata_ExtractCostWithTrailingSpace() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-123", "테스트 질문");

		Map<String, Object> tokenUsage = new HashMap<>();
		tokenUsage.put("total_cost_usd ", 0.0073355);
		tokenUsage.put("total_tokens", 100);

		Map<String, Object> metadata = new HashMap<>();
		metadata.put("token_usage", tokenUsage);

		// when
		context.updateMetadata(metadata);

		// then
		assertThat(context.getCost()).isEqualByComparingTo(new BigDecimal("0.0073355"));
		assertThat(context.getTotalTokens()).isEqualTo(100);
	}

	@Test
	@DisplayName("비용 정보가 없거나 변환할 수 없는 값일 경우 비용은 ZERO를 유지해야 한다.")
	void updateMetadata_CostIsZeroWhenNullOrInvalid() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-123", "테스트 질문");

		Map<String, Object> tokenUsage = new HashMap<>();
		tokenUsage.put("total_cost_usd", null);

		Map<String, Object> metadata = new HashMap<>();
		metadata.put("token_usage", tokenUsage);

		// when
		context.updateMetadata(metadata);

		// then
		assertThat(context.getCost()).isEqualByComparingTo(BigDecimal.ZERO);
	}
}
