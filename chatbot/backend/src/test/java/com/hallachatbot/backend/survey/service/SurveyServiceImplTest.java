package com.hallachatbot.backend.survey.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import com.hallachatbot.backend.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.survey.entity.ChatSurvey;
import com.hallachatbot.backend.survey.repository.ChatSurveyRepository;

@ExtendWith(MockitoExtension.class)
class SurveyServiceImplTest {

	@InjectMocks
	private SurveyServiceImpl surveyService;

	@Mock
	private ChatSurveyRepository chatSurveyRepository;

	@Test
	@DisplayName("설문 제출 시 리포지토리의 save 메서드가 올바르게 호출되어야 한다")
	void submitChatSurvey_Success() {
		// given
		ChatSurveyRequest request = new ChatSurveyRequest(
			"1학년",
			5,
			"high",
			"high",
			"좋아요"
		);

		// when
		surveyService.submitChatSurvey(request);

		// then
		// 1. save 호출 횟수 검증
		verify(chatSurveyRepository, times(1)).save(any(ChatSurvey.class));

		// 2. 전달된 데이터 정합성 검증
		ArgumentCaptor<ChatSurvey> captor = ArgumentCaptor.forClass(ChatSurvey.class);
		verify(chatSurveyRepository).save(captor.capture());

		ChatSurvey savedEntity = captor.getValue();

		assertThat(savedEntity.getUserCategory()).isEqualTo(request.userCategory());
		assertThat(savedEntity.getRating()).isEqualTo(request.rating());
		assertThat(savedEntity.getComment()).isEqualTo(request.comment());
	}
}
