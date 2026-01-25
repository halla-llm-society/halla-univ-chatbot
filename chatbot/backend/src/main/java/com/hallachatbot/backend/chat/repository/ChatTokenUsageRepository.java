package com.hallachatbot.backend.chat.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.chat.entity.ChatTokenUsage;

/**
 * ChatTokenUsage 리포지토리
 *
 * <p>
 * MongoDB 'token' 컬렉션 접근용<br>
 * 대화별 토큰 소모량 저장에 사용됨
 * </p>
 *
 * @author pwk0131
 */
@Repository
public interface ChatTokenUsageRepository extends MongoRepository<ChatTokenUsage, String> {
}
