package com.hallachatbot.backend.domain.survey.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.domain.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.domain.survey.repository.ChatSurveyRepository;

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
		chatSurveyRepository.save(request.toEntity());
		log.info("[Survey] 챗봇 만족도 설문 저장 성공");
	}
}
