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
 * <b>토큰 사용량 기록 엔티티</b>
 *
 * <p>
 * 대화 생성 시 소모된 토큰(Token) 수와 사용된 모델(Preset) 정보를 저장.
 * 비용 산정 및 사용량 통계 분석에 활용.
 * </p>
 *
 * <ul>
 * <li>Collection Name: {@code token}</li>
 * <li>Relation: {@link ChatMessage}와 1:1 대응</li>
 * </ul>
 *
 * @author pwk0131
 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Document(collection = "token${app.mongodb-suffix}")
public class ChatTokenUsage {

	@Id
	private String id;

	/**
	 * 생성 날짜
	 */
	@CreatedDate
	@Field("date")
	private LocalDateTime createdDate;

	/**
	 * 연관된 대화 메시지 ID
	 * <p>
	 * {@link ChatMessage}의 PK(_id)를 참조.<br>
	 * <b>주의:</b> 레거시 데이터와의 호환성을 위해 DB 필드명은 'chatId'로 저장됨.
	 * </p>
	 */
	@Field(name = "chatId", targetType = FieldType.OBJECT_ID)
	private String messageId;

	/**
	 * 사용된 LLM 모델 프리셋 (예: gpt-4o, claude-3)
	 */
	private String preset;

	/**
	 * 총 소모 토큰 수 (입력 + 출력)
	 */
	private Integer totalTokens;

	@Builder
	public ChatTokenUsage(String messageId, String preset, Integer totalTokens) {
		this.messageId = messageId;
		this.preset = preset;
		this.totalTokens = totalTokens;
	}
}
