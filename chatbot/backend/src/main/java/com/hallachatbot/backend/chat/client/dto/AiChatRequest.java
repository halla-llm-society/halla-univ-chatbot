package com.hallachatbot.backend.chat.client.dto;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.hallachatbot.backend.chat.dto.request.ChatRequest;
import com.hallachatbot.backend.chat.dto.response.ChatHistoryResponse;

import lombok.Builder;
import lombok.Getter;

/**
 * AI 서비스 요청 DTO
 */
@Getter
@Builder
public class AiChatRequest {

	@JsonProperty("user_input")
	private String userInput;

	@JsonProperty("message_history")
	private List<ChatHistoryResponse> messageHistory;

	private ChatRequest.Language language;
}
