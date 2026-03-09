package com.hallachatbot.backend.domain.chat.client.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;

/**
 * <b>AI 서비스 요청 DTO</b>
 *
 * <p>
 * AI 모델 서버(LLM Service)로 전송되는 JSON 요청 본문 구조.
 * 사용자 질문, 대화 문맥(History), 언어 설정 등을 포함.
 * </p>
 *
 * @param userInput      사용자 입력 질문
 * @param messageHistory 이전 대화 내역 리스트 (Context 유지용)
 * @param language       답변 생성 시 사용할 언어 설정
 * @author pwk0131
 */
public record AiChatRequest(
	@JsonProperty("user_input")
	String userInput,

	@JsonProperty("message_history")
	List<ChatHistoryResponse> messageHistory,

	ChatRequest.Language language
) {
}
