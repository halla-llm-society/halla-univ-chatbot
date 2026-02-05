package com.hallachatbot.backend.domain.chat.component;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

import java.util.Collections;
import java.util.List;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;

@ExtendWith(MockitoExtension.class)
class ChatReaderTest {

	@InjectMocks
	private ChatReader chatReader;

	@Mock
	private ChatMessageRepository chatMessageRepository;

	@Mock
	private ChatMapper chatMapper;

	@Test
	@DisplayName("채팅 내역 조회 시 Repository와 Mapper가 정상적으로 호출되어야 한다")
	void getChatHistory_Success() {
		// given
		String chatId = "test-chat-id";

		// 가짜 엔티티 리스트 생성
		ChatMessage message = ChatMessage.builder()
			.question("질문")
			.answer("답변")
			.chatId(chatId)
			.build();
		List<ChatMessage> rawHistory = List.of(message);

		// 가짜 응답 DTO 리스트 생성 (Record 사용)
		ChatHistoryResponse responseDto = ChatHistoryResponse.user("질문");
		List<ChatHistoryResponse> convertedHistory = List.of(responseDto);

		// Mocking: Repository가 호출되면 엔티티 리스트 반환
		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(rawHistory);

		// Mocking: Mapper가 호출되면 DTO 리스트 반환
		given(chatMapper.toHistoryResponse(rawHistory))
			.willReturn(convertedHistory);

		// when
		List<ChatHistoryResponse> result = chatReader.getChatHistory(chatId);

		// then
		assertThat(result).hasSize(1);
		assertThat(result.get(0).content()).isEqualTo("질문");

		// 검증: 순서대로 잘 호출했는지 확인
		verify(chatMessageRepository).findTop6ByChatIdOrderByCreatedDateDesc(chatId);
		verify(chatMapper).toHistoryResponse(rawHistory);
	}

	@Test
	@DisplayName("채팅 내역이 없으면 빈 리스트를 반환해야 한다")
	void getChatHistory_Empty() {
		// given
		String chatId = "empty-chat-id";

		given(chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId))
			.willReturn(Collections.emptyList());

		given(chatMapper.toHistoryResponse(Collections.emptyList()))
			.willReturn(Collections.emptyList());

		// when
		List<ChatHistoryResponse> result = chatReader.getChatHistory(chatId);

		// then
		assertThat(result).isEmpty();
	}
}
