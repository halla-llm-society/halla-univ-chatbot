package com.hallachatbot.backend.domain.chat.component;

import java.util.List;

import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;
import com.hallachatbot.backend.domain.chat.entity.ChatMessage;
import com.hallachatbot.backend.domain.chat.repository.ChatMessageRepository;

import lombok.RequiredArgsConstructor;

/**
 * <b>대화 내역 조회 컴포넌트 (Reader)</b>
 *
 * <p>
 * 데이터베이스로부터 과거 대화 내역을 읽어오는 책임을 가지는 클래스
 * {@link Transactional} (readOnly=true) 환경에서 동작하며, 조회된 데이터를
 * {@link ChatMapper}를 통해 필요한 포맷으로 변환하여 반환
 * </p>
 *
 * @author pwk0131
 */

@Component
@RequiredArgsConstructor
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
