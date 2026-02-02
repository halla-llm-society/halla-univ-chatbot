package com.hallachatbot.backend.domain.chat.component;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;

class ChatMapperTest {

	private final ChatMapper chatMapper = new ChatMapper();

	@Test
	@DisplayName("ChatMessage 리스트를 ChatHistoryResponse로 변환하며 역순으로 정렬한다")
	void toHistoryResponse() {
		// given
		// 최신순(내림차순)으로 DB에서 조회된 상황 가정
		ChatMessage msg1 = ChatMessage.builder().question("질문2").answer("답변2").build(); // 최신
		ChatMessage msg2 = ChatMessage.builder().question("질문1").answer("답변1").build(); // 과거

		List<ChatMessage> rawHistory = List.of(msg1, msg2);

		// when
		List<ChatHistoryResponse> responses = chatMapper.toHistoryResponse(rawHistory);

		// then
		// User/Assistant 쌍으로 쪼개지므로 총 4개의 응답이 나와야 함
		assertThat(responses).hasSize(4);

		// 순서는 과거(질문1) -> 현재(질문2) 순이어야 함
		assertThat(responses.get(0).getContent()).isEqualTo("질문1");
		assertThat(responses.get(1).getContent()).isEqualTo("답변1");
		assertThat(responses.get(2).getContent()).isEqualTo("질문2");
		assertThat(responses.get(3).getContent()).isEqualTo("답변2");
	}
}
