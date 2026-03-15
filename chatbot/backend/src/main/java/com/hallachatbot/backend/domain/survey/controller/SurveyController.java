package com.hallachatbot.backend.domain.survey.controller;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hallachatbot.backend.domain.survey.dto.request.ChatSurveyRequest;
import com.hallachatbot.backend.domain.survey.service.SurveyService;
import com.hallachatbot.backend.global.response.Response;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

/**
 * <b>설문조사 API 컨트롤러</b>
 *
 * <p>
 *     클라이언트의 설문 제출 요청을 수신하고 서비스 계층으로 위임
 * </p>
 */
@Tag(name = "Survey", description = "설문조사 API")
@RestController
@RequestMapping("/api/survey")
@RequiredArgsConstructor
public class SurveyController {

	private final SurveyService surveyServiceImpl;

	/**
	 * <b>챗봇 만족도 설문 제출</b>
	 * <p>
	 *     챗봇 이용 후 작성한 만족도, 속도, 품질 등에 대한 설문을 접수
	 * </p>
	 *
	 * @param request 설문 내용이 담긴 요청 바디 {@link ChatSurveyRequest}
	 */
	@Operation(summary = "챗봇 만족도 설문 제출", description = "사용자의 학적 정보와 챗봇 이용 경험(평점, 속도, 품질)을 저장")
	@ApiResponses(value = {
		// todo: Swagger Response 주석 모으기
		@ApiResponse(responseCode = "200", description = "설문 제출 성공"),
		@ApiResponse(responseCode = "400", description = "INVALID_INPUT_VALUE | etc.."),
		@ApiResponse(responseCode = "500", description = "INTERNAL_SERVER_ERROR | DATABASE_ERROR")
	})
	@PostMapping("/chat")
	public Response<Void> submitChatSurvey(@RequestBody @Valid ChatSurveyRequest request) {
		surveyServiceImpl.submitChatSurvey(request);
		return Response.success();
	}
}
