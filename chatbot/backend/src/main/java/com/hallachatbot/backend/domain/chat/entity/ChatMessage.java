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
 * <b>챗봇 대화 메시지 엔티티</b>
 *
 * <p>
 * 사용자와 AI 간의 질의응답 내용을 저장하는 메인 문서.
 * 질문(question), 답변(answer), 그리고 답변 생성에 대한 근거(decision)를 포함.
 * </p>
 *
 * <ul>
 * <li>Collection Name: {@code chat}</li>
 * </ul>
 *
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
	 * 사용자 세션 식별자 (Cookie의 chatId)
	 * <p>
	 * 특정 사용자의 대화 흐름을 그룹화하기 위한 외래 키 역할
	 * </p>
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
