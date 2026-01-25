package com.hallachatbot.backend.survey.service;

import java.time.LocalDateTime;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hallachatbot.backend.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.survey.repository.ChatSurveyRepository;

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
		log.info("설문조사 저장 완료: {}", LocalDateTime.now()
		);
	}
}
