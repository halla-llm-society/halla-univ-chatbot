package com.hallachatbot.backend.survey.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.BDDMockito.willDoNothing;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultHandlers.print;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.hallachatbot.backend.domain.survey.controller.SurveyController;
import com.hallachatbot.backend.domain.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.domain.survey.service.SurveyService;

@WebMvcTest(SurveyController.class)
class SurveyControllerTest {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private ObjectMapper objectMapper;

	@MockitoBean
	private SurveyService surveyService;

	@Test
	@DisplayName("설문 제출 성공 - 유효한 데이터가 들어오면 200 OK를 반환한다")
	void submitChatSurvey_Success() throws Exception {
		// given
		ChatSurveyRequest request = new ChatSurveyRequest(
			"1학년",
			5,
			"high",
			"high",
			"만족합니다."
		);

		willDoNothing().given(surveyService).submitChatSurvey(any(ChatSurveyRequest.class));

		// when & then
		mockMvc.perform(post("/api/survey/chat")
				.contentType(MediaType.APPLICATION_JSON)
				.content(objectMapper.writeValueAsString(request)))
			.andDo(print())
			.andExpect(status().isOk())
			.andExpect(jsonPath("$.isSuccess").value(true));
		// Response 객체 구조에 따라 jsonPath는 조정 필요
	}

	@Test
	@DisplayName("설문 제출 실패 - 필수값이 누락되면 400 Bad Request를 반환한다")
	void submitChatSurvey_Fail_NullField() throws Exception {
		// given
		ChatSurveyRequest invalidRequest = new ChatSurveyRequest(
			null,   // userCategory (Null 불가)
			5,
			"high",
			"high",
			"코멘트"
		);

		// when & then
		mockMvc.perform(post("/api/survey/chat")
				.contentType(MediaType.APPLICATION_JSON)
				.content(objectMapper.writeValueAsString(invalidRequest)))
			.andDo(print())
			.andExpect(status().isBadRequest());
	}

	@Test
	@DisplayName("설문 제출 실패 - 평점 범위를 벗어나면 400 Bad Request를 반환한다")
	void submitChatSurvey_Fail_InvalidRating() throws Exception {
		// given
		ChatSurveyRequest invalidRequest = new ChatSurveyRequest(
			"1학년",
			10,     // rating (Max 5 위반)
			"high",
			"high",
			"코멘트"
		);

		// when & then
		mockMvc.perform(post("/api/survey/chat")
				.contentType(MediaType.APPLICATION_JSON)
				.content(objectMapper.writeValueAsString(invalidRequest)))
			.andDo(print())
			.andExpect(status().isBadRequest());
	}
}
