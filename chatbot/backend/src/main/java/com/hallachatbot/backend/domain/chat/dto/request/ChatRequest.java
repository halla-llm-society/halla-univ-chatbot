package com.hallachatbot.backend.domain.chat.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

/**
 * <b>챗봇 대화 요청 DTO</b>
 *
 * <p>
 * 클라이언트로부터 전달받는 사용자 질문 및 설정 정보
 * </p>
 *
 * @author pwk0131
 */
public record ChatRequest(
	@NotBlank(message = "질문은 비어있을 수 없습니다.")
	@Size(max = 300, message = "질문은 300자를 넘을 수 없습니다.")
	@JsonProperty("user_input")
	String userInput,

	@NotNull(message = "언어 설정은 필수입니다.")
	Language language
) {
	public enum Language {
		KOR, ENG, VNM, CHN, UZB, MNG, IDN
	}
}
