package com.hallachatbot.backend.domain.chat.entity;

import java.time.LocalDateTime;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@Document(collection = "chat")
public class Chat {
	@Id
	private String id;

	private String chatId;

	private String question;

	private String answer;

	private String decision; // RAG gate reason 등

	@CreatedDate
	private LocalDateTime date;
}
