package com.hallachatbot.backend.domain.chat.repository;

import java.util.List;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.chat.entity.ChatMessage;

/**
 * <b>ChatMessage 리포지토리</b>
 * <p>
 * MongoDB 'chat' 컬렉션에 대한 CRUD 및 쿼리 메서드 제공
 * </p>
 *
 * @author pwk0131
 */
@Repository
public interface ChatMessageRepository extends MongoRepository<ChatMessage, String> {

	/**
	 * 특정 채팅방(세션)의 최근 대화 내역 조회
	 *
	 * <p>
	 * 최신순으로 6개를 가져옴
	 * </p>
	 *
	 * @param chatId 사용자 세션 ID
	 * @return 최근 대화 목록 (최신순)
	 */
	List<ChatMessage> findTop6ByChatIdOrderByCreatedDateDesc(String chatId);
}
