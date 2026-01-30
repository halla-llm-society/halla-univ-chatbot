package com.hallachatbot.backend.domain.survey.service;

import com.hallachatbot.backend.domain.survey.dto.request.ChatSurveyRequest;

/**
 * <b>설문조사 비즈니스 로직 처리 서비스</b>
 *
 * <ul>
 * <li><b>역할:</b> 다양한 유형의 설문(챗봇 만족도, 사용자 조사 등) 데이터 처리 및 저장</li>
 * <li><b>현재 설문:</b> 챗봇 만족도 설문({@code ChatSurvey})</li>
 * </ul>
 */
public interface SurveyService {

	/**
	 * <b>챗봇 만족도 설문 제출 처리</b>
	 * * <ul>
	 * <li><b>동작:</b> 요청 DTO를 엔티티로 변환 후 MongoDB에 영구 저장</li>
	 * <li><b>트랜잭션:</b> 쓰기 작업에 대한 단일 트랜잭션 보장</li>
	 * </ul>
	 *
	 * @param request 유효성 검증이 완료된 설문 요청 데이터
	 */
	void submitChatSurvey(ChatSurveyRequest request);
}
