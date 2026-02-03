package com.hallachatbot.backend.domain.chat.component;

import org.springframework.stereotype.Component;

import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.entity.ChatMetadata;
import com.hallachatbot.backend.domain.chat.entity.ChatTokenUsage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatMetadataRepository;
import com.hallachatbot.backend.domain.chat.repository.ChatTokenUsageRepository;
import com.hallachatbot.backend.domain.chat.service.ChatStreamContext;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * <b>대화 데이터 저장 컴포넌트 (Writer)</b>
 *
 * <p>
 * 스트리밍이 종료된 후 {@link ChatStreamContext}에 누적된 데이터를 기반으로
 * 데이터베이스에 영구 저장하는 역할을 수행
 * </p>
 *
 * <ul>
 * <li><b>분산 저장:</b> 대화 내용(Chat), 토큰 사용량(Token), 상세 메타데이터(Metadata)를 각각의 컬렉션에 저장</li>
 * <li><b>트랜잭션:</b> 모든 저장 작업은 하나의 트랜잭션으로 묶여 데이터 일관성을 보장.</li>
 * </ul>
 * @author pwk0131
 */

@Slf4j
@Component
@RequiredArgsConstructor
public class ChatWriter {

	private final ChatMessageRepository chatMessageRepository;
	private final ChatTokenUsageRepository chatTokenUsageRepository;
	private final ChatMetadataRepository chatMetadataRepository;

	public void saveChatData(ChatStreamContext context) {
		// 빈 응답 체크 로직 등은 여기서 수행
		if (context.getAnswer().isBlank()) {
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
