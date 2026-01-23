package com.hallachatbot.backend.domain.chat.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import lombok.ToString;

@Getter
@Setter
@ToString
@NoArgsConstructor
public class ChatRequest {

	@NotBlank(message = "User input cannot be empty")
	@JsonProperty("user_input") // JSON의 user_input을 자바의 userInput으로 매핑
	private String userInput;

	@JsonProperty("language")
	private String language; // KOR, ENG, ...

	@JsonProperty("chatId")
	private String chatId;
}
