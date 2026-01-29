package com.hallachatbot.backend.chat.dto.request;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 챗봇 대화 요청 DTO
 *
 * <p>
 * 클라이언트로부터 전달받는 사용자 질문 및 설정 정보
 * </p>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor
public class ChatRequest {

	/**
	 * 사용자 입력 질문
	 */
	@NotBlank(message = "질문은 비어있을 수 없습니다.")
	@Size(max = 300, message = "질문은 300자를 넘을 수 없습니다.")
	@JsonProperty("user_input")
	private String userInput;

	/**
	 * 답변 언어 설정
	 */
	@NotNull(message = "언어 설정은 필수입니다.")
	private Language language;

	/**
	 * 클라이언트가 보낸 chatId, 보통 쿠키로 처리하므로 바디에서는 잘 안쓰일 수 있음
	 */
	private String chatId;

	public enum Language {
		KOR, ENG, VNM, CHN, UZB, MNG, IDN
	}
}
