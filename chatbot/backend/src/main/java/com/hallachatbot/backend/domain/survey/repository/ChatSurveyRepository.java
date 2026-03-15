package com.hallachatbot.backend.domain.survey.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import com.hallachatbot.backend.domain.survey.entity.ChatSurvey;

/**
 * <b>챗봇 설문 데이터 접근 리포지토리</b>
 *
 * <ul>
 * <li><b>대상 엔티티:</b> {@link ChatSurvey}</li>
 * <li><b>Key 타입:</b> MongoDB ObjectId</li>
 * </ul>
 */
@Repository
public interface ChatSurveyRepository extends MongoRepository<ChatSurvey, String> {
}
