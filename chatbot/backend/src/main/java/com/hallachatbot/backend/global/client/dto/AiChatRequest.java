package com.hallachatbot.backend.global.client.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.hallachatbot.backend.domain.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.domain.chat.dto.response.ChatHistoryResponse;

/**
 * AI 서비스 요청 DTO
 */
public record AiChatRequest(
	@JsonProperty("user_input")
	String userInput,

	@JsonProperty("message_history")
	List<ChatHistoryResponse> messageHistory,

	ChatRequest.Language language
) {
}
