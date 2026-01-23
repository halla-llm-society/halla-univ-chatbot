package com.hallachatbot.backend.domain.chat.dto;

import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class AiRequest {

	@JsonProperty("user_input")
	private String userInput;

	@JsonProperty("message_history")
	private List<Map<String, String>> messageHistory;

	@JsonProperty("language")
	private String language;
}
