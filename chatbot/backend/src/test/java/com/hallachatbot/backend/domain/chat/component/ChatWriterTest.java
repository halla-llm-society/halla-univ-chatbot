package com.hallachatbot.backend.domain.chat.component;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;

import java.util.Map;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.entity.ChatMetadata;
import com.hallachatbot.backend.domain.chat.entity.ChatTokenUsage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;

@ExtendWith(MockitoExtension.class)
class ChatWriterTest {

	@InjectMocks
	private ChatWriter chatWriter;

	@Mock
	private ChatMessageRepository chatMessageRepository;
	@Mock
	private ChatTokenUsageRepository chatTokenUsageRepository;
	@Mock
	private ChatMetadataRepository chatMetadataRepository;

	@Test
	@DisplayName("Context의 내용을 분해하여 Message, Token, Metadata 엔티티로 저장한다")
	void saveChatData() {
		// given
		ChatStreamContext context = new ChatStreamContext("chat-1", "질문");
		context.appendAnswer("최종 답변");
		// Context 내부 필드를 강제 설정 (실제로는 Handler가 함)
		org.springframework.test.util.ReflectionTestUtils.setField(context, "totalTokens", 150);
		org.springframework.test.util.ReflectionTestUtils.setField(context, "preset", "gpt-4");
		context.updateMetadata(Map.of("key", "value"));

		// ID 반환 Mocking
		ChatMessage savedMsg = ChatMessage.builder()
			.chatId("chat-1")
			.question("질문")
			.answer("최종 답변")
			.build();

		// ReflectionTestUtils로 private id 필드에 값 설정
		ReflectionTestUtils.setField(savedMsg, "id", "msg-id-123");

		given(chatMessageRepository.save(any(ChatMessage.class))).willReturn(savedMsg);

		// when
		chatWriter.saveChatData(context);

		// then
		// 1. ChatMessage 검증
		ArgumentCaptor<ChatMessage> msgCaptor = ArgumentCaptor.forClass(ChatMessage.class);
		verify(chatMessageRepository).save(msgCaptor.capture());
		assertThat(msgCaptor.getValue().getAnswer()).isEqualTo("최종 답변");

		// 2. TokenUsage 검증 (MessageId가 연결되었는지 확인)
		ArgumentCaptor<ChatTokenUsage> tokenCaptor = ArgumentCaptor.forClass(ChatTokenUsage.class);
		verify(chatTokenUsageRepository).save(tokenCaptor.capture());
		assertThat(tokenCaptor.getValue().getMessageId()).isEqualTo("msg-id-123");
		assertThat(tokenCaptor.getValue().getTotalTokens()).isEqualTo(150);

		// 3. Metadata 검증
		ArgumentCaptor<ChatMetadata> metaCaptor = ArgumentCaptor.forClass(ChatMetadata.class);
		verify(chatMetadataRepository).save(metaCaptor.capture());
		assertThat(metaCaptor.getValue().getMessageId()).isEqualTo("msg-id-123");
	}

	@Test
	@DisplayName("답변 내용이 비어있으면 DB에 저장하지 않는다")
	void saveChatData_EmptyAnswer() {
		// given
		// 답변(Answer)을 append 하지 않은 빈 Context
		ChatStreamContext emptyContext = new ChatStreamContext("chat-1", "질문");

		// when
		chatWriter.saveChatData(emptyContext);

		// then
		// 저장소 메서드들이 전혀 호출되지 않았음을 검증 (never())
		verify(chatMessageRepository, never()).save(any());
		verify(chatTokenUsageRepository, never()).save(any());
		verify(chatMetadataRepository, never()).save(any());
	}
}
