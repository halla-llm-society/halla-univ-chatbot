package com.hallachatbot.backend.domain.survey.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.domain.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.domain.survey.repository.ChatSurveyRepository;
import com.hallachatbot.backend.global.errorcode.GlobalErrorCode;
import com.hallachatbot.backend.global.exception.GlobalException;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Service
@RequiredArgsConstructor
public class SurveyServiceImpl implements SurveyService {

	private final ChatSurveyRepository chatSurveyRepository;

	@Override
	@Transactional
	public void submitChatSurvey(ChatSurveyRequest request) {
		try {
			chatSurveyRepository.save(request.toEntity());
			log.info("[Survey] 챗봇 만족도 설문 저장 성공");

		} catch (Exception e) {
			log.error("[Survey] 챗봇 만족도 설문 저장 실패: {}", e.getMessage());
			throw new GlobalException(GlobalErrorCode.DATABASE_ERROR);
		}
	}
}
