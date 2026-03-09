package com.hallachatbot.backend.domain.survey.dto.request;

import com.hallachatbot.backend.domain.survey.entity.ChatSurvey;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

/**
 * <b>챗봇 사용 만족도 설문 요청 DTO</b>
 */
@Schema(description = "챗봇 만족도 설문 제출 요청 데이터")
public record ChatSurveyRequest(

	@Schema(description = "사용자 카테고리 (학적/신분)", allowableValues = {"1학년", "2학년", "3학년", "4학년", "대학원생", "교직원", "외부인"})
	@NotNull(message = "사용자 카테고리는 필수입니다.")
	@Pattern(
		regexp = "^(1학년|2학년|3학년|4학년|대학원생|교직원|외부인)$",
		message = "올바르지 않은 사용자 카테고리입니다."
	)
	String userCategory,

	@Schema(description = "만족도 평점", minimum = "1", maximum = "5")
	@NotNull(message = "평점 입력은 필수입니다.")
	@Min(value = 1, message = "평점은 최소 1점이어야 합니다.")
	@Max(value = 5, message = "평점은 최대 5점이어야 합니다.")
	int rating,

	@Schema(description = "챗봇 응답 속도 체감", allowableValues = {"high", "mid", "low"})
	@NotNull(message = "응답 속도 평가는 필수입니다.")
	@Pattern(regexp = "^(high|mid|low)$", message = "응답 속도는 'high', 'mid', 'low' 중 하나여야 합니다.")
	String responseSpeed,

	@Schema(description = "챗봇 답변 품질 체감", allowableValues = {"high", "mid", "low"})
	@NotNull(message = "응답 품질 평가는 필수입니다.")
	@Pattern(regexp = "^(high|mid|low)$", message = "응답 품질은 'high', 'mid', 'low' 중 하나여야 합니다.")
	String responseQuality,

	@Schema(description = "기타 건의사항 및 코멘트", maxLength = 100)
	@Size(max = 100, message = "코멘트는 100자를 초과할 수 없습니다.")
	String comment
) {
	public ChatSurvey toEntity() {
		return ChatSurvey.of(
			userCategory(),
			rating(),
			responseSpeed(),
			responseQuality(),
			comment()
		);
	}
}
