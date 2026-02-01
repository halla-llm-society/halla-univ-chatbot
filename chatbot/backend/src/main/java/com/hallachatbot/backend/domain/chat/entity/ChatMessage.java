package com.hallachatbot.backend.domain.chat.entity;

import java.time.LocalDateTime;

import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;
import org.springframework.data.mongodb.core.mapping.FieldType;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

/**
 * 챗봇 대화 내용 저장 엔티티
 *
 * <p>
 * 컬렉션 : {@code chat}<br>
 * 사용자 질문, AI 답변, RAG 결정 사유 등을 저장함
 * </p>
 * @author pwk0131
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "chat${app.mongodb-suffix}")
public class ChatMessage {

	@Id
	private String id;

	/**
	 * 생성 날짜
	 */
	@CreatedDate
	@Field("date")
	private LocalDateTime createdDate;

	/**
	 * 사용자 질문
	 */
	private String question;

	/**
	 * AI 답변
	 */
	private String answer;

	/**
	 * RAG 게이트 결정 사유 (gate_reason)
	 */
	private String decision;

	/**
	 * 사용자 세션 ID (쿠키의 chatId)
	 */
	@Field(name = "chatId", targetType = FieldType.OBJECT_ID)
	private String chatId;

	@Builder
	public ChatMessage(String question, String answer, String decision, String chatId) {
		this.question = question;
		this.answer = answer;
		this.decision = decision;
		this.chatId = chatId;
	}
}
