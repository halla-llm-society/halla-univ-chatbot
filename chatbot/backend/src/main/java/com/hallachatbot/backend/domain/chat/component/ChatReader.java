package com.hallachatbot.backend.domain.chat.component;

import java.util.List;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;

import lombok.RequiredArgsConstructor;

@Component
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ChatReader {

	private final ChatMessageRepository chatMessageRepository;
	private final ChatMapper chatMapper;

	public List<ChatHistoryResponse> getChatHistory(String chatId) {
		// 1. DB 조회 (최신순 6개)
		List<ChatMessage> rawHistory = chatMessageRepository.findTop6ByChatIdOrderByCreatedDateDesc(chatId);

		// 2. 변환 위임
		return chatMapper.toHistoryResponse(rawHistory);
	}
}
