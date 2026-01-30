package com.hallachatbot.backend.domain.chat.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.chat.entity.ChatMetadata;

/**
 * ChatMetadata 리포지토리
 *
 * <p>
 * MongoDB 'metadata' 컬렉션 접근용<br>
 * AI 모델의 상세 메타데이터 저장에 사용됨
 * </p>
 *
 * @author pwk0131
 */
@Repository
public interface ChatMetadataRepository extends MongoRepository<ChatMetadata, String> {
}
