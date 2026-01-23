package com.hallachatbot.backend.domain.chat.entity;

import java.time.LocalDateTime;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@Builder
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "token")
public class Token {

	@Id
	private String id;

	@Indexed
	@Field("chatId") // 실제로는 Chat 메시지의 ID를 참조 (파이썬 코드 기준)
	private String relatedChatId;

	private String preset;

	private String totalTokens;

	private String totalCostUsd;

	@CreatedDate
	private LocalDateTime date;
}
