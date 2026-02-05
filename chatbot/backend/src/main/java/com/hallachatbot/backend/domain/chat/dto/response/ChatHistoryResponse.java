package com.hallachatbot.backend.domain.chat.dto.response;

/**
 * <b>채팅 히스토리 응답 DTO</b>
 *
 * <p>
 * 클라이언트(UI) 렌더링 및 AI 모델의 문맥 주입을 위해 사용되는 과거 대화 객체.
 * OpenAI Chat Completion API의 Message 구조(role, content)를 준수함.
 * </p>
 *
 * @param role    메시지 발화자 역할 (예: "user", "assistant")
 * @param content 메시지 본문 내용
 * @author pwk0131
 */
public record ChatHistoryResponse(
	String role,
	String content
) {
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
