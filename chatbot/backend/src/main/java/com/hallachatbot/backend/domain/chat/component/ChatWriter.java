package com.hallachatbot.backend.domain.chat.component;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.entity.ChatMetadata;
import com.hallachatbot.backend.domain.chat.entity.ChatTokenUsage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Component
@RequiredArgsConstructor
public class ChatWriter {

	private final ChatMessageRepository chatMessageRepository;
	private final ChatTokenUsageRepository chatTokenUsageRepository;
	private final ChatMetadataRepository chatMetadataRepository;

	@Transactional
	public void saveChatData(ChatStreamContext context) {
		// 빈 응답 체크 로직 등은 여기서 수행
		if (context.getAnswerBuilder().isEmpty()) {
			return;
		}

		try {
			// 1. ChatMessage 저장
			ChatMessage chatMessage = ChatMessage.builder()
				.chatId(context.getChatId())
				.question(context.getQuestion())
				.answer(context.getAnswer())
				.decision(context.getDecision())
				.build();

			ChatMessage savedMsg = chatMessageRepository.save(chatMessage);
			String messageId = savedMsg.getId();

			// 2. TokenUsage 저장
			ChatTokenUsage tokenUsage = ChatTokenUsage.builder()
				.messageId(messageId)
				.preset(context.getPreset())
				.totalTokens(context.getTotalTokens())
				.build();
			chatTokenUsageRepository.save(tokenUsage);

			// 3. Metadata 저장
			ChatMetadata metadata = ChatMetadata.builder()
				.messageId(messageId)
				.metadata(context.getMetadataMap())
				.build();
			chatMetadataRepository.save(metadata);

		} catch (Exception e) {
			log.error("채팅 데이터 저장 실패: chatId={}", context.getChatId(), e);
		}
	}
}
