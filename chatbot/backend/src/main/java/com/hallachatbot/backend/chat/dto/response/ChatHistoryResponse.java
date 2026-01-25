package com.hallachatbot.backend.chat.dto.response;

import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 채팅 히스토리 응답 DTO
 *
 * <p>
 * 클라이언트(UI)에 과거 대화 내역을 전달하기 위한 객체<br>
 * OpenAI API 포맷과 유사하게 role(역할)과 content(내용)으로 구성됨
 * </p>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor
public class ChatHistoryResponse {

	/**
	 * 역할 (user 또는 assistant)
	 */
	private String role;

	/**
	 * 대화 내용
	 */
	private String content;

	@Builder
	public ChatHistoryResponse(String role, String content) {
		this.role = role;
		this.content = content;
	}

	/**
	 * 사용자(User) 메시지 생성 편의 메서드
	 */
	public static ChatHistoryResponse user(String content) {
		return new ChatHistoryResponse("user", content);
	}

	/**
	 * AI(Assistant) 메시지 생성 편의 메서드
	 */
	public static ChatHistoryResponse assistant(String content) {
		return new ChatHistoryResponse("assistant", content);
	}
}
